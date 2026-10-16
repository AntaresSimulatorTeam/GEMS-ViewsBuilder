# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.aggregations_processor import AggregationProcessor
from gems_views_builder.input.simulation_table import join
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData
from gems_views_builder.metric_view import TemporalMetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


class ViewBuilder:
    def __init__(
        self,
        input_data: ViewBuildingInputData,
        metric_structure_table_builder: MetricStructureTableBuilder,
        aggregation_processor: AggregationProcessor,
    ) -> None:
        self.input_data = input_data
        self.metric_structure_table_builder = metric_structure_table_builder
        self.aggregation_processor = aggregation_processor

    def build(self) -> list[TemporalMetricView]:
        metric_views: list[TemporalMetricView] = []
        for metric in self.input_data.view_config.metrics:
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            structured_simulation_table = join(metric_structure_table, self.input_data.filtered_st)
            metric_view = self.aggregation_processor.run(structured_simulation_table, metric)
            metric_views.extend(metric_view)
        return metric_views
