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

    def _check_libraries_directory(self) -> None:
        """Strictly reject any entry in the libraries directory that is not a .yml file."""
        libraries_dir = self.input_paths.libraries_dir
        logging.info(f"Validating model libraries directory {libraries_dir}")
        unexpected = [
            path.name for path in libraries_dir.iterdir() if not (path.is_file() and path.suffix.lower() == YAML_SUFFIX)
        ]
        if unexpected:
            raise ValueError(
                f"Model libraries directory {libraries_dir} contains non-.yml entries: {', '.join(unexpected)}"
            )

    def _check_catalogs_directory(self) -> None:
        """Strictly reject any entry in the catalogs directory that is not a .yml file."""
        catalogs_dir = self.input_paths.catalogs_dir
        logging.info(f"Validating catalogs directory {catalogs_dir}")
        unexpected = [
            path.name for path in catalogs_dir.iterdir() if not (path.is_file() and path.suffix.lower() == YAML_SUFFIX)
        ]
        if unexpected:
            raise ValueError(f"Catalogs directory {catalogs_dir} contains non-.yml entries: {', '.join(unexpected)}")

    def _check_system_file(self) -> None:
        require_suffix(self.input_paths.system, {YAML_SUFFIX}, "System file")

    def _check_taxonomy_file(self) -> None:
        require_suffix(self.input_paths.taxonomy, {YAML_SUFFIX}, "Taxonomy file")

    def _check_calendar_file(self) -> None:
        require_suffix(self.input_paths.calendar, {CSV_SUFFIX}, "Calendar file")

    def _check_view_config_file(self) -> None:
        require_suffix(self.input_paths.view_config, {YAML_SUFFIX}, "View config file")

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
        self._check_libraries_directory()
        self._check_catalogs_directory()
        self._check_system_file()
        self._check_taxonomy_file()
        self._check_calendar_file()
        self._check_view_config_file()
        self._check_simulation_table_files()
        logging.info("Input paths validation completed successfully")


def require_suffix(path: Path, allowed: set[str], label: str) -> None:
    if path.suffix.lower() not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{label} must have extension {expected}, got: {path}")
