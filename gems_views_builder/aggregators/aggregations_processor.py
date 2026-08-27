# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


import polars as pl

from gems_views_builder.aggregators.pattern_aggregator import aggregation_patterns_factory
from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.aggregators.time_aggregator import perform_time_aggregations
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import ViewConfig, TimeGranularity
from gems_views_builder.metric_view import MetricView


class AgggregationProcessor:
    def __init__(self, view_config: ViewConfig) -> None:
        self.terms_aggregator = TermsAggregator()
        # self.time_aggregated_metric_views = dict[TimeGranularity, MetricView]
        self.aggregation_patterns = aggregation_patterns_factory(view_config)
        self.time_granularities = view_config.get_time_granularities()

    def run(self, structured_simulation_table: pl.LazyFrame, metric: Metric) -> list[MetricView]:
        metric_views: list[MetricView] = []
        metric_view = self.terms_aggregator.run(structured_simulation_table, metric)

        time_aggregated_metric_views = perform_time_aggregations(metric, metric_view, self.time_granularities)

        for pattern in self.aggregation_patterns:
            metric_view = pattern.run(time_aggregated_metric_views)
            metric_views.append(metric_view)
        return metric_views
