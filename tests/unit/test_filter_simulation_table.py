# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder import Calendar, FilteredSimulationTable, load_calendar
from gems_views_builder.input.simulation_table import (
    SimulationTable,
    concat_simulation_tables,
    filter_simulation_table,
    load_simulation_table,
)

# ---- Parametrized integration test: logical assertions (no golden overwrite) ----


def test_filter_simulation_table_logical(tmp_path: Path, test_dataset_dir: Path) -> None:
    """Filtered result must satisfy: every row (absolute_time_index, block) in calendar, correct count, rows from sim table."""
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    calendar = load_calendar(test_dataset_dir / "calendar_file.csv")
    simulation_table = load_simulation_table(simulation_table_file)

    filtered_table = filter_simulation_table(simulation_table.dataframe, calendar)
    assert isinstance(filtered_table, FilteredSimulationTable)
    filtered = pl.read_parquet(filtered_table.file_path)

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
    calendar = load_calendar(test_dataset_dir / "calendar_file.csv")
    base_sim_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    base_sim_table = load_simulation_table(base_sim_table_file)

    # Duplicate rows with block=2 so they do not match calendar (block=1)
    base_df = base_sim_table.dataframe.collect(engine="streaming")
    block_dtype = base_df["block"].dtype
    duplicated = base_df.with_columns(pl.lit(2).cast(block_dtype).alias("block"))
    sim_path_block2 = tmp_path / "simulation_table_block2_only.parquet"
    duplicated.write_parquet(sim_path_block2)
    simulation_table = load_simulation_table(sim_path_block2)

    filtered_table = filter_simulation_table(simulation_table.dataframe, calendar)
    assert isinstance(filtered_table, FilteredSimulationTable)
    filtered = pl.read_parquet(filtered_table.file_path)
    # Time-dependent rows with block=2 are all dropped; only non-time-dependent
    # rows (null absolute_time_index) are preserved regardless of block.
    non_time_dep_count = duplicated.filter(pl.col("absolute_time_index").is_null()).height
    assert filtered.height == non_time_dep_count


def test_filter_simulation_table_writes_parquet(
    tmp_path: Path,
    test_dataset_dir: Path,
) -> None:
    """The filtered table is written to parquet with expected content."""
    calendar = load_calendar(test_dataset_dir / "calendar_file.csv")
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    simulation_table = load_simulation_table(simulation_table_file)

    filtered_table = filter_simulation_table(simulation_table.dataframe, calendar)
    assert isinstance(filtered_table, FilteredSimulationTable)

    assert filtered_table.file_path.exists(), "Output parquet should be created"
    written = filtered_table.dataframe.collect()
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
    """When a non-parquet, non-csv file is provided, an error is raised."""
    simulation_table_file = test_dataset_dir / "simulation_table--invalid.txt"
    with pytest.raises(
        ValueError,
        match=r"Simulation table file '.*simulation_table--invalid\.txt' is not a parquet or csv file",
    ):
        load_simulation_table(simulation_table_file)


def make_single_row_simulation_table_(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "block": "b1",
        "component": "comp",
        "output": "out",
        "absolute_time_index": 1,
        "block_time_index": 1,
        "scenario_index": 1,
        "value": 1.0,
        "basis_status": "ok",
    }
    row.update(overrides)
    return row


def make_single_row_calendar(absolute_time_index: int, block: str, granular_date: datetime) -> Calendar:
    return Calendar(
        id="calendar",
        dataframe=pl.DataFrame(
            {"absolute_time_index": [absolute_time_index], "block": [block], "granular_date": [granular_date]},
            schema_overrides={"granular_date": pl.Datetime},
        ).lazy(),
    )


@pytest.mark.parametrize(
    ("block_a", "block_b", "expected_components"),
    [
        ("b1", "b1", {"comp-a", "comp-b"}),
        ("b1", "b2", {"comp-a"}),
        ("b2", "b1", {"comp-b"}),
    ],
)
def test_filter_simulation_table_keeps_calendar_matching_rows_from_every_table(
    block_a: str,
    block_b: str,
    expected_components: set[str],
) -> None:
    # Arrange
    granular_date = datetime(2026, 1, 1)
    calendar = make_single_row_calendar(absolute_time_index=1, block="b1", granular_date=granular_date)
    st_a = SimulationTable(pl.DataFrame([make_single_row_simulation_table_(component="comp-a", block=block_a)]).lazy())
    st_b = SimulationTable(pl.DataFrame([make_single_row_simulation_table_(component="comp-b", block=block_b)]).lazy())

    # Act
    filtered_table = filter_simulation_table(concat_simulation_tables([st_a, st_b]), calendar)

    # Assert
    filtered = pl.read_parquet(filtered_table.file_path)
    assert set(filtered["component"].to_list()) == expected_components
