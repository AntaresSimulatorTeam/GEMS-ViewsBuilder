# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""ViewBuilder."""

from gems_views_builder.aggregators.scenario_aggregator import make_scenario_operator, to_scenario_view
from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.input_data import InputData
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


class ViewBuilder:
    def __init__(self, input_data: InputData, metric_structure_table_builder: MetricStructureTableBuilder) -> None:
        # # Input data of pipeline
        self.input_data = input_data
        # # Builder which is reusable over metrics
        self.metric_structure_table_builder = metric_structure_table_builder
        # # Aggregator for step 2B
        self.terms_aggregator = TermsAggregator(self.input_data.filtered_st)
        # # Aggregator for step 2C
        self.time_aggregator = TimeAggregator(self.input_data.view_config.time_aggregation)

        self.scenario_operator = make_scenario_operator(self.input_data.view_config.scenario_aggregation)

    def build(self) -> list[MetricView]:
        metric_views: list[MetricView] = []
        for metric in self.input_data.view_config.metrics:
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            metric_view = self.terms_aggregator.run(metric_structure_table, metric)
            temporal_metric_view = self.time_aggregator.run(metric_view, metric)
            to_scenario_view(temporal_metric_view, self.scenario_operator)
            metric_views.append(temporal_metric_view)

        return metric_views
