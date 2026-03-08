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

"""MetricStructureBuilder, BusinessViewBuilder, BusinessView (spec views.py)."""

from dataclasses import dataclass

import polars as pl
from gems.study.parsing import InputSystem  # type: ignore[import-untyped]

from src.calendar import Calendar
from src.location import LocationPorts
from src.metrics import BusinessViewConfig
from src.simulation_table import SimulationTable


class MetricStructureBuilder:
    """InputSystem from GemsPy. LIST_OF_COMPONENTS_IN_TAXONOMY_CATEGORY, LOCATING_FUNCTION, build_tables (spec 2.1)."""

    def __init__(self, system: InputSystem, view_configuration: BusinessViewConfig) -> None:
        self.system = system
        self.view_configuration = view_configuration

    def components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        raise NotImplementedError()

    def locating_function(self, component_id: str, location_ports: LocationPorts) -> str | tuple[str, ...]:
        raise NotImplementedError()

    def build_tables(self) -> dict[str, pl.DataFrame]:
        raise NotImplementedError()


class BusinessViewBuilder:
    """__init__(InputSystem, Calendar, BusinessViewConfig, SimulationTable). build_view()."""

    def __init__(
        self,
        system: InputSystem,
        calendar: Calendar,
        view_configuration: BusinessViewConfig,
        simulation_table: SimulationTable,
    ) -> None:
        self.system = system
        self.calendar = calendar
        self.view_configuration = view_configuration
        self.simulation_table = simulation_table

    def build_view(self) -> None:
        raise NotImplementedError()


@dataclass
class BusinessView:
    dataframe: pl.DataFrame
