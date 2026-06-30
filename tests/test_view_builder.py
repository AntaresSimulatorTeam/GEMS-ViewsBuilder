# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import shutil
import textwrap
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest
from pytest import approx

from gems_views_builder.loader import Loader
from gems_views_builder.view import accumulate_on_disk
from gems_views_builder.views_builder import ViewBuilder


def _build_view_builder(dataset_dir: Path) -> ViewBuilder:
    return ViewBuilder(Loader(dataset_dir).load())


@pytest.fixture()
def view_result(test_files_root: Path, tmp_path: Path) -> pl.DataFrame:
    """
    Run ViewBuilder.build() on a fresh copy of test_3 and return the result DataFrame.
    A copy is used so ViewBuilder's intermediate writes do not pollute the shared
    session-scoped test_files_root directory.
    """
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    shutil.copytree(src, dst)
    metric_views = _build_view_builder(dst).build()
    accumulate_on_disk(metric_views, results_dir)
    result_files = list(results_dir.glob("view*.parquet"))
    assert result_files, "No result parquet file written"
    return pl.read_parquet(result_files[0])


def _metric_at(df: pl.DataFrame, metric_id: str, location: str) -> pl.DataFrame:
    return df.filter((pl.col("metric_id") == metric_id) & (pl.col("metric_location") == location)).sort("view_date")


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def test_prod_busa_row_count(view_result: pl.DataFrame) -> None:
    rows = _metric_at(view_result, "PROD", "busA")
    # one row per timestep t in {1, ..., 24}
    assert len(rows) == 24


