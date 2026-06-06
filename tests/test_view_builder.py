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
from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

import gems_views_builder.common as common_mod
from gems_views_builder.catalog import PropertySchema, get_catalog_metric, load_catalog
from gems_views_builder.library import ModelLibrary
from gems_views_builder.metrics_builder import _format_metric_location
from gems_views_builder.system import InputSystem
from gems_views_builder.views import ViewBuilder


@pytest.fixture()
def view_run(test_files_root: Path, tmp_path: Path) -> tuple[pl.DataFrame, Path]:
    """
    Run ViewBuilder.build() on a fresh copy of test_3 and return the result DataFrame.
    A copy is used so ViewBuilder's intermediate writes do not pollute the shared
    session-scoped test_files_root directory.
    """
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)
    ViewBuilder(dst).build()
    result_file = next((dst / "results").glob("*.parquet"))
    return pl.read_parquet(result_file), dst


def _component_matches_filters(metric_filter: PropertySchema | None, component: object) -> bool:
    if metric_filter is None:
        return True
    props = getattr(component, "properties", None) or {}
    if not isinstance(props, dict):
        return False
    return bool(props.get(metric_filter.key) == metric_filter.value)


def _metric_at(df: pl.DataFrame, metric_id: str, location: str) -> pl.DataFrame:
    encoded = _format_metric_location((location,))
    return df.filter((pl.col("metric_id") == metric_id) & (pl.col("metric_location") == encoded)).sort("view_date")


# ---------------------------------------------------------------------------
# PROD
# ---------------------------------------------------------------------------


def test_prod_busa_row_count(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    rows = _metric_at(view_result, "PROD", "busA")

    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    included = [
        cid
        for cid in ("generator_A1", "generator_A2")
        if _component_matches_filters(metric.filter, system.get_component(cid))
    ]
    if not included:
        assert len(rows) == 0
        return
    # one row per timestep t in {1, ..., 24}
    assert len(rows) == 24


def test_prod_busa_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # generator_A1.p(t) + generator_A2.p(t) = t + t = 2t
    rows = _metric_at(view_result, "PROD", "busA")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    included = [
        cid
        for cid in ("generator_A1", "generator_A2")
        if _component_matches_filters(metric.filter, system.get_component(cid))
    ]
    if not included:
        assert rows.is_empty()
        return
    multiplier = len(included)
    expected = [multiplier * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_prod_busb_row_count(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    rows = _metric_at(view_result, "PROD", "busB")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("generator_B1")):
        assert len(rows) == 0
        return
    assert len(rows) == 24


def test_prod_busb_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # generator_B1.p(t) = 100 - 2t
    rows = _metric_at(view_result, "PROD", "busB")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "PROD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("generator_B1")):
        assert rows.is_empty()
        return
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------


def test_load_busa_value(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    rows = _metric_at(view_result, "LOAD", "busA")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "LOAD")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("load_AL")):
        assert len(rows) == 0
        return
    assert len(rows) == 1
    assert rows["metric_value"][0] == 100


def test_load_busb_absent(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, _ = view_run
    # No consumption component connected to busB
    rows = _metric_at(view_result, "LOAD", "busB")
    assert len(rows) == 0


# ---------------------------------------------------------------------------
# BALANCE
# ---------------------------------------------------------------------------


def test_balance_busa_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # link_link_AB.p0_port.flow(t) = 100 - 2t (outflow from busA)
    rows = _metric_at(view_result, "BALANCE", "busA")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "BALANCE")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("link_link_AB")):
        assert len(rows) == 0
        return
    assert len(rows) == 24
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_balance_busb_values(view_run: tuple[pl.DataFrame, Path]) -> None:
    view_result, dst = view_run
    # link_link_AB.p1_port.flow(t) = -(100 - 2t) (inflow into busB)
    rows = _metric_at(view_result, "BALANCE", "busB")
    catalog = load_catalog(dst / "catalogs" / "catalog.yml")
    metric = get_catalog_metric(catalog, "BALANCE")
    library = ModelLibrary.load(dst / "library.yml")
    system = InputSystem.load(dst / "system.yml", library)
    if not _component_matches_filters(metric.filter, system.get_component("link_link_AB")):
        assert len(rows) == 0
        return
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

    # Our logger has propagate=False so caplog's root handler never sees the records.
    # Attach caplog's handler directly so records are captured.
    common_mod.logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="gems_views_builder"):
            ViewBuilder(dst).build()
    finally:
        common_mod.logger.removeHandler(caplog.handler)

    messages = [r.message for r in caplog.records]
    assert any("Starting pipeline" in m for m in messages)
    assert any("All inputs loaded" in m for m in messages)
    assert any("Pipeline complete" in m for m in messages)


def test_logs_dir_and_file_created(test_files_root: Path, tmp_path: Path) -> None:
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)

    ViewBuilder(dst).build()

    logs_dir = dst / "logs"
    assert logs_dir.is_dir(), "logs/ directory was not created"
    log_files = list(logs_dir.glob("pipeline-*.log"))
    assert len(log_files) == 1, f"Expected 1 log file, found {len(log_files)}"
    assert log_files[0].stat().st_size > 0, "Log file is empty"


