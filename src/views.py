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

from src.catalog import Catalog, Metric, get_catalog_metric
import polars as pl

from src.catalog import Catalog, Metric, TermsOperator, TimeOperator
from src.library import ModelLibrary
from src.metrics import ViewConfig
from src.metrics_builder import MetricStructureBuilder
from src.simulation_table import SimulationTable
from src.system import InputSystem
from src.taxonomy import load_taxonomy

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
            raise FileNotFoundError(f"Catalogs directory {catalogs_path} is empty")  # 1 * constraint

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

    def _get_view_date_trunc_unit(self) -> str:
        """Map view_config.time_aggregation to Polars `dt.truncate` unit."""
        if self.view_config.time_aggregation is None or self.view_config.time_aggregation == TimeAggregation.HOURS:
            return "1h"
        raise NotImplementedError(f"Unsupported time aggregation: {self.view_config.time_aggregation}")

    def _get_terms_aggregation_expr(self, terms_operator: TermsOperator) -> pl.Expr:
        
        match terms_operator:
            case TermsOperator.SUM:
                return pl.col("value").sum()
            case TermsOperator.AVG:
                return pl.col("value").mean()
            case _:
                raise NotImplementedError(f"Unsupported terms operator: {terms_operator}")

    def _get_time_aggregation_expr(self, time_operator: TimeOperator) -> pl.Expr:
        match time_operator:
            case TimeOperator.SUM:
                return pl.col("granular_metric_value").sum()
            case TimeOperator.AVG:
                return pl.col("granular_metric_value").mean()
            case _:
                raise NotImplementedError(f"Unsupported time operator: {time_operator}")

    def execute(self) -> None:
        # # 1. Filter simulation table (spec: step 1)
        filtered_simulation_table = self.simulation_table.filter_simulation_table(
            self.view_config.load_calendar(), self.input_data_path / "simulation_table_filtered.csv"
        )
        _ = filtered_simulation_table  # to avoid copilot unnecessary warnings
        # # 2. Create metric structure table and perform SQL operations on it
        # # Metrics are grouped by catalog, in order to prevent multiple loading of the same catalog
        for catalog_id, metrics in self.view_config.catalog_to_metrics.items():

        # # date_trunc(view.aggregation.time, ABS_TIME_INDEX_TO_DATE(...)) (spec: step 2.c)
        view_date_trunc_unit = self._get_view_date_trunc_unit()

        # # 2. Loop over metrics (spec: step 2)
        # Aggregated content is appended across metrics.
        business_view_frames: list[pl.DataFrame] = []

        # # Metrics are grouped by catalog, in order to prevent multiple loading of the same catalog.
        for catalog_id, metrics in self.view_config.metrics_by_catalog.items():
            # # 2.1 Load catalog
            catalog: Catalog = self.view_config.load_catalog(catalog_id)
            # # 2.2 Iterate over all metrics for this catalog
            for metric_id in metrics:
                try:
                    metric: Metric = get_catalog_metric(catalog, metric_id)
                except ValueError:
                    continue  # keep processing other metrics

                # # 2.a {metric}: Building the METRIC_STRUCTURE_TABLE
                metric_structure_table = MetricStructureBuilder(
                    self.system,
                    catalog,
                    metric,
                    self.taxonomy,
                    self.model_library,
                ).build()

                # # 2.b {metric}: METRIC_STRUCTURE_TABLE joins + groupby (spec: step 2.b)
                metric_structure_lazy = metric_structure_table.dataframe.lazy()
                # Right join (SQL-like): simulation columns `component`/`output` match the structure columns
                # `component_id`/`output_id`. We also filter out null `value` to avoid aggregating non-matching rows.
                joined = filtered_simulation_table.dataframe.join(
                    metric_structure_lazy,
                    left_on=["component", "output"], # simulation table cols
                    right_on=["component_id", "output_id"], # metric structure table cols
                    how="right",
                ).filter(pl.col("value").is_not_null())

                terms_aggregation_expr = self._get_terms_aggregation_expr(metric.terms_operator)

                metric_view = (
                    joined.group_by(
                        [
                            "metric_id",
                            "metric_location",
                            "breakdown_properties", # breakdown_property from docs
                            "absolute_time_index",
                            "scenario_index", # scenario_id from docs
                        ]
                    )
                    .agg(terms_aggregation_expr.alias("granular_metric_value"))
                )

                # # 2.c {metric}: temporal aggregation (spec: step 2.c)
                time_aggregation_expr = self._get_time_aggregation_expr(metric.time_operator)

                metric_business_view = (
                    metric_view.with_columns(
                        pl.col("granular_date").dt.truncate(view_date_trunc_unit).alias("view_date") # 14.32 -> 14:00 for example
                    )
                    .group_by(["metric_id", "metric_location", "breakdown_properties", "scenario_index", "view_date"])
                    .agg(time_aggregation_expr.alias("metric_value"))
                    .select(
                        [
                            "metric_id",
                            "metric_location",
                            "breakdown_properties",
                            "view_date",
                            "scenario_index",
                            "metric_value",
                        ]
                    )
                    .rename({"breakdown_properties": "breakdown_property", "scenario_index": "scenario"})
                )

                business_view_frames.append(metric_business_view.collect(engine="streaming"))

        output_path = self.input_data_path / f"business_view_{self.view_config.id}.csv"
        if business_view_frames:
            business_view = pl.concat(business_view_frames, how="vertical_relaxed")
        else:
            business_view = pl.DataFrame(
                schema={
                    "metric_id": pl.Utf8,
                    "metric_location": pl.Utf8,
                    "breakdown_property": pl.Utf8,
                    "view_date": pl.Datetime,
                    "scenario": pl.Int64,
                    "metric_value": pl.Float64,
                }
            )

        business_view.write_csv(output_path)