def test_prod_busa_values(view_result: pl.DataFrame) -> None:
    # generator_A1.p(t) + generator_A2.p(t) = t + t = 2t
    rows = _metric_at(view_result, "PROD", "busA")
    expected = [2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_prod_busb_row_count(view_result: pl.DataFrame) -> None:
    rows = _metric_at(view_result, "PROD", "busB")
    assert len(rows) == 24


def test_prod_busb_values(view_result: pl.DataFrame) -> None:
    # generator_B1.p(t) = 100 - 2t
    rows = _metric_at(view_result, "PROD", "busB")
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_busa_value(view_result: pl.DataFrame) -> None:
    # load_AL.active_load = 100 (not time-dependent).
    rows = _metric_at(view_result, "LOAD", "busA")
    assert len(rows) == 1
    assert rows["metric_value"][0] == 100


def test_load_busb_absent(view_result: pl.DataFrame) -> None:
    # No consumption component connected to busB
    rows = _metric_at(view_result, "LOAD", "busB")
    assert len(rows) == 0


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_busa_values(view_result: pl.DataFrame) -> None:
    # link_link_AB.p0_port.flow(t) = 100 - 2t (outflow from busA)
    rows = _metric_at(view_result, "BALANCE", "busA")
    assert len(rows) == 24
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_balance_busb_values(view_result: pl.DataFrame) -> None:
    # link_link_AB.p1_port.flow(t) = -(100 - 2t) (inflow into busB)
    rows = _metric_at(view_result, "BALANCE", "busB")
    assert len(rows) == 24
    expected = [-(100 - 2 * t) for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_log_messages_emitted_to_stdout(
    test_files_root: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)

    results_dir = tmp_path / "results"
    results_dir.mkdir()
    with caplog.at_level(logging.INFO):
        metric_views = _build_view_builder(dst).build()
        accumulate_on_disk(metric_views, results_dir)

    repo_root = Path(__file__).resolve().parents[1]
    log_directory = repo_root / "logs"
    if not log_directory.exists() or not any(log_directory.glob("gems-views-builder-pipeline-run-*.log")):
        raise FileNotFoundError(f"Log directory {log_directory} not found or does not contain any log files")

    messages = [r.message for r in caplog.records]
    assert any("All inputs loaded" in m for m in messages)
    assert any("All inputs loaded successfully" in m for m in messages), (
        "Missing expected log: All inputs loaded successfully"
    )
    assert any("Results merged into" in m for m in messages), "Missing expected log: Results merged into"


def test_logs_dir_and_file_created(test_files_root: Path, tmp_path: Path) -> None:
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)

    _build_view_builder(dst).build()

    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = repo_root / "logs"
    assert logs_dir.is_dir(), "logs/ directory was not created"
    log_files = list(logs_dir.glob("gems-views-builder-pipeline-run-*.log"))
    assert len(log_files) >= 1, f"Expected at least 1 log file, found {len(log_files)}"
    assert max(f.stat().st_size for f in log_files) > 0, "All log files are empty"


# ---------------------------------------------------------------------------
# Temporal aggregation e2e tests – daily granularity + AVG price metric
# ---------------------------------------------------------------------------

_VIEW_CONFIG_DAILY = textwrap.dedent("""\
    view:
      id: view_area_daily
      scope:
        - location:
          taxonomy-category: balance
        - calendar: calendar_file
      aggregation:
        - time: day
      catalog:
          - id: catalog
      metrics:
          - id: catalog.PROD
          - id: catalog.LOAD
          - id: catalog.BALANCE
          - id: catalog.PRICE
    """)

_CATALOG_WITH_PRICE = textwrap.dedent("""\
    catalog:
      id: test_example_pypsa_daily
      taxonomy: my_taxonomy
      location:
        taxonomy-category: balance
      metrics-definition:
      - id: PROD
        terms:
          - taxonomy-category: production
            output-id: p
            location-ports: p_balance_port
        terms-operator: sum
        time-operator: sum
      - id: LOAD
        terms:
          - taxonomy-category: consumption
            output-id: active_load
            location-ports: p_balance_port
        terms-operator: sum
        time-operator: sum
      - id: BALANCE
        terms:
          - taxonomy-category: link
            output-id: p0_port.flow
            location-ports: p0_port
          - taxonomy-category: link
            output-id: p1_port.flow
            location-ports: p1_port
        terms-operator: sum
        time-operator: sum
      - id: PRICE
        terms:
          - taxonomy-category: balance
            output-id: p_balance
            location-ports: ~
        terms-operator: sum
        time-operator: avg
    """)


def _make_daily_dataset(src: Path, dataset_dir: Path) -> None:
    """Build a dataset directory suitable for daily-aggregation e2e tests.

    Copies the static files from *src* (test_3), overrides view_config and catalog,
    and writes a new simulation table where busA/busB shadow prices are non-null:
      busA.p_balance(t) = t
      busB.p_balance(t) = 2 * t   (t = absolute_time_index, 1..24)
    """
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "catalogs").mkdir()

    for filename in ("system.yml", "taxonomy.yml", "library.yml", "calendar_file.csv"):
        shutil.copy(src / filename, dataset_dir / filename)

    (dataset_dir / "view_config.yml").write_text(_VIEW_CONFIG_DAILY)
    (dataset_dir / "catalogs" / "catalog.yml").write_text(_CATALOG_WITH_PRICE)

    base_parquet = next(src.glob("simulation_table*.parquet"))
    base_df = pl.read_parquet(base_parquet)
    # Replace null shadow-price values for buses with deterministic integers:
    #   busA.p_balance(t) = t,  busB.p_balance(t) = 2t
    updated = base_df.with_columns(
        pl.when(
            (pl.col("component") == "busA")
            & (pl.col("output") == "p_balance")
            & pl.col("absolute_time_index").is_not_null(),
        )
        .then(pl.col("absolute_time_index").cast(pl.Int64))
        .when(
            (pl.col("component") == "busB")
            & (pl.col("output") == "p_balance")
            & pl.col("absolute_time_index").is_not_null(),
        )
        .then((pl.col("absolute_time_index") * 2).cast(pl.Int64))
        .otherwise(pl.col("value"))
        .alias("value"),
    )
    updated.write_parquet(dataset_dir / "simulation_table--daily-test.parquet")


@pytest.fixture()
def daily_view_result(test_files_root: Path, tmp_path: Path) -> pl.DataFrame:
    """Run ViewBuilder with daily granularity on a programmatically built dataset."""
    src = test_files_root / "test_3"
    dataset_dir = tmp_path / "test_daily"
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    _make_daily_dataset(src, dataset_dir)

    metric_views = _build_view_builder(dataset_dir).build()
    accumulate_on_disk(metric_views, results_dir)
    result_files = list(results_dir.glob("view*.parquet"))
    assert result_files, "No result parquet file written"
    return pl.read_parquet(result_files[0])


