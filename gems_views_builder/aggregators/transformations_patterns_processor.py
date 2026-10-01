# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import polars as pl

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.aggregators.transformation_pattern_aggregator import transformations_patterns_factory
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView, sink_temporal_metric_view


class TransformationsPatternsProcessor:
    def __init__(self, view_config: ViewConfig) -> None:
        self.terms_aggregator = TermsAggregator()
        self.time_aggregators = {
            granularity: TimeAggregator(granularity) for granularity in view_config.get_time_granularities()
        }
        self.transformations_patterns = transformations_patterns_factory(view_config)

    def run(self, metric_view: MetricView, metric: Metric) -> list[TemporalMetricView]:
        terms = self.terms_aggregator.run(metric_view.get_lazy_frame(), metric)
        time_views = self._sink_time_aggregations(terms, metric)
        return [pattern.run(time_views[pattern.time_granularity], metric) for pattern in self.transformations_patterns]

    def _sink_time_aggregations(self, terms: pl.LazyFrame, metric: Metric) -> dict[TimeGranularity, TemporalMetricView]:
        return {
            granularity: sink_temporal_metric_view(aggregator.run(terms, metric), granularity)
            for granularity, aggregator in self.time_aggregators.items()
        }
