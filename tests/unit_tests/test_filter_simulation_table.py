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

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl  # noqa: E402
import pytest  # noqa: E402

from src import FilteredSimulationTable, SimulationTable, load_calendar  # noqa: E402

TEST_FILES_ROOT = ROOT_DIR / "resources" / "test_files"

# Existing calendar + simulation table pairs
FILTER_TEST_CASES = [
    (
        TEST_FILES_ROOT / "test_3" / "calendar_file.csv",
        TEST_FILES_ROOT / "test_3" / "simulation_table--20260318-0623.csv",
    ),
]


# ---- Parametrized integration test: logical assertions (no golden overwrite) ----


@pytest.mark.parametrize("calendar_file, simulation_table_file", FILTER_TEST_CASES)
def test_filter_simulation_table_logical(tmp_path: Path, calendar_file: Path, simulation_table_file: Path) -> None:
    """Filtered result must satisfy: every row (absolute_time_index, block) in calendar, correct count, rows from sim table."""
    calendar = load_calendar(calendar_file)
    simulation_table = SimulationTable(simulation_table_file)
    out_file = tmp_path / "filtered_logical.csv"

    filtered_table = simulation_table.filter_simulation_table(calendar, output_path=out_file)
    assert isinstance(filtered_table, FilteredSimulationTable)
    filtered = pl.read_csv(out_file, null_values=["None"], try_parse_dates=True)

    # 1. Every row in the result has (absolute_time_index, block) present in the calendar
    calendar_df = calendar.dataframe.collect()
    in_calendar = filtered.join(calendar_df, on=["absolute_time_index", "block"], how="semi")
    assert in_calendar.height == filtered.height, (
        "Every filtered row must have (absolute_time_index, block) in the calendar"
    )

    # 2. Result has exactly the rows that belong to the calendar block (spec: inner join + block match)
    expected_count = (
        simulation_table.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .collect(engine="streaming")
        .height
    )
    assert filtered.height == expected_count, (
        "Filtered row count must equal simulation rows whose (absolute_time_index, block) is in the calendar"
    )


@pytest.mark.parametrize("tmp_path", [None], indirect=True)
def test_filter_simulation_table_drops_mismatched_block(tmp_path: Path) -> None:
    """Rows whose block does not match the calendar's block for a given absolute_time_index are dropped."""
    calendar_file = TEST_FILES_ROOT / "test_3" / "calendar_file.csv"
    base_sim_table_file = TEST_FILES_ROOT / "test_3" / "simulation_table--20260318-0623.csv"

    calendar = load_calendar(calendar_file)
    base_sim_table = SimulationTable(base_sim_table_file)

    # Duplicate rows with block=2 so they do not match calendar (block=1)
    base_df = base_sim_table.dataframe.collect(engine="streaming")
    block_dtype = base_df["block"].dtype
    duplicated = base_df.with_columns(pl.lit(2).cast(block_dtype).alias("block"))
    sim_path_block2 = tmp_path / "simulation_table_block2_only.csv"
    duplicated.write_csv(sim_path_block2)
    simulation_table = SimulationTable(sim_path_block2)

    out_file = tmp_path / "filtered_empty.csv"
    filtered_table = simulation_table.filter_simulation_table(calendar, output_path=out_file)
    assert isinstance(filtered_table, FilteredSimulationTable)
    filtered = pl.read_csv(out_file, null_values=["None"], try_parse_dates=True)
    assert filtered.height == 0


@pytest.mark.parametrize("calendar_file, simulation_table_file", FILTER_TEST_CASES)
def test_filter_simulation_table_writes_csv(
    tmp_path: Path,
    calendar_file: Path,
    simulation_table_file: Path,
) -> None:
    """When output_path is set, the filtered table is written to CSV with expected content."""
    calendar = load_calendar(calendar_file)
    simulation_table = SimulationTable(simulation_table_file)
    out_file = tmp_path / f"filtered_{calendar_file.stem}.csv"

    filtered_table = simulation_table.filter_simulation_table(calendar, output_path=out_file)
    assert isinstance(filtered_table, FilteredSimulationTable)

    assert out_file.exists(), "Output CSV should be created"
    written = pl.scan_csv(out_file, null_values=["None"], try_parse_dates=True).collect()
    expected = (
        simulation_table.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
        .collect(engine="streaming")
    )
    sort_cols = ["block", "component", "output", "absolute_time_index", "block_time_index", "scenario_index"]
    written_sorted = written.select(expected.columns).sort(sort_cols)
    expected_sorted = expected.sort(sort_cols)
    assert written_sorted.equals(expected_sorted), "Written CSV sim-table columns should match expected"
