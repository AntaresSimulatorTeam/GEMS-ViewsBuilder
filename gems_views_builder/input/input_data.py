# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass, field
from pathlib import Path

from gems_views_builder.input.component import Component
from gems_views_builder.input.library import Library
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig


@dataclass
class InputData:
    input_data_path: Path
    taxonomy: Taxonomy
    view_config: ViewConfig
    library: Library
    system: System
    filtered_st: FilteredSimulationTable
    components: list[Component] = field(default_factory=list)
