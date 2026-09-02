# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


import polars as pl

from gems_views_builder.aggregators.pattern_aggregator import AggregationPatternList
from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import TemporalMetricView


class AgggregationProcessor:
    def __init__(self, view_config: ViewConfig) -> None:
        self.terms_aggregator = TermsAggregator()
        self.aggregation_patterns = AggregationPatternList(view_config)

    def run(self, structured_simulation_table: pl.LazyFrame, metric: Metric) -> list[MetricView]:
        metric_view = self.terms_aggregator.run(structured_simulation_table, metric)
        metric_views = self.aggregation_patterns.run(metric_view, metric)
        return metric_views
