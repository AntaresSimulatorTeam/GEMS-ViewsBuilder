# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass

from gems_views_builder.input.calendar import load_calendar
from gems_views_builder.input.catalog import load_catalogs
from gems_views_builder.input.library import create_lib_from_schema, load_library_schemas
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import load_simulation_table
from gems_views_builder.input.system import load_system
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig, load_view_config
from gems_views_builder.input_paths import InputPaths


@dataclass
class Loader:
    input_paths: InputPaths

    def load(self) -> RawInputData:
        """Perform all input data I/O and return populated raw input data."""

        logging.info("Loading inputs from explicit input paths")
        view_config: ViewConfig = load_view_config(self.input_paths.view_config)
        libs_schemas = load_library_schemas(self.input_paths.libraries_dir)
        raw_input_data = RawInputData(
            input_data_path=self.input_paths.view_config.parent,
            taxonomy=load_taxonomy(self.input_paths.taxonomy),
            view_config=view_config,
            libraries={lib_schema.id: create_lib_from_schema(lib_schema) for lib_schema in libs_schemas},
            system=load_system(self.input_paths.system, libs_schemas),
            simulation_table=load_simulation_table(self.input_paths.simulation_table),
            calendar=load_calendar(self.input_paths.calendar),
            catalogs=load_catalogs(self.input_paths.catalogs_dir, view_config.catalog_ids),
        )

        logging.info("All inputs loaded successfully")
        return raw_input_data
