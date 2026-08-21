from dataclasses import dataclass

import polars as pl

from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView


@dataclass
class AggregationsProcessor:
    terms_aggregator: TermsAggregator
    aggregations: list[str]  # aggregations

    def run(self, structured_simulation_table: pl.LazyFrame, metric: Metric):
        views: list[MetricView] = []

        return views
