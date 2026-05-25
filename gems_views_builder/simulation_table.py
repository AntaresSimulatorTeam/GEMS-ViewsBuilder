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

from gems_views_builder.calendar import Calendar
from gems_views_builder.common import logger

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


def validate_file_format(simulation_table_file: Path) -> None:
    logger.info(f"Validating parquet file format for {simulation_table_file}")
    if simulation_table_file.suffix.lower() != ".parquet":
        raise ValueError(f"Simulation table file '{simulation_table_file}' is not a parquet file")


class SimulationTable:
    """
    Lazy representation of the SIMULATION_TABLE CSV.
    Expected columns: see SIMULATION_TABLE_COLUMNS.
    """

    def __init__(self, simulation_table_file: Path) -> None:
        """
        Cheap constructor: keep only the file path and metadata.

        Use `SimulationTable.load(...)` to perform I/O and schema validation.
        """
        validate_file_format(simulation_table_file)
        self.file = simulation_table_file
        self.id = simulation_table_file.stem
        self._dataframe: pl.LazyFrame | None = None

    @property
    def dataframe(self) -> pl.LazyFrame:
        if self._dataframe is None:
            raise RuntimeError("SimulationTable is not loaded. Call SimulationTable.load(...) first.")
        return self._dataframe

    @classmethod
    def load(cls, simulation_table_file: Path) -> "SimulationTable":
        return cls(simulation_table_file).load_into_self()

    def load_into_self(self) -> "SimulationTable":
        logger.info(f"Loading simulation table from {self.file}")
        self._dataframe = pl.scan_parquet(self.file)
        self._check_simulation_table_columns()
        logger.info(f"Simulation table {self.id!r} loaded successfully")
        return self

    def _check_simulation_table_columns(self) -> None:
        logger.info(f"Validating simulation table columns for {self.id!r}")
        actual = frozenset(self.dataframe.collect_schema().names())
        missing = SIMULATION_TABLE_COLUMNS - actual
        extra = actual - SIMULATION_TABLE_COLUMNS
        errors: list[str] = []
        if missing:
            errors.append(f"Missing columns: {missing}")
        if extra:
            errors.append(f"Unexpected columns: {extra}")
        if errors:
            raise ValueError(f"SimulationTable '{self.id}' has invalid columns: {'; '.join(errors)}")
        logger.info(f"Simulation table {self.id!r} columns validated")

    def filter_simulation_table(self, calendar: Calendar, output_path: Path) -> "FilteredSimulationTable":
        """
        Filter the simulation table based on the calendar and write the result to output_path.
        Returns a FilteredSimulationTable with additional granular_date column from the calendar.
        """
        logger.info(f"Filtering simulation table {self.id!r} with calendar {calendar.id!r} into {output_path}")
        # Time-dependent rows: keep only timesteps present in the calendar.
        time_dep_path = output_path.with_suffix(".time_dep.parquet")
        logger.info(f"Writing time-dependent filtered rows to {time_dep_path}")
        (
            self.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
            .filter(pl.col("block") == pl.col("block_right"))
            .drop("block_right")
        ).sink_parquet(time_dep_path, compression="zstd", compression_level=3)

        # Non-time-dependent rows (absolute_time_index IS NULL) are not tied
        # to any timestep; pass them through with a null granular_date so
        # their constant values are preserved in the view.
        non_time_dep_path = output_path.with_suffix(".non_time_dep.parquet")
        logger.info(f"Writing non-time-dependent filtered rows to {non_time_dep_path}")
        granular_date_dtype = pl.read_parquet_schema(time_dep_path)["granular_date"]
        (
            self.dataframe.filter(pl.col("absolute_time_index").is_null()).with_columns(
                pl.lit(None).cast(granular_date_dtype).alias("granular_date")
            )
        ).sink_parquet(non_time_dep_path, compression="zstd", compression_level=3)

        logger.info(f"Merging filtered simulation table parts into {output_path}")
        pl.scan_parquet([time_dep_path, non_time_dep_path]).sink_parquet(
            output_path, compression="zstd", compression_level=3, row_group_size=64_000
        )
        time_dep_path.unlink()
        non_time_dep_path.unlink()
        logger.info(f"Filtered simulation table ready at {output_path}")
        return FilteredSimulationTable.load(output_path)


class FilteredSimulationTable:
    """
    Lazy representation of a filtered SIMULATION_TABLE CSV(Parquet in close future).
    Has all SIMULATION_TABLE columns plus granular_date from the calendar join.
    """

    def __init__(self, filtered_simulation_table_file: Path) -> None:
        """
        filtered_simulation_table_file: Path to the filtered simulation_table CSV
        """
        validate_file_format(filtered_simulation_table_file)
        self.file = filtered_simulation_table_file
        self.id = filtered_simulation_table_file.stem
        self._dataframe: pl.LazyFrame | None = None

    @property
    def dataframe(self) -> pl.LazyFrame:
        if self._dataframe is None:
            raise RuntimeError("FilteredSimulationTable is not loaded. Call FilteredSimulationTable.load(...) first.")
        return self._dataframe

    @classmethod
    def load(cls, filtered_simulation_table_file: Path) -> "FilteredSimulationTable":
        return cls(filtered_simulation_table_file).load_into_self()

    def load_into_self(self) -> "FilteredSimulationTable":
        logger.info(f"Loading filtered simulation table from {self.file}")
        self._dataframe = pl.scan_parquet(self.file)
        self._check_filtered_columns()
        logger.info(f"Filtered simulation table {self.id!r} loaded successfully")
        return self

    def _check_filtered_columns(self) -> None:
        logger.info(f"Validating filtered simulation table columns for {self.id!r}")
        actual = frozenset(self.dataframe.collect_schema().names())
        missing = FILTERED_SIMULATION_TABLE_COLUMNS - actual
        extra = actual - FILTERED_SIMULATION_TABLE_COLUMNS
        errors: list[str] = []
        if missing:
            errors.append(f"Missing columns: {missing}")
        if extra:
            errors.append(f"Unexpected columns: {extra}")
        if errors:
            raise ValueError(f"FilteredSimulationTable '{self.id}' has invalid columns: {'; '.join(errors)}")
        logger.info(f"Filtered simulation table {self.id!r} columns validated")
