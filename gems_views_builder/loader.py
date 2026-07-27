# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

from gems_views_builder.input.calendar import load_calendar
from gems_views_builder.input.catalog import load_catalogs
from gems_views_builder.input.library import load_library, resolve_libraries
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import load_simulation_table
from gems_views_builder.input.system import load_system
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig, load_view_config
from gems_views_builder.input_layout import InputLayout


class Loader:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path
        self.paths = InputLayout(input_data_path)

    def load(self) -> RawInputData:
        """Perform all input data I/O and return populated raw input data."""

        logging.info(f"Loading inputs from {self.input_data_path}")
        view_config: ViewConfig = load_view_config(self.paths.view_config_path)

        raw_input_data = RawInputData(
            input_data_path=self.input_data_path,
            taxonomy=load_taxonomy(self.paths.taxonomy_path),
            view_config=view_config,
            library=load_library(self.paths.model_libraries_path),
            system=load_system(self.paths.system_file, resolve_libraries(self.paths.model_libraries_path)),
            simulation_table=load_simulation_table(self.paths.simulation_table_path),
            calendar=load_calendar(self.paths.input_dir, view_config.calendar_id),
            catalogs=load_catalogs(self.paths.catalogs_dir, view_config.catalog_ids),
        )

        logging.info("All inputs loaded successfully")
        return raw_input_data
