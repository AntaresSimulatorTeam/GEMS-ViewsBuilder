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

from gems_views_builder.aggregator import Aggregator
from gems_views_builder.input.input_data import InputData
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_builder import build_metric_structure
from gems_views_builder.writer import MergedView, Writer


class ViewBuilder:
    def __init__(self, input_data: InputData) -> None:
        self.input_data = input_data
        self.writer = Writer(input_data.input_data_path)
        self.aggregator = Aggregator(input_data.input_data_path)

    def build(self) -> MergedView:
        metric_views: list[MetricView] = []
        for catalog_id, metric_ids in self.input_data.view_config.catalog_to_metrics.items():
            catalog = self.input_data.catalogs[catalog_id]
            for metric_id in metric_ids:
                try:
                    metric = catalog.get_metric(metric_id)
                except ValueError:
                    continue
                structure = build_metric_structure(
                    self.input_data.system,
                    metric,
                    self.input_data.library,
                    self.writer,
                    location_aggregation=self.input_data.view_config.location_aggregation,
                )
                metric_views.append(self.aggregator.aggregate(self.input_data.filtered_st, structure, metric))
        merged = MergedView.merge_views(metric_views, self.writer)
        self.input_data.filtered_st.cleanup()
        return merged