def test_no_log_file_leaked_on_exception(test_files_root: Path, tmp_path: Path) -> None:
    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)

    with patch.object(ViewBuilder, "create_intermediate_dir", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            ViewBuilder(dst).build()

    # Handler must be closed — no open file handle left dangling
    assert common_mod._file_handler is None, "File handler was not closed after exception"
    # The log file itself is expected to exist (messages before the exception were written)
    # but must be closed and readable — not locked or partially flushed
    log_files = list((dst / "logs").glob("pipeline-*.log"))
    assert len(log_files) == 1
    assert log_files[0].read_text(encoding="utf-8")  # non-empty and readable


# ---------------------------------------------------------------------------
# Spatial aggregation (test_location_aggregation fixture)
# ---------------------------------------------------------------------------


def _loc_run(test_files_root: Path, tmp_path: Path, config_variant: str | None = None) -> pl.DataFrame:
    """Build the test_location_aggregation fixture and return the result DataFrame.

    config_variant: name of an alternative view_config file (without .yml) to
    copy over view_config.yml before running. None means use the default.
    """
    src = test_files_root / "test_location_aggregation"
    dst = tmp_path / f"loc_agg_{config_variant or 'default'}"
    shutil.copytree(src, dst)
    if config_variant is not None:
        shutil.copy(dst / f"{config_variant}.yml", dst / "view_config.yml")
    ViewBuilder(dst).build()
    return pl.read_parquet(next((dst / "results").glob("*.parquet")))


def test_country_collapse_fr(test_files_root: Path, tmp_path: Path) -> None:
    """PRODUCTION at '{FR}' = gen_FR1 + gen_FR2 summed per hour."""
    df = _loc_run(test_files_root, tmp_path)
    rows = _metric_at(df, "PRODUCTION", "FR")
    assert rows["metric_value"].to_list() == [20, 40, 60, 80]
    assert df.filter(pl.col("metric_location").is_in(["{area_FR1}", "{area_FR2}"])).is_empty()


def test_country_collapse_de(test_files_root: Path, tmp_path: Path) -> None:
    """PRODUCTION at '{DE}' = gen_DE alone."""
    df = _loc_run(test_files_root, tmp_path)
    rows = _metric_at(df, "PRODUCTION", "DE")
    assert rows["metric_value"].to_list() == [10, 20, 30, 40]


def test_unknown_sentinel_keep(test_files_root: Path, tmp_path: Path) -> None:
    """gen_orph has no country property; on_missing=keep routes it to '{<unknown>}'."""
    df = _loc_run(test_files_root, tmp_path)
    rows = _metric_at(df, "PRODUCTION", "<unknown>")
    assert rows["metric_value"].to_list() == [10, 20, 30, 40]
    assert df.filter(pl.col("metric_location") == "{area_orph}").is_empty()


def test_unknown_drop(test_files_root: Path, tmp_path: Path) -> None:
    """on_missing=drop excludes gen_orph; FR and DE totals unchanged."""
    df = _loc_run(test_files_root, tmp_path, config_variant="view_config_drop")
    assert df.filter(pl.col("metric_location") == "{<unknown>}").is_empty()
    assert df.filter(pl.col("metric_location") == "{area_orph}").is_empty()
    assert _metric_at(df, "PRODUCTION", "FR")["metric_value"].to_list() == [20, 40, 60, 80]
    assert _metric_at(df, "PRODUCTION", "DE")["metric_value"].to_list() == [10, 20, 30, 40]


def test_balance_location_collapse(test_files_root: Path, tmp_path: Path) -> None:
    """BALANCE link flows appear at country-level labels, not raw area IDs."""
    df = _loc_run(test_files_root, tmp_path)
    assert _metric_at(df, "BALANCE", "FR")["metric_value"].to_list() == [5, 5, 5, 5]
    assert _metric_at(df, "BALANCE", "DE")["metric_value"].to_list() == [-5, -5, -5, -5]
    assert df.filter(
        (pl.col("metric_id") == "BALANCE") & pl.col("metric_location").is_in(["{area_FR1}", "{area_DE}"])
    ).is_empty()


def test_no_location_key_regression(test_files_root: Path, tmp_path: Path) -> None:
    """Without a location key, PRODUCTION rows carry raw area IDs — feature is opt-in."""
    df = _loc_run(test_files_root, tmp_path, config_variant="view_config_no_location")
    for area in ("area_FR1", "area_FR2", "area_DE", "area_orph"):
        rows = _metric_at(df, "PRODUCTION", area)
        assert rows["metric_value"].to_list() == [10, 20, 30, 40], f"unexpected values for {area}"
    assert df.filter(pl.col("metric_location").is_in(["{FR}", "{DE}", "{<unknown>}"])).is_empty()
