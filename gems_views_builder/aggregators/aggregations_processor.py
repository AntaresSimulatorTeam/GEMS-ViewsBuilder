# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


import polars as pl

from gems_views_builder.aggregators.pattern_aggregator import aggregation_patterns_factory
from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.aggregators.time_aggregator import perform_time_aggregations
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import TemporalMetricView


class AgggregationProcessor:
    def __init__(self, view_config: ViewConfig) -> None:
        self.terms_aggregator = TermsAggregator()
        self.aggregation_patterns = aggregation_patterns_factory(view_config)
        self.time_granularities = view_config.get_time_granularities()

    def run(self, structured_simulation_table: pl.LazyFrame, metric: Metric) -> list[TemporalMetricView]:
        time_metric_views: list[TemporalMetricView] = []
        metric_view = self.terms_aggregator.run(structured_simulation_table, metric)

        time_aggregated_metric_views = perform_time_aggregations(metric, metric_view, self.time_granularities)

        for aggregation in self.aggregation_patterns:
            view = aggregation.run(time_aggregated_metric_views)
            time_metric_views.append(metric_view)
        return time_metric_views
