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
from typing import Optional

import polars as pl

from src.calendar import Calendar

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


class SimulationTable:
    """
    In memory representation of the SIMULATION_TABLE
    Expected columns: see SIMULATION_TABLE_COLUMNS.
    """

    def __init__(self, simulation_table_file: Path) -> None:
        """
        simulation_table_file: Path to the simulation_table.csv file
        """
        self.id = simulation_table_file.stem
        self.dataframe = pl.read_csv(
            simulation_table_file,
            null_values=["None"],
        )
        self._check_simulation_table_columns()

    def _check_simulation_table_columns(self) -> None:
        actual = frozenset(self.dataframe.columns)
        missing = SIMULATION_TABLE_COLUMNS - actual
        extra = actual - SIMULATION_TABLE_COLUMNS
        errors: list[str] = []
        if missing:
            errors.append(f"Missing columns: {missing}")
        if extra:
            errors.append(f"Unexpected columns: {extra}")
        if errors:
            raise ValueError(f"SimulationTable '{self.id}' has invalid columns: {'; '.join(errors)}")

    def filter_simulation_table(self, calendar: Calendar, output_path: Optional[Path] = None) -> pl.DataFrame:
        """
        Filter the simulation table based on the calendar.
        If output_path is provided, save the filtered simulation table to the output path.
        """
        filtered_table = self.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        # right is appended by the join(polars)
        # drop block_right in order to save memory
        filtered_table = filtered_table.filter(pl.col("block") == pl.col("block_right")).drop("block_right")
        if output_path is not None:
            filtered_table.write_csv(output_path)
        return filtered_table
