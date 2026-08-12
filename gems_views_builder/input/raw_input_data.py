# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass, field
from pathlib import Path

from gems_views_builder.input.calendar import Calendar
from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.library import Library
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig


@dataclass
class RawInputData:
    """Study inputs as loaded from disk, before view-building transformations."""

    input_data_path: Path
    taxonomy: Taxonomy
    view_config: ViewConfig
    library: Library
    system: System
    simulation_table: SimulationTable
    calendar: Calendar
    catalogs: dict[str, Catalog] = field(default_factory=dict)
