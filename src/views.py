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

"""MetricStructureBuilder, ViewBuilder, View (spec views.py)."""

from pathlib import Path

from src.catalog import Catalog, Metric
from src.input_system import InputSystem
from src.metrics import MetricStructureBuilder, ViewConfig
from src.model_library import ModelLibrary
from src.simulation_table import SimulationTable
from src.taxonomy import Taxonomy

"""
# ViewConfig -> representation of the view_config.yml file and it references the catalogs and calendar
# System -> representation of the system.yml file
# Taxonomy -> representation of the taxonomy.yml file
"""


class ViewBuilder:
    def __init__(
        self,
        input_data_path: Path,
    ) -> None:
        self._check_input_data_structure(input_data_path)
        self.system = self._load_system(input_data_path)
        self.taxonomy = Taxonomy(input_data_path / "taxonomy.yml")
        self.view_config = ViewConfig(input_data_path / "view_config.yml")
        simulation_table_path = next(input_data_path.glob("simulation_table*"))
        self.simulation_table = SimulationTable(simulation_table_path)
        self.model_library = ModelLibrary(input_data_path / "pypsa_models.yml")
        self.input_data_path = input_data_path

    def _check_input_data_structure(self, input_data_path: Path) -> None:
        if not input_data_path.is_dir():
            raise NotADirectoryError(f"Input data path {input_data_path} is not a directory")

        catalogs_path = input_data_path / "catalogs"
        if not catalogs_path.is_dir():
            raise NotADirectoryError(f"Catalogs directory {catalogs_path} not found or not a directory")
        if not any(catalogs_path.iterdir()):
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")

        exact_files = ["taxonomy.yml", "view_config.yml"]
        for filename in exact_files:
            if not (input_data_path / filename).is_file():
                raise FileNotFoundError(f"Required file '{filename}' not found in {input_data_path}")

        prefix_files = {"system": ".yml", "calendar": ".csv", "simulation_table": ".csv"}
        for prefix, expected_suffix in prefix_files.items():
            match = next(input_data_path.glob(f"{prefix}*"), None)
            if match is None:
                raise FileNotFoundError(f"Required file starting with '{prefix}' not found in {input_data_path}")
            if match.suffix != expected_suffix:
                raise ValueError(f"File '{match.name}' starting with '{prefix}' must be a '{expected_suffix}' file")

    def _load_system(self, input_data_path: Path) -> InputSystem:
        system_path = next(input_data_path.glob("system*"))
        return InputSystem.from_file(system_path)

    def execute(self) -> None:
        # # 1. Filter simulation table
        filtered_simulation_table = self.simulation_table.filter_simulation_table(  # noqa: F841
            self.calendar, self.input_data_path / "simulation_table_filtered.csv"
        )
        print(filtered_simulation_table)  # to avoid copilot unnecessary warnings
        # # 2. Create metric structure table
        # # Metrics are grouped by catalog, in order to prevent multiple loading of the same catalog
        for catalog_id, metrics in self.view_config.metrics.items():
            # # 2.1 Load catalog
            catalog: Catalog = self.view_config._load_current_catalog(catalog_id)
            # # 2.2 Iterate over all metrics for this catalog
            for metric_id in metrics:
                try:
                    metric: Metric = catalog.get_metric_by_id(metric_id)
                except ValueError:
                    continue  # # We should decide do we want to break process fully or continue with the next metric

                # # 2.3 Build metric structure table
                MetricStructureBuilder(
                    self.system,
                    catalog,
                    metric,
                    self.taxonomy,
                    self.model_library,
                    self.input_data_path / f"metric_structure_table_{metric_id}.csv",
                ).build_table()
                # # Right join
                # # Group by
                # # Group by

            # Delete metric structure table after use
            (self.input_data_path / f"metric_structure_table_{metric_id}.csv").unlink()
