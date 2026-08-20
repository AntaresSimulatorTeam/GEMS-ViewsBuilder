# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import Pattern
from gems_views_builder.into_scenario_view import ScenarioPatternOperator, make_scenario_operator, to_scenario_view
from gems_views_builder.metric_view import MetricView


# # Combinatorial formula 5 * 2 = 10 at maximum
# # 5 time granularities
# # 2 scenario types
@dataclass
class PatternStep:
    time_aggregator: TimeAggregator
    scenario_operator: ScenarioPatternOperator


class PatternRunner:
    def __init__(self, patterns: tuple[Pattern, ...]) -> None:
        self.pattern_steps = [
            PatternStep(
                time_aggregator=TimeAggregator(pattern.time, pattern.id),
                scenario_operator=make_scenario_operator(pattern.scenario),
            )
            for pattern in patterns
        ]

    def run(self, metric_view: MetricView, metric: Metric) -> list[MetricView]:
        pattern_views: list[MetricView] = []
        for step in self.pattern_steps:
            temporal_metric_view = step.time_aggregator.run(metric_view, metric)
            to_scenario_view(temporal_metric_view, step.scenario_operator)
            pattern_views.append(temporal_metric_view)

        return pattern_views
