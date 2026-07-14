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

import polars as pl
import pytest

from gems_views_builder.__main__ import run
from gems_views_builder.input.component import format_metric_location
from gems_views_builder.view import CsvViewSinker, ParquetViewSinker


def copy_study_in_tmp(src: Path, tmp_path: Path) -> Path:
    dst = tmp_path / src.name
    shutil.copytree(src, dst)
    return dst


@pytest.fixture()
def test_3_study(test_files_root: Path, tmp_path: Path) -> Path:
    return copy_study_in_tmp(test_files_root / "test_3", tmp_path)


def _location_aggregation_src(test_files_root: Path) -> Path:
    candidate = test_files_root / "test_location_aggregation"
    if candidate.is_dir():
        return candidate
    alt = test_files_root.parent / "tests" / "test_inputs" / "test_location_aggregation"
    if alt.is_dir():
        return alt
    raise FileNotFoundError(f"test_location_aggregation fixture not found under {test_files_root}")


def metric_at(df: pl.DataFrame, metric_id: str, location: str) -> pl.DataFrame:
    encoded = format_metric_location((location,))
    return df.filter((pl.col("metric_id") == metric_id) & (pl.col("metric_location") == encoded)).sort("view_date")


@pytest.fixture()
def view_result(test_3_study: Path) -> pl.DataFrame:
    sinker = ParquetViewSinker(test_3_study)
    run(test_3_study, sinker)
    result_files = list(test_3_study.glob("view*.parquet"))
    assert result_files, "No result parquet file written"
    return pl.read_parquet(result_files[0])


def test_build_view__prod_at_bus_a__returns_24_hourly_rows(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "PROD", "busA")
    assert len(rows) == 24


