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

from pathlib import Path

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


class ViewBuilder:
    def __init__(
        self,
        input_data_path: Path,
    ) -> None:
        self._check_input_data_structure(input_data_path)
        self.system = self._load_system(input_data_path)
        self.taxonomy = load_taxonomy(input_data_path / "taxonomy.yml")
        self.view_config = ViewConfig(input_data_path / "view_config.yml")
        simulation_table_candidates = sorted(input_data_path.glob("simulation_table*.parquet"))
        simulation_table_path = next((p for p in simulation_table_candidates if "filtered" not in p.stem), None)
        if simulation_table_path is None:
            raise FileNotFoundError(f"Required file starting with 'simulation_table' not found in {input_data_path}")
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
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")  # 1 * constraint

        exact_files = ["taxonomy.yml", "view_config.yml"]
        for filename in exact_files:
            if not (input_data_path / filename).is_file():
                raise FileNotFoundError(f"Required file '{filename}' not found in {input_data_path}")

        prefix_files = {"system": ".yml", "calendar": ".csv", "simulation_table": ".parquet"}
        for prefix, expected_suffix in prefix_files.items():
            match = next(input_data_path.glob(f"{prefix}*"), None)
            if match is None:
                raise FileNotFoundError(f"Required file starting with '{prefix}' not found in {input_data_path}")
            if match.suffix != expected_suffix:
                raise ValueError(f"File '{match.name}' starting with '{prefix}' must be a '{expected_suffix}' file")

    def _load_system(self, input_data_path: Path) -> InputSystem:
        system_path = next(input_data_path.glob("system*"))
        return InputSystem.from_file(system_path)

    def _build_metric_view(self, joined_dataframe: pl.LazyFrame, metric: Metric) -> Path:
        value_agg = (
            pl.col("value").sum() if metric.terms_operator == TermsOperator.SUM else pl.col("value").mean()
        )
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
                    pl.first("granular_date").alias("granular_date"),
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
        out_path = out_dir / f"{metric.id}.parquet"
        metric_view.sink_parquet(out_path)
        return out_path

    def _build_view(self, metric_view_parquet_path: Path, metric: Metric) -> Path:
        metric_view = pl.scan_parquet(metric_view_parquet_path)
        time_agg = (
            pl.col("granular_metric_value").sum()
            if metric.time_operator == TimeOperator.SUM
            else pl.col("granular_metric_value").mean()
        ).alias("metric_value")
        view_date_expr = pl.col("granular_date").alias("view_date")
        business_view = (
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
        dataset_dir = self.input_data_path / "views" / "metric_business_view" / metric.id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        existing_parts = sorted(dataset_dir.glob("part-*.parquet"))
        next_part_idx = (int(existing_parts[-1].stem.split("-")[1]) + 1) if existing_parts else 0
        out_path = dataset_dir / f"part-{next_part_idx:05d}.parquet"
        business_view.sink_parquet(out_path)
        return out_path

    def execute(self, cleanup_intermediate: bool = False) -> None:
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
                metric_structure_table.dataframe.write_parquet(metric_structure_path) # # TO DO for benchmark: test behavior when using write_parquet and not sink_parquet since metric structure table won't be heavy datum
                                                                                      # # Apply sylvan suggestions for creation of new parquet file(meta data)

                filtered_lazy = pl.scan_parquet(filtered_simulation_table_path)
                metric_structure_lazy = pl.scan_parquet(metric_structure_path)

                joined_dataframe = filtered_lazy.join(
                    metric_structure_lazy,
                    left_on=["component", "output"],
                    right_on=["component_id", "output_id"],
                    how="right",
                )

                metric_view_parquet_path = self._build_metric_view(
                    joined_dataframe=joined_dataframe, metric=metric
                )
                view_parquet_path = self._build_view(
                    metric_view_parquet_path=metric_view_parquet_path, metric=metric
                )
                # # Open question do we want to keep small parquet files and then after everything to make one big parquet file 
                # # Parquet doens't support in place wiriting as csv(basic open file append at the end)
                # # We could proceed with csv but have that on mind we lose fast processing of result after
                # # In future integration with AntaREST we will need fast retrival of specific data from view(e.g. business view)
                parquet_files_to_process.append(view_parquet_path)
                if cleanup_intermediate:
                    # Safe cleanup: remove only intermediates produced by this run.
                    metric_view_parquet_path.unlink(missing_ok=True)
                    metric_structure_path.unlink(missing_ok=True)

        if cleanup_intermediate:
            filtered_simulation_table_path.unlink(missing_ok=True)