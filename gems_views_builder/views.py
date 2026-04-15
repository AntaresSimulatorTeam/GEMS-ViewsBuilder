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

"""ViewBuilder."""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from gems_views_builder.catalog import Catalog, Metric, get_catalog_metric
from gems_views_builder.engines.base import BackendName, DataEngine, make_engine
from gems_views_builder.library import ModelLibrary
from gems_views_builder.metrics import ViewConfig
from gems_views_builder.metrics_builder import MetricStructureBuilder
from gems_views_builder.simulation_table import SimulationTable
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import load_taxonomy

"""
# ViewConfig -> representation of the view_config.yml file and it references the catalogs and calendar
# System -> representation of the system.yml file
# Taxonomy -> representation of the taxonomy.yml file
"""
EXACT_FILES = ["taxonomy.yml", "view_config.yml", "library.yml", "system.yml"]
PREFIX_FILES = {"calendar": ".csv", "simulation_table": ".parquet"}


class ViewBuilder:
    def __init__(
        self,
        input_data_path: Path,
        backend: BackendName = "polars",
    ) -> None:
        self.input_data_path = input_data_path
        self.engine: DataEngine = make_engine(backend)
        # If this function raises an error, the builder will not be able to build the views.
        self._check_input_data_structure()
        #
        self.system = self._load_system()
        self.taxonomy = load_taxonomy(self.input_data_path / "taxonomy.yml")
        self.view_config = ViewConfig(self.input_data_path / "view_config.yml")
        self.simulation_table = SimulationTable(
            next(self.input_data_path.glob("simulation_table*.parquet"))
        )  # we could have only one simulation table at this phase
        self.model_library = ModelLibrary(
            self.input_data_path / "library.yml"
        )  # must be named like this for now; in future when we enable user to have more than one library we should decide the pattern to use
        self._part_counter = 0

    def _check_input_data_path(self) -> None:
        """
        # Check if input_data_path exists and is a directory.
        """
        if not self.input_data_path.is_dir():
            raise NotADirectoryError(f"Input data path {self.input_data_path} is not a directory")

    def _check_catalogs_directory(self) -> None:
        """
        # Check if catalogs directory exists and is a directory.
        # Check if catalogs directory is empty.
        """
        catalogs_path = self.input_data_path / "catalogs"
        if not catalogs_path.is_dir():
            raise NotADirectoryError(f"Catalogs directory {catalogs_path} not found or not a directory")
        if not any(catalogs_path.iterdir()):
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")  # 1 * constraint

    def _check_required_input_files(self) -> None:
        """
        # Check if there are exactly 6 required files.
        """
        files_counter: defaultdict[str, int] = defaultdict(int)
        # # Check names
        for filename in EXACT_FILES:
            if not (self.input_data_path / filename).is_file():
                raise FileNotFoundError(f"Required file '{filename}' not found in {self.input_data_path}")
            files_counter[filename] += 1

        for prefix, expected_suffix in PREFIX_FILES.items():
            match = next(self.input_data_path.glob(f"{prefix}*"), None)
            if match is None:
                raise FileNotFoundError(f"Required file starting with '{prefix}' not found in {self.input_data_path}")
            if match.suffix != expected_suffix:
                raise ValueError(f"File '{match.name}' starting with '{prefix}' must be a '{expected_suffix}' file")
            files_counter[match.name] += 1

        # # Check counter
        if sum(files_counter.values()) != len(EXACT_FILES) + len(PREFIX_FILES):
            raise ValueError(
                f"Expected {len(EXACT_FILES) + len(PREFIX_FILES)} files in {self.input_data_path}, found {len(files_counter)}"
            )

    def _check_input_data_structure(self) -> None:
        """
        Expected files:
        - taxonomy.yml
        - view_config.yml
        - library.yml
        - system.yml
        - simulation_table.parquet
        - calendar.csv
        - catalogs directory with 1 * catalogs without strict name convention for now
        """
        self._check_input_data_path()

        self._check_catalogs_directory()

        self._check_required_input_files()

    def _load_system(self) -> InputSystem:
        system_path = next(self.input_data_path.glob("system*"))
        return InputSystem.from_file(system_path)

    def build(self, cleanup_intermediate: bool = True) -> None:
        # 1. Filter simulation table (written to disk).
        intermediates_dir = self.input_data_path / "views" / "intermediate"
        intermediates_dir.mkdir(parents=True, exist_ok=True)
        filtered_simulation_table_path = intermediates_dir / "simulation_table_filtered.parquet"

        calendar = self.view_config.load_calendar()
        self.engine.filter_simulation_table(
            self.simulation_table.file_path,
            calendar.file_path,
            filtered_simulation_table_path,
        )

        parquet_files_to_process = []

        # 2. Metrics are grouped by catalog to prevent multiple loads of the same catalog.
        for catalog_id, metrics in self.view_config.catalog_to_metrics.items():
            # 2.1 Load catalog.
            catalog: Catalog = self.view_config.load_catalog(catalog_id)

            # 2.2 Iterate over all metrics for this catalog.
            for metric_id in metrics:
                try:
                    metric: Metric = get_catalog_metric(catalog, metric_id)
                except ValueError:
                    continue  # We should decide whether to break fully or continue with the next metric.

                # 2.3 Build metric structure rows, persist to disk via the engine.
                rows = MetricStructureBuilder(
                    self.system,
                    catalog,
                    metric,
                    self.taxonomy,
                    self.model_library,
                ).build_rows()

                metric_structure_dir = self.input_data_path / "views" / "metric_structure"
                metric_structure_dir.mkdir(parents=True, exist_ok=True)
                metric_structure_path = metric_structure_dir / f"{metric.id}.parquet"
                self.engine.write_metric_structure(rows, metric_structure_path)

                # 2.4 Aggregate metric terms (join + group_by).
                metric_view_dir = self.input_data_path / "views" / "metric_view"
                metric_view_dir.mkdir(parents=True, exist_ok=True)
                metric_view_path = metric_view_dir / f"{metric.id}.parquet"
                self.engine.aggregate_metric_terms(
                    filtered_simulation_table_path,
                    metric_structure_path,
                    metric.terms_operator,
                    metric_view_path,
                )

                # 2.5 Aggregate temporally.
                dataset_dir = self.input_data_path / "temporal_aggregation"
                dataset_dir.mkdir(parents=True, exist_ok=True)
                temp_path = dataset_dir / f"{metric.id}-{self._part_counter}.parquet"
                self._part_counter += 1
                self.engine.aggregate_metric_temporally(
                    metric_view_path,
                    metric.time_operator,
                    temp_path,
                )

                parquet_files_to_process.append(temp_path)
                if cleanup_intermediate:
                    # Safe cleanup: remove only intermediates produced by this run.
                    metric_view_path.unlink(missing_ok=True)
                    metric_structure_path.unlink(missing_ok=True)

        if cleanup_intermediate:
            filtered_simulation_table_path.unlink(missing_ok=True)

        if parquet_files_to_process:
            results_dir = self.input_data_path / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            out_path = results_dir / f"view{timestamp}.parquet"
            self.engine.consolidate(parquet_files_to_process, out_path)
            for path in parquet_files_to_process:
                path.unlink(missing_ok=True)
