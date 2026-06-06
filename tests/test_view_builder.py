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
from gems_views_builder.views import ViewBuilder


@pytest.fixture()
def view_result(test_files_root: Path, tmp_path: Path) -> pl.DataFrame:
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
    return pl.read_parquet(result_file)


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
    # load_AL.active_load = 100 (not time-dependent)
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