# Calendar: t=1..23 → 2025-01-01 (hour 01:00..23:00), t=24 → 2025-01-02 (00:00).
_DAY1 = datetime(2025, 1, 1)
_DAY2 = datetime(2025, 1, 2)


# ---------------------------------------------------------------------------
# PROD – SUM operator, daily granularity
# generator_A1.p(t) = t, generator_A2.p(t) = t  →  PROD_busA(t) = 2t
# generator_B1.p(t) = 100 - 2t                  →  PROD_busB(t) = 100 - 2t
# ---------------------------------------------------------------------------


def test_daily_prod_busa_row_count(daily_view_result: pl.DataFrame) -> None:
    rows = _metric_at(daily_view_result, "PROD", "busA")
    assert len(rows) == 2


def test_daily_prod_busa_values(daily_view_result: pl.DataFrame) -> None:
    # Day 1 (t=1..23): sum(2t) = 2*(1+…+23) = 552
    # Day 2 (t=24):    2*24 = 48
    rows = _metric_at(daily_view_result, "PROD", "busA")
    assert rows["view_date"].to_list() == [_DAY1, _DAY2]
    assert rows["metric_value"].to_list() == [552, 48]


def test_daily_prod_busb_row_count(daily_view_result: pl.DataFrame) -> None:
    rows = _metric_at(daily_view_result, "PROD", "busB")
    assert len(rows) == 2


def test_daily_prod_busb_values(daily_view_result: pl.DataFrame) -> None:
    # Day 1 (t=1..23): sum(100-2t) = 23*100 - 2*(1+…+23) = 2300 - 552 = 1748
    # Day 2 (t=24):    100 - 2*24 = 52
    rows = _metric_at(daily_view_result, "PROD", "busB")
    assert rows["view_date"].to_list() == [_DAY1, _DAY2]
    assert rows["metric_value"].to_list() == [1748, 52]


# ---------------------------------------------------------------------------
# LOAD – SUM operator, time-independent constant (unchanged by daily roll-up)
# load_AL.active_load = 100
# ---------------------------------------------------------------------------


def test_daily_load_busa_value(daily_view_result: pl.DataFrame) -> None:
    rows = _metric_at(daily_view_result, "LOAD", "busA")
    assert len(rows) == 1
    assert rows["metric_value"][0] == 100


# ---------------------------------------------------------------------------
# PRICE – AVG operator, daily granularity
# busA.p_balance(t) = t      →  avg over day 1 = mean(1..23) = 12.0
# busB.p_balance(t) = 2*t    →  avg over day 1 = mean(2,4,…,46) = 24.0
# ---------------------------------------------------------------------------


def test_daily_price_busa_row_count(daily_view_result: pl.DataFrame) -> None:
    rows = _metric_at(daily_view_result, "PRICE", "busA")
    assert len(rows) == 2


def test_daily_price_busa_values(daily_view_result: pl.DataFrame) -> None:
    # Day 1 (t=1..23): mean(1,…,23) = 276/23 = 12.0
    # Day 2 (t=24):    24.0
    rows = _metric_at(daily_view_result, "PRICE", "busA")
    assert rows["view_date"].to_list() == [_DAY1, _DAY2]
    assert rows["metric_value"][0] == approx(12.0)
    assert rows["metric_value"][1] == approx(24.0)


def test_daily_price_busb_row_count(daily_view_result: pl.DataFrame) -> None:
    rows = _metric_at(daily_view_result, "PRICE", "busB")
    assert len(rows) == 2


def test_daily_price_busb_values(daily_view_result: pl.DataFrame) -> None:
    # Day 1 (t=1..23): mean(2,4,…,46) = 552/23 = 24.0
    # Day 2 (t=24):    48.0
    rows = _metric_at(daily_view_result, "PRICE", "busB")
    assert rows["view_date"].to_list() == [_DAY1, _DAY2]
    assert rows["metric_value"][0] == approx(24.0)
    assert rows["metric_value"][1] == approx(48.0)
