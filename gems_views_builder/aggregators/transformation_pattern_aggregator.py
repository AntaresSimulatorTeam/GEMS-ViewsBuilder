# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import TransformationPattern, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView, sink_temporal_metric_view
from gems_views_builder.spatial_filter import SpatialFilter


class TransformationPatternOperator:
    def __init__(self, pattern: TransformationPattern) -> None:
        self.spatial_filter = SpatialFilter(pattern.spatial_filter)
        self.time_granularity = pattern.time_granularity
        self.scenario_aggregator = ScenarioAggregator(pattern.scenario)

    def run(self, metric_view: MetricView, metric: Metric) -> TemporalMetricView:
        dataframe = self.spatial_filter.apply_spatial_filter(metric_view.get_lazy_frame())
        dataframe = self.scenario_aggregator.run(dataframe, metric)
        return sink_temporal_metric_view(dataframe, self.time_granularity)


def transformations_patterns_factory(view_config: ViewConfig) -> list[TransformationPatternOperator]:
    return [TransformationPatternOperator(pattern) for pattern in view_config.transformations_patterns]
