# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.common import sink_to_parquet
from gems_views_builder.input.calendar import Calendar
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.pair_id import bucket_count_for, bucket_of, make_pair_lookup

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

# Filtered simulation table is compact: the (component, output) strings are replaced by
# their MurmurHash3 ``pair_id`` (see gems_views_builder.pair_id), and rows are clustered
# on disk by ``pair_bucket`` (hive partitions). granular_date comes from the calendar join.
FILTERED_SIMULATION_TABLE_COLUMNS: frozenset[str] = (SIMULATION_TABLE_COLUMNS - {"component", "output"}) | {
    "granular_date",
    "pair_id",
    "pair_bucket",
}


@dataclass
class SimulationTable:
    """Lazy representation of the SIMULATION_TABLE parquet file."""

    dataframe: pl.LazyFrame


@dataclass
class PersistentSimulationTable(SimulationTable):
    """Lazy representation of the persisted, filtered and clustered SIMULATION_TABLE.

    Columns: FILTERED_SIMULATION_TABLE_COLUMNS. Stored under ``dir_path`` as hive
    partitions ``pair_bucket=<k>/*.parquet`` with ``k = pair_id % bucket_count``.
    """

    dir_path: Path
    bucket_count: int

    def __del__(self) -> None:
        logging.debug(f"Cleaning filtered simulation table {self.dir_path}")
        rmtree(self.dir_path, ignore_errors=True)


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
    simulation_table: pl.LazyFrame,
    calendar: Calendar,
    needed_pairs: Iterable[tuple[str, str]],
) -> PersistentSimulationTable:
    """Keep only needed (component, output) pairs and calendar timesteps, then persist clustered by pair.

    ``needed_pairs`` are the (component, output) pairs referenced by at least one metric;
    every other row is dropped before the calendar join and before anything is written.
    """
    logging.info("Filtering simulation table by needed (component, output) pairs and calendar")
    needed_pairs = set(needed_pairs)
    bucket_count = bucket_count_for(len(needed_pairs))
    pair_lookup = make_pair_lookup(needed_pairs, bucket_count)
    logging.info(f"{pair_lookup.height} (component, output) pair(s) needed, clustered into {bucket_count} bucket(s)")

    # Small lookup table: inner join both drops unused pairs and attaches pair_id / pair_bucket.
    needed = simulation_table.join(pair_lookup.lazy(), on=["component", "output"], how="inner").drop(
        "component", "output"
    )
    # Time-dependent rows: keep only timesteps present in the calendar.
    time_dep = (
        needed.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
    )
    # Non-time-dependent rows are not tied to a timestep, keep them with a null date.
    granular_date_dtype = calendar.dataframe.collect_schema()["granular_date"]
    non_time_dep = needed.filter(pl.col("absolute_time_index").is_null()).with_columns(
        pl.lit(None).cast(granular_date_dtype).alias("granular_date")
    )
    columns = time_dep.collect_schema().names()
    filtered = pl.concat([time_dep.select(columns), non_time_dep.select(columns)])

    dir_path = Path(tempfile.mkdtemp())
    sink_to_parquet(filtered, pl.PartitionBy(dir_path, key="pair_bucket"))
    logging.info(f"Filtered simulation table written to {dir_path}")

    if any(dir_path.rglob("*.parquet")):
        dataframe = pl.scan_parquet(dir_path, hive_partitioning=True)
    else:
        # Nothing matched: a partitioned sink writes no file, and scanning an empty dir fails.
        dataframe = pl.LazyFrame(schema=filtered.collect_schema())
    return PersistentSimulationTable(dataframe=dataframe, dir_path=dir_path, bucket_count=bucket_count)


def join(metric_structure_table: MetricStructureTable, filtered_st: PersistentSimulationTable) -> pl.LazyFrame:
    """Join on ``pair_id``, reading only the clusters that hold this metric's pairs."""
    pair_ids = metric_structure_table.dataframe.select("pair_id").unique().collect()["pair_id"].to_list()
    buckets = sorted({bucket_of(pair_id, filtered_st.bucket_count) for pair_id in pair_ids})
    simulation_rows = filtered_st.dataframe.filter(pl.col("pair_bucket").is_in(buckets))
    return simulation_rows.join(metric_structure_table.dataframe, on="pair_id", how="right")
