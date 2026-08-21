# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.scenario_runner import PatternRunner
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


class ViewBuilder:
    def __init__(
        self,
        view_building_input: ViewBuildingInputData,
        metric_structure_table_builder: MetricStructureTableBuilder,
    ) -> None:
        self.view_building_input = view_building_input
        self.metric_structure_table_builder = metric_structure_table_builder
        # Aggregator for step 2B
        self.terms_aggregator = TermsAggregator(self.view_building_input.filtered_st)
        # Aggregator for step 2C extended for multiple scenarios
        self.pattern_runner = PatternRunner(self.view_building_input.view_config.aggregation_patterns)

    def build(self) -> list[MetricView]:
        metric_views: list[MetricView] = []
        for metric in self.view_building_input.view_config.metrics:
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            metric_view = self.terms_aggregator.run(metric_structure_table, metric)
            pattern_views = self.pattern_runner.run(metric_view, metric)
            metric_views.extend(pattern_views)
        return metric_views
