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

"""InputGemsBusinessView (spec views.py)."""

from pathlib import Path

from gems.study.parsing import InputSystem, parse_yaml_components  # type: ignore[import-untyped]

from src.calendar import Calendar
from src.catalog import Catalog
from src.metrics import BusinessViewConfig
from src.simulation_table import SimulationTable
from src.taxonomy import Taxonomy


class InputGemsBusinessView:
    def __init__(
        self,
        input_data_path: Path,
    ) -> None:
        self._check_input_data_structure(input_data_path)
        self.simulation_table = SimulationTable(next(input_data_path.glob("simulation_table*")))
        self.calendar = Calendar(next(input_data_path.glob("calendar*")))
        self.system = self._load_system(input_data_path)
        self.taxonomy = Taxonomy(input_data_path / "taxonomy.yml")
        self.business_view_config = BusinessViewConfig(input_data_path / "business_view_config.yml")
        self.catalogs: list[Catalog] = [
            Catalog(input_data_path / "catalogs" / f"{catalog_id}.yml")
            for catalog_id in self.business_view_config.catalog_ids
        ]

    def _check_input_data_structure(self, input_data_path: Path) -> None:
        if not input_data_path.is_dir():
            raise NotADirectoryError(f"Input data path {input_data_path} is not a directory")

        catalogs_path = input_data_path / "catalogs"
        if not catalogs_path.is_dir():
            raise NotADirectoryError(f"Catalogs directory {catalogs_path} not found or not a directory")
        if not any(catalogs_path.iterdir()):
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")

        exact_files = ["taxonomy.yml", "business_view_config.yml"]
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

    def build_view(self) -> None:
        raise NotImplementedError()

    def _load_system(self, input_data_path: Path) -> InputSystem:
        system_path = next(input_data_path.glob("system*"))
        with open(system_path) as f:
            return parse_yaml_components(f)
