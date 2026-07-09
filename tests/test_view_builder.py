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
from gems_views_builder.metrics_structure_builder import format_metric_location
from gems_views_builder.view import CsvViewSinker, ParquetViewSinker


def copy_study_in_tmp(src: Path, tmp_path: Path) -> Path:
    dst = tmp_path / src.name
    shutil.copytree(src, dst)
    return dst


@pytest.fixture()
def test_3_study(test_files_root: Path, tmp_path: Path) -> Path:
    return copy_study_in_tmp(test_files_root / "test_3", tmp_path)


@pytest.fixture()
def view_result(test_3_study: Path) -> pl.DataFrame:
    sinker = ParquetViewSinker(test_3_study)
    run(test_3_study, sinker)
    result_files = list(test_3_study.glob("view*.parquet"))
    assert result_files, "No result parquet file written"
    return pl.read_parquet(result_files[0])


def metric_at(df: pl.DataFrame, metric_id: str, location: str) -> pl.DataFrame:
    encoded = format_metric_location((location,))
    return df.filter((pl.col("metric_id") == metric_id) & (pl.col("metric_location") == encoded)).sort("view_date")


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
