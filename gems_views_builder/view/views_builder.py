# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""ViewBuilder."""

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
        self.time_aggregator = TimeAggregator(self.view_building_input.view_config.time_aggr_granularity)
        self.scenario_operator = make_scenario_operator(self.view_building_input.view_config.scenario_aggregation)

    def build(self) -> list[MetricView]:
        metric_views: list[MetricView] = []
        # # Before this step locations are built, practically we know what is located where
        for metric in self.view_building_input.view_config.metrics:
            # # Create metric
            metric_structure_table = self.metric_structure_table_builder.build(metric)
            metric_view = self.terms_aggregator.run(metric_structure_table, metric)
            # # Here is problem
            temporal_metric_view = self.time_aggregator.run(metric_view, metric)
            to_scenario_view(temporal_metric_view, self.scenario_operator)
            metric_views.append(temporal_metric_view)

        return metric_views
