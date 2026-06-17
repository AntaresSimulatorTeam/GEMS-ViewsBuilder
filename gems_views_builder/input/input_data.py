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

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.library import Library
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig


class InputData:
    def __init__(
        self,
        taxonomy: Taxonomy,
        view_config: ViewConfig,
        catalogs: dict[str, Catalog],
        simulation_table: SimulationTable,
        library: Library,
        system: System,
    ) -> None:
        self.taxonomy = taxonomy
        self.view_config = view_config
        self.catalogs = catalogs
        self.simulation_table = simulation_table
        self.library = library
        self.system = system
