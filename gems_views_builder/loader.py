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

        logging.info(f"Loading inputs from {self.input_layout.input_dir}")
        view_config: ViewConfig = load_view_config(self.input_layout.view_config_path)

        raw_input_data = RawInputData(
            input_data_path=self.input_layout.root_dir,
            taxonomy=load_taxonomy(self.input_layout.taxonomy_path),
            view_config=view_config,
            library=load_library(self.input_layout.model_libraries_path),
            system=load_system(
                self.input_layout.system_file, resolve_libraries(self.input_layout.model_libraries_path)
            ),
            simulation_table=load_simulation_table(self.input_layout.simulation_table_path),
            calendar=load_calendar(self.input_layout.input_dir, view_config.calendar_id),
            catalogs=load_catalogs(self.input_layout.catalogs_dir, view_config.catalog_ids),
        )

        logging.info("All inputs loaded successfully")
        return raw_input_data
