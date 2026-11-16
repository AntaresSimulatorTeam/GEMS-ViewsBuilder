# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.simulation_table import join
from gems_views_builder.input.view_building_input import ViewBuildingInput
from gems_views_builder.metric_view import MetricView


class ViewBuilder:
    def __init__(self, input_data: ViewBuildingInput) -> None:
        self.filtered_st = input_data.filtered_st
        self.view_config = input_data.view_config
        self.metric_structure_table_builder = input_data.metric_structure_table_builder
        self.aggregation_processor = input_data.aggregation_processor

    def build(self) -> list[MetricView]:
        metric_views: list[MetricView] = []
        for metric in self.view_config.metrics:
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            structured_view = join(metric_structure_table, self.filtered_st)
            # Give the view a view config id (will be used by accumulation after view building).
            structured_view.view_config_id = self.view_config.id
            views = self.aggregation_processor.run(structured_view, metric)
            metric_views.extend(views)
        return metric_views
