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

from gems_views_builder.common import save
from gems_views_builder.loader import Loader
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
    save(metric_views, results_dir)
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
        save(metric_views, results_dir)

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
