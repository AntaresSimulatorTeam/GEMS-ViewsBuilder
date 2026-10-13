# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass

from gems_views_builder.input.library import create_lib_from_yml
from gems_views_builder.input.load import (
    load_calendar,
    load_catalogs,
    load_simulation_tables,
    load_system,
    load_taxonomy,
    load_view_config,
    load_yml_libs,
)
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.input_paths import InputPaths


@dataclass
class Loader:
    input_paths: InputPaths

    def load(self) -> RawInputData:
        """Perform all input data I/O and return populated raw input data."""

        logging.info("Loading inputs from explicit input paths")
        view_config: ViewConfig = load_view_config(self.input_paths.view_config)
        yml_libs = load_yml_libs(self.input_paths.libraries_dir)
        raw_input_data = RawInputData(
            taxonomy=load_taxonomy(self.input_paths.taxonomy),
            view_config=view_config,
            libraries={yml_lib.id: create_lib_from_yml(yml_lib) for yml_lib in yml_libs},
            system=load_system(self.input_paths.system, yml_libs),
            simulation_tables=load_simulation_tables(self.input_paths.simulation_tables),
            calendar=load_calendar(self.input_paths.calendar),
            catalogs=load_catalogs(self.input_paths.catalogs_dir, view_config.catalog_ids),
        )

        logging.info("All inputs loaded successfully")
        return raw_input_data
