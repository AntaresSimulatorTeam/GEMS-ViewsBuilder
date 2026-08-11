# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path

from gems_views_builder.input_layout import InputLayout

YAML_SUFFIX = ".yml"
CSV_SUFFIX = ".csv"
SIMULATION_TABLE_SUFFIXES = {".parquet", ".csv"}


@dataclass
class InputLayoutValidator:
    """
    Validates InputLayout path shapes (extensions / expected contents).

    Existence of directories and files is checked earlier (CLI).
    This layer checks that paths look like the expected input kinds.
    """

    input_layout: InputLayout

    def _check_lib_dir(self) -> None:
        """Strictly reject any entry in the libraries directory that is not a .yml file."""
        libraries_dir = self.input_layout.libraries_dir
        logging.info(f"Validating model libraries directory {libraries_dir}")
        unexpected = [
            path.name for path in libraries_dir.iterdir() if not (path.is_file() and path.suffix.lower() == YAML_SUFFIX)
        ]
        if unexpected:
            raise ValueError(
                f"Model libraries directory {libraries_dir} contains non-.yml entries: {', '.join(unexpected)}"
            )

    def _check_catalogs_dir(self) -> None:
        """Strictly reject any entry in the catalogs directory that is not a .yml file."""
        catalogs_dir = self.input_layout.catalogs_dir
        logging.info(f"Validating catalogs directory {catalogs_dir}")
        unexpected = [
            path.name for path in catalogs_dir.iterdir() if not (path.is_file() and path.suffix.lower() == YAML_SUFFIX)
        ]
        if unexpected:
            raise ValueError(f"Catalogs directory {catalogs_dir} contains non-.yml entries: {', '.join(unexpected)}")

    def _check_sys_file(self) -> None:
        require_suffix(self.input_layout.system, {YAML_SUFFIX}, "System file")

    def _check_tax_file(self) -> None:
        require_suffix(self.input_layout.taxonomy, {YAML_SUFFIX}, "Taxonomy file")

    def _check_cal_file(self) -> None:
        require_suffix(self.input_layout.calendar, {CSV_SUFFIX}, "Calendar file")

    def _check_vc_file(self) -> None:
        require_suffix(self.input_layout.view_config, {YAML_SUFFIX}, "View config file")

    def _check_st_file(self) -> None:
        require_suffix(
            self.input_layout.simulation_table,
            SIMULATION_TABLE_SUFFIXES,
            "Simulation table",
        )

    def validate(self) -> None:
        logging.info("Starting input layout validation")
        self._check_lib_dir()
        self._check_catalogs_dir()
        self._check_sys_file()
        self._check_tax_file()
        self._check_cal_file()
        self._check_vc_file()
        self._check_st_file()
        logging.info("Input layout validation completed successfully")


def require_suffix(path: Path, allowed: set[str], label: str) -> None:
    if path.suffix.lower() not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{label} must have extension {expected}, got: {path}")
