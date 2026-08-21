# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


from gems_views_builder.aggregators.pattern_aggregator import PatternAggregator
from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator, make_scenario_operator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import Pattern
from gems_views_builder.metric_view import MetricView


class PatternRunner:
    def __init__(self, patterns: tuple[Pattern, ...]) -> None:
        self.pattern_aggregators = [
            PatternAggregator(
                time_aggregator=TimeAggregator(pattern.time),
                scenario_aggregator=ScenarioAggregator(make_scenario_operator(pattern.scenario)),
            )
            for pattern in patterns
        ]

    def run(self, metric_view: MetricView, metric: Metric) -> list[MetricView]:
        pattern_views: list[MetricView] = []
        for aggregator in self.pattern_aggregators:
            pattern_views.append(aggregator.run(metric_view, metric))
        return pattern_views
