# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView


class PatternAggregator:
    def __init__(self, pattern: AggregationPattern):
        self.time_aggregator = TimeAggregator(pattern.time_granularity)
        self.scenario_aggregator = ScenarioAggregator(pattern)

    def run(self, metric_view: MetricView, metric: Metric) -> TemporalMetricView:
        temporal_metric_view = self.time_aggregator.run(metric_view, metric)
        return self.scenario_aggregator.run(temporal_metric_view, metric)


def aggregation_patterns_factory(view_config: ViewConfig) -> list[PatternAggregator]:
    pattern_aggregators = []
    for pattern in view_config.aggregation_patterns:
        pattern_aggregators.append(PatternAggregator(pattern))
    return pattern_aggregators
