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
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.input.calendar import Calendar

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


@dataclass
class FilteredSimulationTable:
    """Lazy representation of a filtered SIMULATION_TABLE parquet file.

    Has all SIMULATION_TABLE columns plus granular_date from the calendar join.
    """

    file_path: Path
    dataframe: pl.LazyFrame

    def cleanup(self) -> None:
        logging.info(f"Cleaning filtered simulation table {self.file_path}")
        self.file_path.unlink(missing_ok=True)


def load_simulation_table(simulation_table_file: Path) -> SimulationTable:
    """Load and validate a simulation table from a parquet file."""
    if simulation_table_file.suffix.lower() != ".parquet":
        raise ValueError(f"Simulation table file '{simulation_table_file}' is not a parquet file")
    logging.info(f"Loading simulation table from {simulation_table_file}")
    dataframe = pl.scan_parquet(simulation_table_file)
    validate_columns(dataframe, simulation_table_file.stem, SIMULATION_TABLE_COLUMNS, "SimulationTable")
    logging.info(f"Simulation table {simulation_table_file.stem!r} successfully loaded from {simulation_table_file}")
    return SimulationTable(dataframe)


def filter_simulation_table(
    simulation_table: SimulationTable, calendar: Calendar, intermediates_dir: Path
) -> FilteredSimulationTable:
    """Filter simulation_table by calendar, persist result to intermediates_dir, and return it."""
    logging.info("Filtering simulation table by calendar")
    intermediates_dir.mkdir(parents=True, exist_ok=True)
    output_path = intermediates_dir / "simulation_table_filtered.parquet"

    # Time-dependent rows: keep only timesteps present in the calendar.
    time_dep_path = output_path.with_suffix(".time_dep.parquet")
    (
        simulation_table.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .drop("block_right")
    ).sink_parquet(time_dep_path, compression="zstd", compression_level=3)

    # Non-time-dependent rows (absolute_time_index IS NULL) are not tied
    # to any timestep; pass them through with a null granular_date so
    # their constant values are preserved in the view.
    non_time_dep_path = output_path.with_suffix(".non_time_dep.parquet")
    granular_date_dtype = pl.read_parquet_schema(time_dep_path)["granular_date"]
    (
        simulation_table.dataframe.filter(pl.col("absolute_time_index").is_null()).with_columns(
            pl.lit(None).cast(granular_date_dtype).alias("granular_date")
        )
    ).sink_parquet(non_time_dep_path, compression="zstd", compression_level=3)

    pl.scan_parquet([time_dep_path, non_time_dep_path]).sink_parquet(
        output_path, compression="zstd", compression_level=3, row_group_size=64_000
    )
    time_dep_path.unlink()
    non_time_dep_path.unlink()
    logging.info(f"Filtered simulation table written to {output_path}")

    dataframe = pl.scan_parquet(output_path)
    validate_columns(dataframe, output_path.stem, FILTERED_SIMULATION_TABLE_COLUMNS, "FilteredSimulationTable")
    return FilteredSimulationTable(output_path, dataframe)


def validate_columns(dataframe: pl.LazyFrame, table_id: str, expected: frozenset[str], label: str) -> None:
    actual = frozenset(dataframe.collect_schema().names())
    missing = expected - actual
    extra = actual - expected
    errors: list[str] = []
    if missing:
        errors.append(f"Missing columns: {missing}")
    if extra:
        errors.append(f"Unexpected columns: {extra}")
    if errors:
        raise ValueError(f"{label} '{table_id}' has invalid columns: {'; '.join(errors)}")
