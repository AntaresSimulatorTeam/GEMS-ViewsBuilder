# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.common import sink_by_bucket_id
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
    "bucket_id",
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
        # Delete only this file so sibling bucket files in the same temp dir stay alive.
        # Remove the parent dir when it becomes empty.
        logging.debug(f"Cleaning filtered simulation table {self.file_path}")
        self.file_path.unlink(missing_ok=True)
        parent = self.file_path.parent
        try:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            logging.debug(f"Could not remove empty dir {parent}", exc_info=True)


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
) -> list[PersistentSimulationTable]:
    """Filter by pair lookup + calendar, partition by bucket_id, return one table per bucket."""
    pre_filtered_st = pre_filter_simulation_table(simulation_table, pair_lookup_table)

    logging.info("Filtering simulation table by calendar")
    intermediates_dir = Path(tempfile.mkdtemp())

    # Time-dependent rows: keep only timesteps present in the calendar.
    time_dep = (
        pre_filtered_st.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right", "component", "output")
    )
    # Non-time-dependent rows are not tied to a timestep, keep them with a null date.
    granular_date_dtype = calendar.dataframe.collect_schema()["granular_date"]
    non_time_dep = (
        pre_filtered_st.filter(pl.col("absolute_time_index").is_null())
        .with_columns(pl.lit(None).cast(granular_date_dtype).alias("granular_date"))
        .drop("component", "output")
    )

    columns = time_dep.collect_schema().names()
    final_st = pl.concat([time_dep.select(columns), non_time_dep.select(columns)])

    sink_by_bucket_id(final_st, intermediates_dir)
    logging.info(f"Filtered simulation table written to {intermediates_dir}")

    filtered_simulation_tables = [
        PersistentSimulationTable(dataframe=pl.scan_parquet(path), file_path=path)
        for path in sorted(intermediates_dir.glob("filtered_simulation_table_bucket_*.parquet"))
    ]
    logging.info(f"Filtered simulation table has {len(filtered_simulation_tables)} bucket file(s)")
    return filtered_simulation_tables


def join(
    metric_structure_table: MetricStructureTable, filtered_simulation_table: PersistentSimulationTable
) -> MetricView:
    return MetricView(
        lazyframe=filtered_simulation_table.dataframe.join(
            metric_structure_table.dataframe, on=["component", "output"], how="right"
        )
    )


def pre_filter_simulation_table(simulation_table: pl.LazyFrame, pair_lookup_table: pl.LazyFrame) -> pl.LazyFrame:
    return simulation_table.join(pair_lookup_table, on=["component", "output"], how="inner").drop("component", "output")
