# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator, make_scenario_operator
from gems_views_builder.aggregators.time_aggregator import TimeAggregatorDecorator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView
from gems_views_builder.spatial_filter import SpatialFilter


class PatternAggregator:
    def __init__(
        self, pattern: AggregationPattern, time_aggregated_metric_views: dict[TimeGranularity, MetricView]
    ) -> None:
        self.time_aggregator = TimeAggregatorDecorator(time_aggregated_metric_views, pattern.time_granularity)
        self.scenario_aggregator = ScenarioAggregator(
            make_scenario_operator(pattern.scenario), SpatialFilter(pattern.spatial_filter)
        )
        self.id = pattern.id  # For debug only (useless otherwise)

    def run(self, metric_view: TemporalMetricView, metric: Metric) -> MetricView:
        temporal_metric_view = self.time_aggregator.run(metric_view, metric)
        return self.scenario_aggregator.run(temporal_metric_view)


class AggregationPatternList:
    def __init__(self, view_config: ViewConfig) -> None:
        self.aggregation_patterns: list[PatternAggregator] = []
        self.time_aggregated_metric_views: dict[TimeGranularity, MetricView] = {}

        for pattern in view_config.aggregation_patterns:
            self.aggregation_patterns.append(PatternAggregator(pattern, self.time_aggregated_metric_views))

    def run(self, metric_view: TemporalMetricView, metric: Metric) -> list[MetricView]:
        metric_views: list[MetricView] = []
        self.time_aggregated_metric_views.clear()  # Important : clearing for each new metric
        for pattern in self.aggregation_patterns:
            view = pattern.run(metric_view, metric)
            metric_views.append(view)
        return metric_views
