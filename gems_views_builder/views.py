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
from typing import Literal

import polars as pl

from gems_views_builder.catalog import Catalog, Metric, TermsOperator, TimeOperator, get_catalog_metric
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

_ParquetCompression = Literal["lz4", "uncompressed", "snappy", "gzip", "brotli", "zstd"]
_PARQUET_COMPRESSION: _ParquetCompression = "zstd"
_PARQUET_COMPRESSION_LEVEL = 3
_PARQUET_ROW_GROUP_SIZE = 64_000


class ViewBuilder:
    def __init__(
        self,
        input_data_path: Path,
    ) -> None:
        self.input_data_path = input_data_path
        # # If this function raise an error, the builder will not be able to build the views.
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
        )  # # must be named like this for now, in future when we enable user to have more than one libraries we should decide pattern to use
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

    def _aggregate_metric_terms(
        self, joined_dataframe: pl.LazyFrame, metric_term_operator: TermsOperator, metric_id: str
    ) -> Path:
        """
        2b step from POC
        2b-1 Right join TIME_FILTERED_SIMULATION_TABLE with METRIC_STRUCTURE_TABLE on component and output
        2b-2 Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        value_agg = pl.col("value").sum() if metric_term_operator == TermsOperator.SUM else pl.col("value").mean()
        metric_view = (
            joined_dataframe.with_columns(pl.col("scenario_index").alias("scenario"))
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "absolute_time_index",
                    "scenario",
                ]
            )
            .agg(
                [
                    value_agg.alias("granular_metric_value"),
                    pl.first("granular_date"),  # # take a first row of group whatever it is
                ]
            )
            .select(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "absolute_time_index",
                    "scenario",
                    "granular_metric_value",
                    "granular_date",
                ]
            )
        )
        out_dir = self.input_data_path / "views" / "metric_view"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{metric_id}.parquet"
        metric_view.sink_parquet(
            out_path,
            compression=_PARQUET_COMPRESSION,
            compression_level=_PARQUET_COMPRESSION_LEVEL,
            row_group_size=_PARQUET_ROW_GROUP_SIZE,
        )
        return out_path

    def _aggregate_metric_temporally(
        self, metric_view_parquet_path: Path, metric_time_operator: TimeOperator, metric_id: str
    ) -> Path:
        metric_view = pl.scan_parquet(metric_view_parquet_path)
        time_agg = (
            pl.col("granular_metric_value").sum()
            if metric_time_operator == TimeOperator.SUM
            else pl.col("granular_metric_value").mean()
        ).alias("metric_value")
        view_date_expr = pl.col("granular_date").alias("view_date")
        view = (
            metric_view.with_columns(view_date_expr)
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "scenario",
                    "view_date",
                ]
            )
            .agg(time_agg)
            .select(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "view_date",
                    "scenario",
                    "metric_value",
                ]
            )
        )
        # Business view is meant to be created once, then appended to on future runs.
        # We implement this by writing a new parquet "part" file each time.
        dataset_dir = self.input_data_path / "temporal_aggregation"
        dataset_dir.mkdir(parents=True, exist_ok=True)

        out_path = dataset_dir / f"{metric_id}-{self._part_counter}.parquet"
        self._part_counter += 1
        view.sink_parquet(
            out_path,
            compression=_PARQUET_COMPRESSION,
            compression_level=_PARQUET_COMPRESSION_LEVEL,
            row_group_size=_PARQUET_ROW_GROUP_SIZE,
        )
        return out_path

    def _consolidate_results(self, chunk_paths: list[Path]) -> Path:
        results_dir = self.input_data_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = results_dir / f"view{timestamp}.parquet"
        pl.scan_parquet(chunk_paths).sink_parquet(
            out_path,
            compression=_PARQUET_COMPRESSION,
            compression_level=_PARQUET_COMPRESSION_LEVEL,
            row_group_size=_PARQUET_ROW_GROUP_SIZE,
        )
        for path in chunk_paths:
            path.unlink(missing_ok=True)
        return out_path

    def build(self, cleanup_intermediate: bool = False) -> None:
        # # 1. Filter simulation table (written to disk)
        filtered_simulation_table_path = self.input_data_path / "simulation_table_filtered.parquet"
        self.simulation_table.filter_simulation_table(self.view_config.load_calendar(), filtered_simulation_table_path)
        parquet_files_to_process = []
        # # 2. Metrics are grouped by catalog, in order to prevent multiple loading of the same catalog
        for catalog_id, metrics in self.view_config.catalog_to_metrics.items():
            # # 2.1 Load catalog
            catalog: Catalog = self.view_config.load_catalog(catalog_id)
            # # 2.2 Iterate over all metrics for this catalog
            for metric_id in metrics:
                try:
                    metric: Metric = get_catalog_metric(catalog, metric_id)
                except ValueError:
                    continue  # # We should decide do we want to break process fully or continue with the next metric

                # 2.3 Build metric structure table, persist to disk, then re-open lazily
                metric_structure_table = MetricStructureBuilder(
                    self.system,
                    catalog,
                    metric,
                    self.taxonomy,
                    self.model_library,
                ).build()
                metric_structure_dir = self.input_data_path / "views" / "metric_structure"
                metric_structure_dir.mkdir(parents=True, exist_ok=True)
                metric_structure_path = metric_structure_dir / f"{metric.id}.parquet"
                metric_structure_table.dataframe.write_parquet(
                    metric_structure_path,
                    compression=_PARQUET_COMPRESSION,
                    compression_level=_PARQUET_COMPRESSION_LEVEL,
                    row_group_size=_PARQUET_ROW_GROUP_SIZE,
                    use_pyarrow=True,
                    pyarrow_options={"data_page_version": "2.0"},
                )  # # TO DO for benchmark: test behavior when using write_parquet and not sink_parquet since metric structure table won't be heavy datum

                filtered_simulation_table_lazy = pl.scan_parquet(filtered_simulation_table_path)
                metric_structure_lazy = pl.scan_parquet(metric_structure_path)
                # pass this 2 to the aggregate metric terms and

                # # type(joined dataframe) == Lazy array
                # # no real data(in memory/disk) just query exectuion plan on scanned data
                # # we will perform additional query inside
                joined_dataframe = filtered_simulation_table_lazy.join(
                    metric_structure_lazy,
                    on=["component", "output"],
                    how="right",
                )

                metric_view_parquet_path = self._aggregate_metric_terms(
                    joined_dataframe=joined_dataframe, metric_term_operator=metric.terms_operator, metric_id=metric.id
                )
                temp_metric_view = self._aggregate_metric_temporally(
                    metric_view_parquet_path=metric_view_parquet_path,
                    metric_time_operator=metric.time_operator,
                    metric_id=metric.id,
                )

                parquet_files_to_process.append(temp_metric_view)
                if cleanup_intermediate:
                    # Safe cleanup: remove only intermediates produced by this run.
                    metric_view_parquet_path.unlink(missing_ok=True)
                    metric_structure_path.unlink(missing_ok=True)

        if cleanup_intermediate:
            filtered_simulation_table_path.unlink(missing_ok=True)

        if parquet_files_to_process:
            self._consolidate_results(parquet_files_to_process)
