# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path

from gems_views_builder.input_paths import InputPaths

YAML_SUFFIX = ".yml"
CSV_SUFFIX = ".csv"
SIMULATION_TABLE_SUFFIXES = {".parquet", ".csv"}


@dataclass
class InputPathsValidator:
    """
    Validates InputPaths shapes (extensions / expected contents).

    Existence of directories and files is checked earlier (CLI).
    This layer checks that paths look like the expected input kinds.
    """

    input_paths: InputPaths

    def _check_system_file(self) -> None:
        require_suffix(self.input_paths.system, {YAML_SUFFIX}, "System file")

    def _check_taxonomy_file(self) -> None:
        require_suffix(self.input_paths.taxonomy, {YAML_SUFFIX}, "Taxonomy file")

    def _check_calendar_file(self) -> None:
        require_suffix(self.input_paths.calendar, {CSV_SUFFIX}, "Calendar file")

    def _check_view_configs_files(self) -> None:
        for view_config in self.input_paths.view_configs:
            require_suffix(view_config, {YAML_SUFFIX}, "View config file")

    def _check_simulation_table_files(self) -> None:
        if not self.input_paths.simulation_tables:
            raise ValueError("Simulation table files are required")

        files_extensions = set()
        for path in self.input_paths.simulation_tables:
            require_suffix(path, SIMULATION_TABLE_SUFFIXES, "Simulation table")
            files_extensions.add(path.suffix.lower())

        if len(files_extensions) > 1:
            raise ValueError(f"Simulation table files must have the same extension, got: {', '.join(files_extensions)}")

    def validate(self) -> None:
        logging.info("Starting input paths validation")
        self._check_system_file()
        self._check_taxonomy_file()
        self._check_calendar_file()
        self._check_view_configs_files()
        self._check_simulation_table_files()
        logging.info("Input paths validation completed successfully")


def require_suffix(path: Path, allowed: set[str], label: str) -> None:
    if path.suffix.lower() not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{label} must have extension {expected}, got: {path}")
