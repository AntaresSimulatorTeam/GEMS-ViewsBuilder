# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.aggregation_operator import AggregationOperator
from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView


class PatternAggregator:
    def __init__(self, pattern: AggregationPattern) -> None:
        self.aggregators: list[AggregationOperator] = [
            TimeAggregator(pattern.time_granularity),
            ScenarioAggregator(pattern.scenario, pattern.spatial_filter),
        ]

    def run(self, metric_view: MetricView, metric: Metric) -> TemporalMetricView:
        for aggregator in self.aggregators:
            metric_view = aggregator.run(metric_view, metric)
        if not isinstance(metric_view, TemporalMetricView):
            raise TypeError("Pattern aggregation must produce a TemporalMetricView")
        return metric_view


def aggregation_patterns_factory(view_config: ViewConfig) -> list[PatternAggregator]:
    return [PatternAggregator(pattern) for pattern in view_config.aggregation_patterns]
