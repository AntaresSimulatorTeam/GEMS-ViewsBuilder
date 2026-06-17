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
from gems_views_builder.common import log_file
from gems_views_builder.input.catalog import Catalog, Metric
from gems_views_builder.loader import Loader
from gems_views_builder.metrics_builder import MetricStructureBuilder
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.validation.study_layout_validator import StudyLayoutValidator
from gems_views_builder.writer import Writer

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
        self.input_data_path = input_data_path
        StudyLayoutValidator(self.input_data_path).validate()
        self.loader = Loader.load(self.input_data_path)
        # # Currently we support only one taxonomy per study
        validate_catalogs_against_taxonomy(self.loader.catalogs, self.loader.taxonomy)

        self.aggregator = Aggregator(self.input_data_path)
        self.writer = Writer(self.input_data_path)

    def create_intermediate_dir(self) -> Path:
        intermediates_dir = self.input_data_path / "views" / "intermediate"
        intermediates_dir.mkdir(parents=True, exist_ok=True)
        return intermediates_dir

    def build(self) -> None:
        logging.info(f"Pipeline log file initialized at {log_file}")
        logging.info(f"Starting pipeline for study at {self.input_data_path}")

        intermediates_dir = self.create_intermediate_dir()
        filtered_simulation_table_path = intermediates_dir / "simulation_table_filtered.parquet"

        # # 1. Filter simulation table (written to disk)
        logging.info("Step 1: Filtering simulation table by calendar")
        self.loader.simulation_table.filter_simulation_table(
            self.loader.view_config.load_calendar(), filtered_simulation_table_path
        )
        logging.info(f"Filtered simulation table written to {filtered_simulation_table_path}")

        parquet_files_to_process = []
        logging.info(
            f"Step 2: Processing {sum(len(m) for m in self.loader.view_config.catalog_to_metrics.values())} "
            f"metric(s) across {len(self.loader.view_config.catalog_to_metrics)} catalog(s)"
        )

        # # 2. Metrics are grouped by catalog (preloaded and validated in Loader)
        for catalog_id, metrics in self.loader.view_config.catalog_to_metrics.items():
            logging.info(f"Processing catalog '{catalog_id}' ({len(metrics)} metric(s))")
            # # 2.1 Load catalog
            catalog: Catalog = self.loader.catalogs[catalog_id]
            # # 2.2 Iterate over all metrics for this catalog
            for metric_id in metrics:
                logging.info(f"[{metric_id}] Processing metric")
                try:
                    metric: Metric = catalog.get_metric(metric_id)
                except ValueError:
                    logging.info(f"[{metric_id}] Metric not found in catalog '{catalog_id}' — skipping")
                    continue  # # We should decide do we want to break process fully or continue without the current metric

                # # 2.3 Build metric structure table, persist to disk, then re-open lazily
                metric_structure_table = MetricStructureBuilder(
                    self.loader.system,
                    catalog,
                    metric,
                    self.loader.taxonomy,
                    self.loader.library,
                ).build()

                metric_structure_path = self.writer.write_metric_structure_table(
                    metric_structure_table.dataframe, metric.id
                )

                filtered_simulation_table_lazy = pl.scan_parquet(filtered_simulation_table_path)
                metric_structure_lazy = pl.scan_parquet(metric_structure_path)

                # # type(joined dataframe) == Lazy array
                # # no real data(in memory/disk) just query exectuion plan on scanned data
                # # we will perform additional query inside
                logging.info(f"[{metric_id}] Joining filtered simulation table with metric structure")
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

                logging.info(f"[{metric_id}] Cleaning intermediate files")
                clean_intermediate_metric(metric_view_parquet_path, metric_structure_path)

        logging.info("Cleaning filtered simulation table")
        clean_filtered_simulation_table(filtered_simulation_table_path)

        logging.info("Step 3: Writing results")
        self.writer.merge_results(parquet_files_to_process)
        logging.info("Pipeline complete")


# # Utils functions for ViewBuilder class
# # They don't use any class attributes or methods, so they are not part of the class
# # Should I put that inside common.py file?
def clean_intermediate_metric(metric_view_parquet_path: Path, metric_structure_path: Path) -> None:
    metric_view_parquet_path.unlink(missing_ok=True)
    metric_structure_path.unlink(missing_ok=True)


def clean_filtered_simulation_table(filtered_simulation_table_path: Path) -> None:
    filtered_simulation_table_path.unlink(missing_ok=True)
