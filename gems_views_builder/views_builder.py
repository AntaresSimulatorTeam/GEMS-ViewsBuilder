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

import logging
from pathlib import Path

import polars as pl

from gems_views_builder.aggregator import Aggregator
from gems_views_builder.common import clean_filtered_simulation_table, clean_intermediate_metric
from gems_views_builder.input.catalog import Catalog, Metric
from gems_views_builder.input.input_data import InputData
from gems_views_builder.metrics_builder import MetricStructureBuilder
from gems_views_builder.writer import Writer

"""
# ViewConfig -> representation of the view_config.yml file and it references the catalogs and calendar
# System -> representation of the system.yml file
# Taxonomy -> representation of the taxonomy.yml file
"""


class ViewBuilder:
    def __init__(
        self,
        input_data: InputData,
    ) -> None:
        self.input_data = input_data
        self.aggregator = Aggregator(self.input_data.input_data_path)
        self.writer = Writer(self.input_data.input_data_path)

    def create_intermediate_dir(self) -> Path:
        intermediates_dir = self.input_data.input_data_path / "views" / "intermediate"
        intermediates_dir.mkdir(parents=True, exist_ok=True)
        return intermediates_dir

    def build(self) -> None:
        intermediates_dir = self.create_intermediate_dir()
        filtered_simulation_table_path = intermediates_dir / "simulation_table_filtered.parquet"

        # # 1. Filter simulation table (written to disk)

        self.input_data.simulation_table.filter_simulation_table(
            self.input_data.view_config.load_calendar(), filtered_simulation_table_path
        )

        parquet_files_to_process = []

        # # 2. Metrics are grouped by catalog (preloaded and validated in Loader)
        for catalog_id, metrics in self.input_data.view_config.catalog_to_metrics.items():
            # # 2.1 Load catalog
            catalog: Catalog = self.input_data.catalogs[catalog_id]
            # # 2.2 Iterate over all metrics for this catalog
            for metric_id in metrics:
                try:
                    metric: Metric = catalog.get_metric(metric_id)
                except ValueError:
                    logging.info(f"[{metric_id}] Metric not found in catalog '{catalog_id}' — skipping")
                    continue  # # We should decide do we want to break process fully or continue without the current metric

                # # 2.3 Build metric structure table, persist to disk, then re-open lazily
                metric_structure_table = MetricStructureBuilder(
                    self.input_data.system,
                    catalog,
                    metric,
                    self.input_data.taxonomy,
                    self.input_data.library,
                ).build()

                metric_structure_path = self.writer.write_metric_structure_table(
                    metric_structure_table.dataframe, metric.id
                )

                filtered_simulation_table_lazy = pl.scan_parquet(filtered_simulation_table_path)
                metric_structure_lazy = pl.scan_parquet(metric_structure_path)

                # # type(joined dataframe) == Lazy array
                # # no real data(in memory/disk) just query exectuion plan on scanned data
                # # we will perform additional query inside
                # logging.info(f"[{metric_id}] Joining filtered simulation table with metric structure")
                joined_dataframe = filtered_simulation_table_lazy.join(
                    metric_structure_lazy,
                    on=["component", "output"],
                    how="right",
                )

                metric_view_parquet_path = self.aggregator.aggregate_metric_terms(
                    joined_dataframe=joined_dataframe,
                    metric_term_operator=metric.terms_operator,
                    metric_id=metric.id,
                )
                temp_metric_view = self.aggregator.aggregate_metric_temporally(
                    metric_view_parquet_path=metric_view_parquet_path,
                    metric_time_operator=metric.time_operator,
                    metric_id=metric.id,
                )

                parquet_files_to_process.append(temp_metric_view)
                clean_intermediate_metric(metric_view_parquet_path, metric_structure_path)

        clean_filtered_simulation_table(filtered_simulation_table_path)
        self.writer.merge_results(parquet_files_to_process)
