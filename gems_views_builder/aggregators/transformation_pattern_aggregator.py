# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.aggregation_operator import AggregationOperator
from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import TransformationPattern, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView, persist_temporal_metric_view
from gems_views_builder.spatial_filter import SpatialFilter


class TransformationPatternOperator:
    def __init__(self, pattern: TransformationPattern) -> None:
        self.spatial_filter = SpatialFilter(pattern.spatial_filter)
        self.time_granularity = pattern.time_granularity
        self.transformation_aggregators: list[AggregationOperator] = [
            TimeAggregator(pattern.time_granularity),
            ScenarioAggregator(pattern.scenario),
        ]

    def run(self, metric_view: MetricView, metric: Metric) -> TemporalMetricView:
        dataframe = self.spatial_filter.apply_spatial_filter(metric_view.get_lazy_frame())
        for aggregator in self.transformation_aggregators:
            dataframe = aggregator.run(dataframe, metric)
        return persist_temporal_metric_view(dataframe, self.time_granularity)


def transformation_patterns_factory(view_config: ViewConfig) -> list[TransformationPatternOperator]:
    return [TransformationPatternOperator(pattern) for pattern in view_config.transformations_patterns]
