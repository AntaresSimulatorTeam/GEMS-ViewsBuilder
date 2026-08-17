# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData
from gems_views_builder.into_scenario_view import make_scenario_operator, to_scenario_view
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
        # Aggregator for step 2C

        # # Here we need to introduce multiple TimeAggregators for each scenario aggregation
        # # With new feature we could have multiple Scenarios
        # # Idea is to wrap everything
        self.time_aggregator = TimeAggregator(self.view_building_input.view_config.scenario_aggregations[0].time)
        self.scenario_operator = make_scenario_operator(
            self.view_building_input.view_config.scenario_aggregations[0].scenario
        )

    def build(self) -> list[MetricView]:
        metric_views: list[MetricView] = []
        for metric in self.view_building_input.view_config.metrics:
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            metric_view = self.terms_aggregator.run(metric_structure_table, metric)
            # # Here is problem, we need to loop over scenarios and run the time aggregation for each scenario
            # # Scenario Aggregator will execute this 2 functions for each scenario and return a list of MetricViews
            # # That list will be exetendend to the metric_views list
            # #
            temporal_metric_view = self.time_aggregator.run(metric_view, metric)
            to_scenario_view(temporal_metric_view, self.scenario_operator)

            metric_views.append(temporal_metric_view)

        return metric_views