def test_build_view__prod_at_bus_a__sums_generators_as_2t(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "PROD", "busA")
    expected = [2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_build_view__prod_at_bus_b__returns_24_hourly_rows(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "PROD", "busB")
    assert len(rows) == 24


def test_build_view__prod_at_bus_b__matches_generator_b1(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "PROD", "busB")
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_build_view__load_at_bus_a__returns_constant_100(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "LOAD", "busA")
    assert len(rows) == 1
    assert rows["metric_value"][0] == 100


def test_build_view__load_at_bus_b__has_no_rows(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "LOAD", "busB")
    assert len(rows) == 0


def test_build_view__balance_at_bus_a__matches_link_outflow(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "BALANCE", "busA")
    assert len(rows) == 24
    expected = [100 - 2 * t for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_build_view__balance_at_bus_b__matches_link_inflow(view_result: pl.DataFrame) -> None:
    rows = metric_at(view_result, "BALANCE", "busB")
    assert len(rows) == 24
    expected = [-(100 - 2 * t) for t in range(1, 25)]
    assert rows["metric_value"].to_list() == expected


def test_build_view_from_parquet_simu_table__print_it_in_csv__check_view_format(test_3_study: Path) -> None:
    # Arrange
    sinker = CsvViewSinker(test_3_study)

    # Act
    run(test_3_study, sinker)

    # Assert
    result_files = list(test_3_study.glob("view*.csv"))
    assert result_files, "No result csv file written"
    assert not list(test_3_study.glob("view*.parquet")), "Unexpected parquet file written"
    assert pl.read_csv(result_files[0]).height > 0


def test_build_view__run_pipeline__emits_expected_log_messages(
    test_3_study: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Arrange
    sinker = ParquetViewSinker(test_3_study)

    # Act
    with caplog.at_level(logging.INFO):
        run(test_3_study, sinker)

    # Assert
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


def test_build_view__run_pipeline__creates_log_file(test_3_study: Path) -> None:
    # Arrange
    sinker = ParquetViewSinker(test_3_study)

    # Act
    run(test_3_study, sinker)

    # Assert
    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = repo_root / "logs"
    assert logs_dir.is_dir(), "logs/ directory was not created"
    log_files = list(logs_dir.glob("gems-views-builder-pipeline-run-*.log"))
    assert len(log_files) >= 1, f"Expected at least 1 log file, found {len(log_files)}"
    assert max(f.stat().st_size for f in log_files) > 0, "All log files are empty"


# ---------------------------------------------------------------------------
# Spatial aggregation (test_location_aggregation fixture)
# ---------------------------------------------------------------------------


def _loc_run(test_files_root: Path, tmp_path: Path, config_variant: str | None = None) -> pl.DataFrame:
    """Build the test_location_aggregation fixture and return the result DataFrame.

    config_variant: name of an alternative view_config file (without .yml) to
    copy over view_config.yml before running. None means use the default.
    """
    src = _location_aggregation_src(test_files_root)
    dst = tmp_path / f"loc_agg_{config_variant or 'default'}"
    shutil.copytree(src, dst)
    if config_variant is not None:
        shutil.copy(dst / f"{config_variant}.yml", dst / "view_config.yml")
    sinker = ParquetViewSinker(dst)
    run(dst, sinker)
    result_files = list(dst.glob("view*.parquet"))
    assert result_files, "No result parquet file written"
    return pl.read_parquet(result_files[0])


def test_country_collapse_fr(test_files_root: Path, tmp_path: Path) -> None:
    """PRODUCTION at '{FR}' = gen_FR1 + gen_FR2 summed per hour."""
    df = _loc_run(test_files_root, tmp_path)
    rows = metric_at(df, "PRODUCTION", "FR")
    assert rows["metric_value"].to_list() == [20, 40, 60, 80]
    assert df.filter(pl.col("metric_location").is_in(["area_FR1", "area_FR2"])).is_empty()


def test_country_collapse_de(test_files_root: Path, tmp_path: Path) -> None:
    """PRODUCTION at '{DE}' = gen_DE alone."""
    df = _loc_run(test_files_root, tmp_path)
    rows = metric_at(df, "PRODUCTION", "DE")
    assert rows["metric_value"].to_list() == [10, 20, 30, 40]


def test_unknown_sentinel_keep(test_files_root: Path, tmp_path: Path) -> None:
    """gen_orph has no country property; on_missing=keep routes it to '{<unknown>}'."""
    df = _loc_run(test_files_root, tmp_path)
    rows = metric_at(df, "PRODUCTION", "<unknown>")
    assert rows["metric_value"].to_list() == [10, 20, 30, 40]
    assert df.filter(pl.col("metric_location") == "area_orph").is_empty()


def test_unknown_drop(test_files_root: Path, tmp_path: Path) -> None:
    """on_missing=drop excludes gen_orph; FR and DE totals unchanged."""
    df = _loc_run(test_files_root, tmp_path, config_variant="view_config_drop")
    assert df.filter(pl.col("metric_location") == "<unknown>").is_empty()
    assert df.filter(pl.col("metric_location") == "area_orph").is_empty()
    assert metric_at(df, "PRODUCTION", "FR")["metric_value"].to_list() == [20, 40, 60, 80]
    assert metric_at(df, "PRODUCTION", "DE")["metric_value"].to_list() == [10, 20, 30, 40]


def test_balance_location_collapse(test_files_root: Path, tmp_path: Path) -> None:
    """BALANCE link flows appear at country-level labels, not raw area IDs."""
    df = _loc_run(test_files_root, tmp_path)
    assert metric_at(df, "BALANCE", "FR")["metric_value"].to_list() == [5, 5, 5, 5]
    assert metric_at(df, "BALANCE", "DE")["metric_value"].to_list() == [-5, -5, -5, -5]
    assert df.filter(
        (pl.col("metric_id") == "BALANCE") & pl.col("metric_location").is_in(["area_FR1", "area_DE"])
    ).is_empty()


def test_no_location_key_regression(test_files_root: Path, tmp_path: Path) -> None:
    """Without a location key, PRODUCTION rows carry raw area IDs — feature is opt-in."""
    df = _loc_run(test_files_root, tmp_path, config_variant="view_config_no_location")
    for area in ("area_FR1", "area_FR2", "area_DE", "area_orph"):
        rows = metric_at(df, "PRODUCTION", area)
        assert rows["metric_value"].to_list() == [10, 20, 30, 40], f"unexpected values for {area}"
    assert df.filter(pl.col("metric_location").is_in(["FR", "DE", "<unknown>"])).is_empty()
