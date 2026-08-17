# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.view_config import ScenarioAggregation
from gems_views_builder.into_scenario_view import ScenarioOperator, make_scenario_operator, to_scenario_view
from gems_views_builder.metric_view import MetricView
from gems_views_builder.input.catalog import Metric


# # Combinatorial formula 5 * 2 = 10 at maximum
# # 5 time granularities
# # 2 scenario types
@dataclass
class ScenarioAggregationStep:
    time_aggregator: TimeAggregator
    scenario_operator: ScenarioOperator


@dataclass
class ScenarioAggregationRunner:
    def __init__(self, scenario_aggregations: tuple[ScenarioAggregation, ...]) -> None:
        self.scenario_aggregation_steps = [
            ScenarioAggregationStep(
                time_aggregator=TimeAggregator(scenario_aggregation.time, scenario_aggregation.id),
                scenario_operator=make_scenario_operator(scenario_aggregation.scenario),
            )
            for scenario_aggregation in scenario_aggregations
        ]

    def run(self, metric_view: MetricView, metric: Metric) -> list[MetricView]:
        scenario_aggregation_views: list[MetricView] = []
        for step in self.scenario_aggregation_steps:
            temporal_metric_view = step.time_aggregator.run(metric_view, metric)
            to_scenario_view(temporal_metric_view, step.scenario_operator)
            scenario_aggregation_views.append(temporal_metric_view)

        return scenario_aggregation_views
