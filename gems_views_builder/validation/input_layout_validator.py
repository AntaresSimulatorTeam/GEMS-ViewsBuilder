# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass

from gems_views_builder.input_layout import InputLayout


@dataclass
class InputLayoutValidator:
    """
    Validates the on-disk layout expected by GEMS-ViewsBuilder, rooted at the GVB input
    directory (``input_dir``):

    - input/model-libraries/ : exactly one library.yml file(currently)
    - input/system.yml
    - input/calendar.csv    : exactly one calendar file
    - input/catalogs/        : one or more catalog.yml files
    - input/taxonomy/        : exactly one taxonomy.yml file
    - input/view-configs/    : exactly one view_config.yml file
    - output/{simulation_id}/ (most recent by folder name) : exactly one simulation table file
    """

    input_layout: InputLayout

    def _check_input_dir(self) -> None:
        logging.info(f"Validating input directory {self.input_layout.input_dir}")
        if not self.input_layout.input_dir.is_dir():
            raise NotADirectoryError(f"Input directory {self.input_layout.input_dir} is not a directory")

    def _check_model_libraries(self) -> None:
        if not self.input_layout.model_libraries_path.is_file():
            raise FileNotFoundError(
                f"Required file 'model-libraries/library.yml' not found in {self.input_layout.input_dir}"
            )

    def _check_system_file(self) -> None:
        if not self.input_layout.system_file.is_file():
            raise FileNotFoundError(f"Required file 'system.yml' not found in {self.input_layout.input_dir}")

    def _check_catalogs_directory(self) -> None:
        catalogs_path = self.input_layout.catalogs_dir
        logging.info(f"Validating catalogs directory {catalogs_path}")
        if not catalogs_path.is_dir():
            raise NotADirectoryError(f"Catalogs directory {catalogs_path} not found or not a directory")
        if not any(catalogs_path.glob("*.yml")):
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} has no catalog .yml file")

    def _check_taxonomy_directory(self) -> None:
        if not self.input_layout.taxonomy_path.is_file():
            raise FileNotFoundError(f"Required file 'taxonomy/taxonomy.yml' not found in {self.input_layout.input_dir}")

    def _check_calendar_file(self) -> None:
        if not self.input_layout.calendar_path.is_file():
            raise FileNotFoundError(f"Required file 'calendar.csv' not found in {self.input_layout.input_dir}")

    def _check_view_configs_directory(self) -> None:
        if not self.input_layout.view_config_path.is_file():
            raise FileNotFoundError(
                f"Required file 'view-configs/view_config.yml' not found in {self.input_layout.input_dir}"
            )

    def _check_output_directory(self) -> None:
        try:
            path = self.input_layout.simulation_table_path
        except StopIteration:
            raise FileNotFoundError(
                f"Required file 'simulation_table.parquet' or 'simulation_table.csv' "
                f"not found in {self.input_layout.simulation_dir}"
            ) from None
        if not path.is_file() or path.suffix not in {".parquet", ".csv"}:
            raise FileNotFoundError(
                f"Required file 'simulation_table.parquet' or 'simulation_table.csv' "
                f"not found in {self.input_layout.simulation_dir}"
            )

    def validate(self) -> None:
        logging.info(f"Starting input layout validation for {self.input_layout.root_dir}")
        self._check_input_dir()
        self._check_model_libraries()
        self._check_system_file()
        self._check_catalogs_directory()
        self._check_taxonomy_directory()
        self._check_calendar_file()
        self._check_view_configs_directory()
        self._check_output_directory()
        logging.info(f"Input layout validation completed successfully for {self.input_layout.root_dir}")
