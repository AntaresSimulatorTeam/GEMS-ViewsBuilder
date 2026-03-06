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

from dataclasses import dataclass

import polars as pl

# Columns of the SIMULATION_TABLE (spec section 1.5):
# simulation_id       (str)   – identifies the simulation
# block_id            (str)   – identifies the timeblock in the simulation
# component_id        (str)   – identifies the component
# output_id           (str)   – variable, port_field, or extra-output of the component
# absolute_time_index (int | None) – None if output is not time-dependent
# block_time_index    (int | None) – time index within the block; None if not time-dependent
# scenario_index      (int | None) – None if output is not scenario-dependent
# value               (float) – value of output_id at (absolute_time_index, scenario_index)
SIMULATION_TABLE_COLUMNS: frozenset[str] = frozenset(
    {
        "simulation_id",
        "block_id",
        "component_id",
        "output_id",
        "absolute_time_index",
        "block_time_index",
        "scenario_index",
        "value",
    }
)


@dataclass
class SimulationTable:
    """
    In memory representation of the SIMULATION_TABLE
    Expected columns: see SIMULATION_TABLE_COLUMNS.
    """

    id: str
    dataframe: pl.DataFrame

    def __post_init__(self) -> None:
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
