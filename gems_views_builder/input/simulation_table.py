# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.input.calendar import Calendar
from gems_views_builder.metric_structure_table import MetricStructureTable

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

# Filtered simulation table has all SIMULATION_TABLE columns plus granular_date from the calendar join
FILTERED_SIMULATION_TABLE_COLUMNS: frozenset[str] = SIMULATION_TABLE_COLUMNS | {"granular_date"}


@dataclass
class SimulationTable:
    """Lazy representation of the SIMULATION_TABLE parquet file."""

    dataframe: pl.LazyFrame


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


def filter_simulation_table(simulation_table: pl.LazyFrame, calendar: Calendar) -> pl.LazyFrame:
    """Filter a simulation table by the calendar and keep the result lazy.

    Time-dependent rows are kept only when their ``(absolute_time_index, block)`` is in the calendar.
    Non-time-dependent rows are kept with a null ``granular_date``.
    """
    logging.info("Filtering simulation table by calendar")
    # Time-dependent rows: keep only timesteps present in the calendar.
    time_dep = (
        simulation_table.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
    )
    # Non-time-dependent rows are not tied to a timestep, keep them with a null date.
    granular_date_dtype = calendar.dataframe.collect_schema()["granular_date"]
    non_time_dep = simulation_table.filter(pl.col("absolute_time_index").is_null()).with_columns(
        pl.lit(None).cast(granular_date_dtype).alias("granular_date")
    )
    columns = time_dep.collect_schema().names()
    return pl.concat([time_dep.select(columns), non_time_dep.select(columns)])


def join(metric_structure_table: MetricStructureTable, filtered_st: pl.LazyFrame) -> pl.LazyFrame:
    return filtered_st.join(metric_structure_table.dataframe, on=["component", "output"], how="right")
