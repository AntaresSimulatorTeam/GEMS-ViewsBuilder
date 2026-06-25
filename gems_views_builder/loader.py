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

import logging
from pathlib import Path

from gems_views_builder.input.calendar import load_calendar
from gems_views_builder.input.catalog import load_catalogs
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import load_library
from gems_views_builder.input.simulation_table import (
    filter_simulation_table,
    load_simulation_table,
)
from gems_views_builder.input.system import load_system
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig, load_view_config


class Loader:
    def __init__(self, input_data_path: Path, results_path: Path) -> None:
        self.input_data_path = input_data_path
        self.results_path = results_path

    def load(self) -> InputData:
        """Perform all input data I/O and return populated input data."""

        logging.info(f"Loading inputs from {self.input_data_path}")
        view_config: ViewConfig = load_view_config(self.input_data_path / "view_config.yml")

        simulation_table = load_simulation_table(next(self.input_data_path.glob("simulation_table*.parquet")))
        calendar = load_calendar(self.input_data_path, view_config.calendar_id)
        intermediates_dir = self.input_data_path / "views" / "intermediate"
        filtered_st = filter_simulation_table(simulation_table, calendar, intermediates_dir)

        input_data = InputData(
            input_data_path=self.input_data_path,
            taxonomy=load_taxonomy(self.input_data_path / "taxonomy.yml"),
            view_config=view_config,
            catalogs=load_catalogs(self.input_data_path, view_config.catalog_ids),
            library=load_library(self.input_data_path / "library.yml"),
            system=load_system(self.input_data_path),
            filtered_st=filtered_st,
            results_path=self.results_path,
        )

        logging.info("All inputs loaded successfully")
        return input_data
