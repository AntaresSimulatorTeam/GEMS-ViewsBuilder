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

<<<<<<< HEAD
from gems_views_builder.aggregator import Aggregator
from gems_views_builder.input.input_data import InputData
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_builder import build_metric_structure
from gems_views_builder.writer import MergedView, Writer
=======
import logging

from gems_views_builder.input.input_data import InputData
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.terms_aggregator import TermsAggregator
from gems_views_builder.time_aggregator import TimeAggregator
>>>>>>> origin/main


class ViewBuilder:
    def __init__(self, input_data: InputData) -> None:
<<<<<<< HEAD
        self.input_data = input_data
        self.writer = Writer(input_data.input_data_path)
        self.aggregator = Aggregator(input_data.input_data_path)

    def build(self) -> MergedView:
=======
        # # Input data of pipeline
        self.input_data = input_data
        # # Builder which is reusable over metrics
        self.metric_structure_table_builder = MetricStructureTableBuilder(
            self.input_data.system, self.input_data.library
        )
        # # Aggregator for step 2B
        self.terms_aggregator = TermsAggregator(self.input_data.filtered_st)
        # # Aggregator for step 2C
        self.time_aggregator = TimeAggregator()

    def build(self) -> list[MetricView]:
>>>>>>> origin/main
        metric_views: list[MetricView] = []
        for catalog_id, metric_ids in self.input_data.view_config.catalog_to_metrics.items():
            catalog = self.input_data.catalogs[catalog_id]
            for metric_id in metric_ids:
                try:
                    metric = catalog.get_metric(metric_id)
                except ValueError:
<<<<<<< HEAD
                    continue
                structure = build_metric_structure(
                    self.input_data.system,
                    metric,
                    self.input_data.library,
                    self.writer,
                )
                metric_views.append(self.aggregator.aggregate(self.input_data.filtered_st, structure, metric))
        merged = MergedView.merge_views(metric_views, self.writer)
        self.input_data.filtered_st.cleanup()
        return merged
=======
                    logging.warning(f"Metric {metric_id} not found in catalog {catalog_id}")
                    continue

                metric_structure_table = self.metric_structure_table_builder.build(metric)
                metric_view = self.terms_aggregator.run(metric_structure_table, metric)
                temporal_metric_view = self.time_aggregator.run(metric_view, metric)
                metric_views.append(temporal_metric_view)

        return metric_views
>>>>>>> origin/main
