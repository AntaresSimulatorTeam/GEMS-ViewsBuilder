# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from gems_views_builder import Calendar, PersistentSimulationTable, load_calendar
from gems_views_builder.input.simulation_table import (
    SimulationTable,
    filter_simulation_table,
    load_simulation_table,
)
from gems_views_builder.input.view_building_input import concat_simulation_tables
from gems_views_builder.pair_id import make_pair_id, make_pair_lookup
from tests.common import make_simulation_table_row


def all_pairs(simulation_table: pl.LazyFrame) -> set[tuple[str, str]]:
    pairs = simulation_table.select("component", "output").drop_nulls().unique().collect()
    return set(zip(pairs["component"], pairs["output"], strict=True))


def with_needed_pair(simulation_table: pl.LazyFrame) -> pl.LazyFrame:
    """Rows with a null component or output can never be needed by a metric."""
    return simulation_table.drop_nulls(["component", "output"])


def with_pair_id(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Replace (component, output) by their pair_id, like the filtered table does."""
    lookup = make_pair_lookup(all_pairs(dataframe.lazy()), bucket_count=1).select("component", "output", "pair_id")
    return dataframe.join(lookup, on=["component", "output"]).drop("component", "output")


# ---- Parametrized integration test: logical assertions (no golden overwrite) ----


def test_filter_simulation_table_logical(tmp_path: Path, test_dataset_dir: Path) -> None:
    """Filtered result must satisfy: every row (absolute_time_index, block) in calendar, correct count, rows from sim table."""
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    calendar = load_calendar(test_dataset_dir / "calendar_file.csv")
    simulation_table = load_simulation_table(simulation_table_file)

    filtered_table = filter_simulation_table(
        simulation_table.dataframe, calendar, all_pairs(simulation_table.dataframe)
    )
    assert isinstance(filtered_table, PersistentSimulationTable)
    filtered = filtered_table.dataframe.collect()

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
        with_needed_pair(simulation_table.dataframe)
        .join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .collect(engine="streaming")
        .height
    )
    non_time_dep_count = (
        with_needed_pair(simulation_table.dataframe)
        .filter(pl.col("absolute_time_index").is_null())
        .collect(engine="streaming")
        .height
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

    filtered_table = filter_simulation_table(
        simulation_table.dataframe, calendar, all_pairs(simulation_table.dataframe)
    )
    assert isinstance(filtered_table, PersistentSimulationTable)
    filtered = filtered_table.dataframe.collect()
    # Time-dependent rows with block=2 are all dropped; only non-time-dependent
    # rows (null absolute_time_index) are preserved regardless of block.
    non_time_dep_count = (
        duplicated.drop_nulls(["component", "output"]).filter(pl.col("absolute_time_index").is_null()).height
    )
    assert filtered.height == non_time_dep_count


def test_filter_simulation_table_writes_parquet(
    tmp_path: Path,
    test_dataset_dir: Path,
) -> None:
    """The filtered table is written to parquet with expected content."""
    calendar = load_calendar(test_dataset_dir / "calendar_file.csv")
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    simulation_table = load_simulation_table(simulation_table_file)

    filtered_table = filter_simulation_table(
        simulation_table.dataframe, calendar, all_pairs(simulation_table.dataframe)
    )
    assert isinstance(filtered_table, PersistentSimulationTable)

    assert any(filtered_table.dir_path.glob("pair_bucket=*/*.parquet")), "Clustered parquet files should be created"
    written = filtered_table.dataframe.collect()
    expected = (
        with_needed_pair(simulation_table.dataframe)
        .join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
        .collect(engine="streaming")
    )
    granular_date_dtype = written.schema["granular_date"]
    non_time_dep = (
        with_needed_pair(simulation_table.dataframe)
        .filter(pl.col("absolute_time_index").is_null())
        .with_columns(pl.lit(None).cast(granular_date_dtype).alias("granular_date"))
        .collect(engine="streaming")
    )
    expected = with_pair_id(pl.concat([expected, non_time_dep]))
    sort_cols = ["block", "pair_id", "absolute_time_index", "block_time_index", "scenario_index"]
    written_sorted = written.select(expected.columns).sort(sort_cols)
    expected_sorted = expected.sort(sort_cols)
    assert written_sorted.equals(expected_sorted), "Written parquet sim-table columns should match expected"


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
    st_a = SimulationTable(pl.DataFrame([make_simulation_table_row(component="comp-a", block=block_a)]).lazy())
    st_b = SimulationTable(pl.DataFrame([make_simulation_table_row(component="comp-b", block=block_b)]).lazy())

    # Act
    needed_pairs = {("comp-a", "out"), ("comp-b", "out")}
    filtered_table = filter_simulation_table(concat_simulation_tables([st_a, st_b]), calendar, needed_pairs)

    # Assert
    filtered = filtered_table.dataframe.collect()
    assert set(filtered["pair_id"].to_list()) == {make_pair_id(c, "out") for c in expected_components}


def test_filter_simulation_table_drops_pairs_not_needed_by_any_metric() -> None:
    # Arrange
    calendar = make_single_row_calendar(absolute_time_index=1, block="b1", granular_date=datetime(2026, 1, 1))
    rows = [
        make_simulation_table_row(component="comp-a", output="out"),
        make_simulation_table_row(component="comp-a", output="unused-output"),
        make_simulation_table_row(component="unused-comp", output="out"),
        make_simulation_table_row(component="comp-b", output="out", absolute_time_index=None, block_time_index=None),
    ]
    simulation_table = pl.DataFrame(rows).lazy()

    # Act
    filtered_table = filter_simulation_table(simulation_table, calendar, {("comp-a", "out"), ("comp-b", "out")})

    # Assert
    filtered = filtered_table.dataframe.collect()
    expected_ids = [make_pair_id("comp-a", "out"), make_pair_id("comp-b", "out")]
    assert sorted(filtered["pair_id"].to_list()) == sorted(expected_ids)
    assert "component" not in filtered.columns
    assert "output" not in filtered.columns
    bucket_dirs = {d.name for d in filtered_table.dir_path.iterdir()}
    assert bucket_dirs == {f"pair_bucket={b}" for b in filtered["pair_bucket"].to_list()}


def test_filter_simulation_table_with_no_needed_pair_is_empty() -> None:
    calendar = make_single_row_calendar(absolute_time_index=1, block="b1", granular_date=datetime(2026, 1, 1))
    simulation_table = pl.DataFrame([make_simulation_table_row()]).lazy()

    filtered_table = filter_simulation_table(simulation_table, calendar, set())

    filtered = filtered_table.dataframe.collect()
    assert filtered.height == 0
    assert {"pair_id", "pair_bucket", "value", "granular_date"} <= set(filtered.columns)
