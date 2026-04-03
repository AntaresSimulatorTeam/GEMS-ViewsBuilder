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
    if simulation_table_file.suffix.lower() != ".parquet":
        raise ValueError(f"Simulation table file '{simulation_table_file}' is not a parquet file")


class SimulationTable:
    """
    Lazy representation of the SIMULATION_TABLE CSV.
    Expected columns: see SIMULATION_TABLE_COLUMNS.
    """

    def __init__(self, simulation_table_file: Path) -> None:
        """
        simulation_table_file: Path to the simulation_table.parquet file
        """
        validate_file_format(simulation_table_file)
        self.id = simulation_table_file.stem
        self.dataframe = pl.scan_parquet(simulation_table_file)
        self._check_simulation_table_columns()

    def _check_simulation_table_columns(self) -> None:
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

    def filter_simulation_table(self, calendar: Calendar, output_path: Path) -> "FilteredSimulationTable":
        """
        Filter the simulation table based on the calendar and write the result to output_path.
        Returns a FilteredSimulationTable with additional granular_date column from the calendar.
        """
        # Build a lazy pipeline, actual execution happens on sink.
        filtered_lazy = (
            self.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
            .filter(pl.col("block") == pl.col("block_right"))
            .drop("block_right")
        )
        filtered_lazy.sink_parquet(
            output_path,
            compression="zstd",
            compression_level=3,
            row_group_size=64_000,
        )
        return FilteredSimulationTable(output_path)


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
        self.id = filtered_simulation_table_file.stem
        self.dataframe = pl.scan_parquet(filtered_simulation_table_file)
        self._check_filtered_columns()

    def _check_filtered_columns(self) -> None:
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
