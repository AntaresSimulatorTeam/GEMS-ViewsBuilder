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

from pathlib import Path

import polars as pl
import pytest

from gems_views_builder import FilteredSimulationTable, SimulationTable, load_calendar

# ---- Parametrized integration test: logical assertions (no golden overwrite) ----


def test_filter_simulation_table_logical(tmp_path: Path, test_dataset_dir: Path) -> None:
    """Filtered result must satisfy: every row (absolute_time_index, block) in calendar, correct count, rows from sim table."""
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    calendar = load_calendar(test_dataset_dir, "calendar_file")
    simulation_table = SimulationTable.load(simulation_table_file)
    out_file = tmp_path / "filtered_logical.parquet"

    filtered_table = simulation_table.filter_simulation_table(calendar, output_path=out_file)
    assert isinstance(filtered_table, FilteredSimulationTable)
    filtered = pl.read_parquet(out_file)

    # Time-dependent rows must have (absolute_time_index, block) in the calendar.
    # Non-time-dependent rows (null absolute_time_index) are passed through as-is.
    time_dep = filtered.filter(pl.col("absolute_time_index").is_not_null())
    calendar_df = calendar.dataframe.collect()
    in_calendar = time_dep.join(calendar_df, on=["absolute_time_index", "block"], how="semi")
    assert in_calendar.height == time_dep.height, (
        "Every filtered row must have (absolute_time_index, block) in the calendar"
    )

    # Total count = time-dep (inner join + block match) + non-time-dep (null index)
    time_dep_count = (
        simulation_table.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .collect(engine="streaming")
        .height
    )
    non_time_dep_count = (
        simulation_table.dataframe.filter(pl.col("absolute_time_index").is_null()).collect(engine="streaming").height
    )
    expected_total = time_dep_count + non_time_dep_count
    assert filtered.height == expected_total, "Filtered count must equal calendar-matched plus non-time-dependent rows"


def test_filter_simulation_table_drops_mismatched_block(tmp_path: Path, test_dataset_dir: Path) -> None:
    """Rows whose block does not match the calendar's block for a given absolute_time_index are dropped."""
    calendar = load_calendar(test_dataset_dir, "calendar_file")
    base_sim_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    base_sim_table = SimulationTable.load(base_sim_table_file)

    # Duplicate rows with block=2 so they do not match calendar (block=1)
    base_df = base_sim_table.dataframe.collect(engine="streaming")
    block_dtype = base_df["block"].dtype
    duplicated = base_df.with_columns(pl.lit(2).cast(block_dtype).alias("block"))
    sim_path_block2 = tmp_path / "simulation_table_block2_only.parquet"
    duplicated.write_parquet(sim_path_block2)
    simulation_table = SimulationTable.load(sim_path_block2)

    out_file = tmp_path / "filtered_empty.parquet"
    filtered_table = simulation_table.filter_simulation_table(calendar, output_path=out_file)
    assert isinstance(filtered_table, FilteredSimulationTable)
    filtered = pl.read_parquet(out_file)
    # Time-dependent rows with block=2 are all dropped; only non-time-dependent
    # rows (null absolute_time_index) are preserved regardless of block.
    non_time_dep_count = duplicated.filter(pl.col("absolute_time_index").is_null()).height
    assert filtered.height == non_time_dep_count


def test_filter_simulation_table_writes_parquet(
    tmp_path: Path,
    test_dataset_dir: Path,
) -> None:
    """When output_path is set, the filtered table is written to parquet with expected content."""
    calendar = load_calendar(test_dataset_dir, "calendar_file")
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    simulation_table = SimulationTable.load(simulation_table_file)
    out_file = tmp_path / "filtered_calendar_file.parquet"

    filtered_table = simulation_table.filter_simulation_table(calendar, output_path=out_file)
    assert isinstance(filtered_table, FilteredSimulationTable)

    assert out_file.exists(), "Output parquet should be created"
    written = pl.scan_parquet(out_file).collect()
    expected = (
        simulation_table.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
        .collect(engine="streaming")
    )
    sort_cols = ["block", "component", "output", "absolute_time_index", "block_time_index", "scenario_index"]
    granular_date_dtype = written.schema["granular_date"]
    non_time_dep = (
        simulation_table.dataframe.filter(pl.col("absolute_time_index").is_null())
        .with_columns(pl.lit(None).cast(granular_date_dtype).alias("granular_date"))
        .collect(engine="streaming")
    )
    expected = pl.concat([expected, non_time_dep])
    written_sorted = written.select(expected.columns).sort(sort_cols)
    expected_sorted = expected.sort(sort_cols)
    assert written_sorted.equals(expected_sorted), "Written parquet sim-table columns should match expected"


def test_filter_simulation_table_invalid_file_format(test_dataset_dir: Path) -> None:
    """When a non-parquet file is provided, an error is raised."""
    simulation_table_file = test_dataset_dir / "simulation_table--invalid.csv"
    with pytest.raises(
        ValueError,
        match=r"Simulation table file '.*simulation_table--invalid\.csv' is not a parquet file",
    ):
        SimulationTable(simulation_table_file)
