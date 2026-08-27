# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator, make_scenario_operator
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView
from gems_views_builder.spatial_filter import SpatialFilter


class PatternAggregator:
    def __init__(self, pattern: AggregationPattern):
        self.time_granularity = pattern.time_granularity
        self.scenario_aggregator = ScenarioAggregator(
            make_scenario_operator(pattern.scenario), SpatialFilter(pattern.spatial_filter)
        )

    def run(self, time_aggregated_metric_views: dict[TimeGranularity, MetricView]) -> MetricView:
        return self.scenario_aggregator.run(time_aggregated_metric_views[self.time_granularity])


def aggregation_patterns_factory(view_config: ViewConfig) -> list[PatternAggregator]:
    pattern_aggregators = []
    for pattern in view_config.aggregation_patterns:
        pattern_aggregators.append(PatternAggregator(pattern))
    return pattern_aggregators
