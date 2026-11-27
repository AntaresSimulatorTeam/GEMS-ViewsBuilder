# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp

import polars as pl
import pytest

from gems_views_builder import Calendar, PersistentSimulationTable, load_calendar
from gems_views_builder.common import CHUNK_NUMBER, murmur_hash
from gems_views_builder.input.simulation_table import (
    SimulationTable,
    create_simulation_table_chunks,
    filter_simulation_table,
    load_simulation_table,
)
from gems_views_builder.input.view_building_input import concat_simulation_tables
from tests.common import make_simulation_table_row


def pair_lookup_table(simulation_table: pl.LazyFrame) -> pl.LazyFrame:
    """One lookup row per (component, output), so calendar tests keep every simulation pair."""
    pairs = simulation_table.select(["component", "output"]).unique().collect()
    rows = []
    for component, output in pairs.iter_rows():
        pair_id = murmur_hash(str(component), str(output))
        rows.append(
            {
                "component": component,
                "output": output,
                "pair_id": pair_id,
                "chunk_id": pair_id % CHUNK_NUMBER,
            }
        )
    return pl.DataFrame(rows).lazy()


def collect_chunks(chunks: dict[int, PersistentSimulationTable]) -> pl.DataFrame:
    if not chunks:
        return pl.DataFrame()
    return pl.concat([chunk.dataframe.collect() for chunk in chunks.values()])


def filtered_chunks(
    simulation_table: pl.LazyFrame, calendar: Calendar, lookup: pl.LazyFrame
) -> dict[int, PersistentSimulationTable]:
    filtered = filter_simulation_table(simulation_table, calendar, lookup)
    return create_simulation_table_chunks(filtered, Path(mkdtemp()))


# ---- Parametrized integration test: logical assertions (no golden overwrite) ----


def test_filter_simulation_table_logical(tmp_path: Path, test_dataset_dir: Path) -> None:
    """Filtered result must satisfy: every row (absolute_time_index, block) in calendar, correct count, rows from sim table."""
    simulation_table_file = next(iter(sorted(test_dataset_dir.glob("simulation_table*.parquet"))))
    calendar = load_calendar(test_dataset_dir / "calendar_file.csv")
    simulation_table = load_simulation_table(simulation_table_file)

    filtered_tables = filtered_chunks(
        simulation_table.dataframe, calendar, pair_lookup_table(simulation_table.dataframe)
    )
    assert all(isinstance(chunk, PersistentSimulationTable) for chunk in filtered_tables.values())
    filtered = collect_chunks(filtered_tables)

    # Time-dependent rows must have (absolute_time_index, block) in the calendar.
    # Non-time-dependent rows (null absolute_time_index) are passed through as-is.
    time_dep = filtered.filter(pl.col("absolute_time_index").is_not_null())
    calendar_df = calendar.dataframe.collect()
    in_calendar = time_dep.join(calendar_df, on=["absolute_time_index", "block"], how="semi")
    assert in_calendar.height == time_dep.height, (
        "Every filtered row must have (absolute_time_index, block) in the calendar"
    )

    # Total count = pair-matched rows that are calendar time-dep or non-time-dep.
    # A null component cannot join the pair lookup, so that row is removed.
    matched = simulation_table.dataframe.join(
        pair_lookup_table(simulation_table.dataframe), on=["component", "output"], how="inner"
    )
    time_dep_count = (
        matched.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .collect(engine="streaming")
        .height
    )
    non_time_dep_count = matched.filter(pl.col("absolute_time_index").is_null()).collect(engine="streaming").height
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

    lookup = pair_lookup_table(simulation_table.dataframe)
    filtered_tables = filtered_chunks(simulation_table.dataframe, calendar, lookup)
    assert all(isinstance(chunk, PersistentSimulationTable) for chunk in filtered_tables.values())
    filtered = collect_chunks(filtered_tables)
    # Time-dependent rows with block=2 are all dropped; only non-time-dependent
    # rows (null absolute_time_index) are preserved regardless of block.
    # Rows with a null component are not a (component, output) pair, so they are removed.
    non_time_dep_count = (
        duplicated.join(lookup.collect(), on=["component", "output"], how="inner")
        .filter(pl.col("absolute_time_index").is_null())
        .height
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

    lookup = pair_lookup_table(simulation_table.dataframe)
    filtered_tables = filtered_chunks(simulation_table.dataframe, calendar, lookup)
    assert all(isinstance(chunk, PersistentSimulationTable) for chunk in filtered_tables.values())
    assert all(chunk.file_path.exists() for chunk in filtered_tables.values()), "Output parquet should be created"
    written = collect_chunks(filtered_tables)
    pre_filtered = simulation_table.dataframe.join(lookup, on=["component", "output"], how="inner").drop(
        "component", "output"
    )
    expected = (
        pre_filtered.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
        .collect(engine="streaming")
    )
    sort_cols = ["block", "pair_id", "absolute_time_index", "block_time_index", "scenario_index"]
    granular_date_dtype = written.schema["granular_date"]
    non_time_dep = (
        pre_filtered.filter(pl.col("absolute_time_index").is_null())
        .with_columns(pl.lit(None).cast(granular_date_dtype).alias("granular_date"))
        .collect(engine="streaming")
    )
    expected = pl.concat([expected, non_time_dep]).drop("chunk_id")
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
    simulation_table = concat_simulation_tables([st_a, st_b])
    lookup = pair_lookup_table(simulation_table)
    filtered_tables = filtered_chunks(simulation_table, calendar, lookup)

    # Assert
    filtered = collect_chunks(filtered_tables).join(lookup.collect(), on="pair_id", how="left")
    assert set(filtered["component"].to_list()) == expected_components


def test_pair_without_simulation_rows_has_no_chunk_file() -> None:
    """A lookup pair with no simulation rows is dropped by the filter, so its chunk gets no file."""
    calendar = make_single_row_calendar(absolute_time_index=1, block="b1", granular_date=datetime(2026, 1, 1))
    simulation_table = pl.DataFrame([make_simulation_table_row(component="comp-a")]).lazy()
    lookup = pair_lookup_table(simulation_table).collect()
    missing_chunk_id = next(chunk_id for chunk_id in range(CHUNK_NUMBER) if chunk_id not in set(lookup["chunk_id"]))
    missing_pair = pl.DataFrame(
        {
            "component": ["missing"],
            "output": ["out"],
            "pair_id": [murmur_hash("missing", "out")],
            "chunk_id": [missing_chunk_id],
        }
    ).cast(lookup.schema)
    chunks = filtered_chunks(simulation_table, calendar, pl.concat([lookup, missing_pair]).lazy())

    assert missing_chunk_id not in chunks
    assert set(chunks) == set(lookup["chunk_id"].to_list())
