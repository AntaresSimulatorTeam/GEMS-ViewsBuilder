# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.aggregations_processor import AgggregationProcessor
from gems_views_builder.input.simulation_table import join
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import TemporalMetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def give_views_a_config(metric_views: list[TemporalMetricView], view_config: ViewConfig) -> None:
    for view in metric_views:
        view.view_config_id = view_config.id

class ViewBuilder:
    def __init__(
        self,
        input_data: ViewBuildingInputData,
        metric_structure_table_builder: MetricStructureTableBuilder,
        aggregation_processor: AgggregationProcessor,
    ) -> None:
        self.input_data = input_data
        self.metric_structure_table_builder = metric_structure_table_builder
        self.aggregation_processor = aggregation_processor
        self.view_config = input_data.view_config

    def build(self) -> list[TemporalMetricView]:
        metric_views: list[TemporalMetricView] = []
        for metric in self.view_config.metrics:
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            structured_simulation_table = join(metric_structure_table, self.input_data.filtered_st)
            views = self.aggregation_processor.run(structured_simulation_table, metric)
            metric_views.extend(views)
        give_views_a_config(metric_views, self.view_config)
        return metric_views
