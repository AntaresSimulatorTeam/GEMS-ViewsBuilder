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

from gems_views_builder.input.catalog import load_catalogs
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import load_library
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig


class Loader:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    @classmethod
    def load(cls, input_data_path: Path) -> InputData:
        """Create a loader and perform all input data I/O."""
        return cls(input_data_path).load_input_data()

    def load_input_data(self) -> InputData:
        """Perform all input data I/O and return populated input data."""
        logging.info(f"Loading inputs from {self.input_data_path}")
        view_config = ViewConfig.load(self.input_data_path / "view_config.yml")
        input_data = InputData(
            taxonomy=load_taxonomy(self.input_data_path / "taxonomy.yml"),
            view_config=view_config,
            catalogs=load_catalogs(self.input_data_path, view_config.catalog_ids),
            simulation_table=SimulationTable.load(next(self.input_data_path.glob("simulation_table*.parquet"))),
            library=load_library(self.input_data_path / "library.yml"),
            system=System.from_file(self.input_data_path / "system.yml"),
        )
        logging.info("All inputs loaded successfully")
        return input_data
