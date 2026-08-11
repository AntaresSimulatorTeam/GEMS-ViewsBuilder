# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

from gems_views_builder.input.calendar import load_calendar
from gems_views_builder.input.catalog import Catalog, load_catalogs
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import load_library, resolve_libraries
from gems_views_builder.input.simulation_table import (
    filter_simulation_table,
    load_simulation_table,
)
from gems_views_builder.input.system import load_system
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import ViewConfig, load_view_config


class Loader:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def load(self) -> InputData:
        """Perform all input data I/O and return populated input data."""

        logging.info(f"Loading inputs from {self.input_data_path}")
        view_config: ViewConfig = load_view_config(self.input_data_path / "view_config.yml")

        catalogs: dict[str, Catalog] = load_catalogs(self.input_data_path, view_config.catalog_ids)
        view_config.fetch_metrics(catalogs)

        simulation_table = load_simulation_table(next(self.input_data_path.glob("simulation_table*")))
        calendar = load_calendar(self.input_data_path, view_config.calendar_id)
        filtered_st = filter_simulation_table(simulation_table, calendar)

        library_path = self.input_data_path / "library.yml"
        input_data = InputData(
            input_data_path=self.input_data_path,
            taxonomy=load_taxonomy(self.input_data_path / "taxonomy.yml"),
            view_config=view_config,
            library=load_library(library_path),
            system=load_system(self.input_data_path, resolve_libraries(library_path)),
            filtered_st=filtered_st,
        )

        logging.info("All inputs loaded successfully")
        return input_data
