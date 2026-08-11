# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass

from gems_views_builder.input.calendar import load_calendar
from gems_views_builder.input.catalog import load_catalogs
from gems_views_builder.input.library import load_library, resolve_libraries
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import load_simulation_table
from gems_views_builder.input.system import load_system
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig, load_view_config
from gems_views_builder.input_layout import InputLayout


@dataclass
class Loader:
    input_layout: InputLayout

    def load(self) -> RawInputData:
        """Perform all input data I/O and return populated raw input data."""

        logging.info("Loading inputs from explicit input layout paths")
        view_config: ViewConfig = load_view_config(self.input_layout.view_config)

        library_file = self.input_layout.library_file
        raw_input_data = RawInputData(
            input_data_path=self.input_layout.view_config.parent,
            taxonomy=load_taxonomy(self.input_layout.taxonomy),
            view_config=view_config,
            library=load_library(library_file),
            system=load_system(self.input_layout.system, resolve_libraries(library_file)),
            simulation_table=load_simulation_table(self.input_layout.simulation_table),
            calendar=load_calendar(self.input_layout.calendar),
            catalogs=load_catalogs(self.input_layout.catalogs_dir, view_config.catalog_ids),
        )

        logging.info("All inputs loaded successfully")
        return raw_input_data
