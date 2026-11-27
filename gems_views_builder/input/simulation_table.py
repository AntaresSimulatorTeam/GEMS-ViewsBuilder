# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.common import sink_by_chunk_id
from gems_views_builder.input.calendar import Calendar
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.metric_view import MetricView

# Columns of the SIMULATION_TABLE:
# block               (str)   – identifies the timeblock in the simulation
# component           (str)   – identifies the component
# output              (str)   – variable, port_field, or extra-output of the component
# absolute_time_index (int | None) – None if output is not time-dependent
# block_time_index    (int | None) – time index within the block; None if not time-dependent
# scenario_index      (int | None) – None if output is not scenario-dependent
# value               (float) – value of output at (absolute_time_index, scenario_index)
# basis_status        (str)   – basis status of the output
SIMULATION_TABLE_COLUMNS: frozenset[str] = frozenset(
    {
        "block",
        "component",
        "output",
        "absolute_time_index",
        "block_time_index",
        "scenario_index",
        "value",
        "basis_status",
    }
)

# Filtered simulation table has all SIMULATION_TABLE columns plus calendar/pair columns
FILTERED_SIMULATION_TABLE_COLUMNS: frozenset[str] = SIMULATION_TABLE_COLUMNS | {
    "granular_date",
    "pair_id",
    "chunk_id",
}


@dataclass
class SimulationTable:
    """Lazy representation of the SIMULATION_TABLE parquet file."""

    dataframe: pl.LazyFrame


@dataclass
class PersistentSimulationTable(SimulationTable):
    """Lazy representation of a persistent SIMULATION_TABLE parquet file.

    Has all SIMULATION_TABLE columns plus granular_date from the calendar join.
    """

    file_path: Path

    def __del__(self) -> None:
        logging.debug(f"Cleaning filtered simulation table {self.file_path}")
        self.file_path.unlink(missing_ok=True)


def load_simulation_tables(simulation_tables: list[Path]) -> list[SimulationTable]:
    return [load_simulation_table(simulation_table) for simulation_table in simulation_tables]


def load_simulation_table(simulation_table_file: Path) -> SimulationTable:
    """Load a simulation table from a parquet or csv file."""
    suffix = simulation_table_file.suffix.lower()
    logging.info(f"Loading simulation table from {simulation_table_file}")
    if suffix == ".parquet":
        dataframe = pl.scan_parquet(simulation_table_file)
    elif suffix == ".csv":
        dataframe = pl.scan_csv(simulation_table_file)
    else:
        raise ValueError(f"Simulation table file '{simulation_table_file}' is not a parquet or csv file")
    logging.info(f"Simulation table {simulation_table_file.stem!r} successfully loaded from {simulation_table_file}")
    return SimulationTable(dataframe)


def filter_simulation_table(
    simulation_table: pl.LazyFrame, calendar: Calendar, pair_lookup_table: pl.LazyFrame
) -> pl.LazyFrame:
    """Reduce the simulation table to the rows the views need.

    1. Keep only (component, output) pairs present in the pair lookup table(pairs used over view config metrics), then drop
       those string columns. Later joins use pair_id, and joining on an integer is much
       faster than joining on a string.
    2. Keep only timesteps present in the calendar.
    """
    needed_pairs = select_needed_pairs(simulation_table, pair_lookup_table)
    return attach_granular_dates(needed_pairs, calendar)


def join(
    metric_structure_table: MetricStructureTable,
    filtered_simulation_table_chunks: dict[int, PersistentSimulationTable],
) -> MetricView:
    simulation_table_chunks = [
        filtered_simulation_table_chunks[chunk_id].dataframe
        for chunk_id in metric_structure_table.get_unique_chunk_ids()
    ]
    st = pl.concat(simulation_table_chunks)
    return MetricView(lazyframe=st.join(metric_structure_table.dataframe, on="pair_id", how="right"))


def select_needed_pairs(simulation_table: pl.LazyFrame, pair_lookup_table: pl.LazyFrame) -> pl.LazyFrame:
    return simulation_table.join(pair_lookup_table, on=["component", "output"], how="inner").drop("component", "output")


def attach_granular_dates(simulation_table: pl.LazyFrame, calendar: Calendar) -> pl.LazyFrame:
    """
    Purpose of this function is to attach granular dates to the simulation table.
    """
    # Time-dependent rows: keep only timesteps present in the calendar.
    time_dep = (
        simulation_table.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
    )
    # Non-time-dependent rows are not tied to a timestep, keep them with a null date.
    # This could be improved once we merge PR213 into main
    granular_date_dtype = calendar.dataframe.collect_schema()["granular_date"]
    non_time_dep = simulation_table.filter(pl.col("absolute_time_index").is_null()).with_columns(
        pl.lit(None).cast(granular_date_dtype).alias("granular_date")
    )

    columns = time_dep.collect_schema().names()
    return pl.concat([time_dep.select(columns), non_time_dep.select(columns)])


def create_simulation_table_chunks(
    final_st: pl.LazyFrame, intermediate_dir: Path
) -> dict[int, PersistentSimulationTable]:
    sink_by_chunk_id(final_st, intermediate_dir)
    simulation_table_chunks = dict[int, PersistentSimulationTable]()

    for path in intermediate_dir.glob("filtered_simulation_table_chunk_*.parquet"):
        chunk_id = int(path.stem.split("_")[-1])
        simulation_table_chunks[chunk_id] = PersistentSimulationTable(dataframe=pl.scan_parquet(path), file_path=path)

    return simulation_table_chunks
