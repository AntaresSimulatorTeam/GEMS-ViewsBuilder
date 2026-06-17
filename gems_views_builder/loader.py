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
from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.system import load_system
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig, load_view_config
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator


class Loader:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def load(self) -> InputData:
        """Perform all input data I/O and return populated input data."""

        # # Validate study layout before loading any input data
        StudyLayoutValidator(self.input_data_path).validate()

        logging.info(f"Loading inputs from {self.input_data_path}")
        view_config: ViewConfig = load_view_config(self.input_data_path / "view_config.yml")
        if view_config.calendar_id is None:
            raise ValueError(f"view_config.yml '{view_config.id}': no calendar configured in scope")

        input_data = InputData(
            input_data_path=self.input_data_path,
            taxonomy=load_taxonomy(self.input_data_path / "taxonomy.yml"),
            view_config=view_config,
            catalogs=load_catalogs(self.input_data_path, view_config.catalog_ids),
            simulation_table=SimulationTable.load(next(self.input_data_path.glob("simulation_table*.parquet"))),
            library=load_library(self.input_data_path / "library.yml"),
            system=load_system(self.input_data_path),
            calendar=load_calendar(self.input_data_path, view_config.calendar_id),
        )

        # # Check consistecy between catalog and taxonomy
        # # This is placeholder,some checks are done but it will be finished on suggested comments in dedicated PR
        # # Currently we support only one taxonomy per study
        validate_catalogs_against_taxonomy(input_data.catalogs, input_data.taxonomy)

        logging.info("All inputs loaded successfully")
        return input_data
