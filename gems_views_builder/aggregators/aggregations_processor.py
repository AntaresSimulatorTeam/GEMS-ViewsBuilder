# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.aggregators.pattern_aggregator import aggregation_patterns_factory
from gems_views_builder.aggregators.terms_aggregator import TermsAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView


class AggregationProcessor:
    def __init__(self, view_config: ViewConfig) -> None:
        self.terms_aggregator = TermsAggregator()
        self.aggregation_patterns = aggregation_patterns_factory(view_config)

    def run(self, metric_view: MetricView, metric: Metric) -> list[TemporalMetricView]:
        metric_view = self.terms_aggregator.run(metric_view, metric)
        return [pattern.run(metric_view, metric) for pattern in self.aggregation_patterns]
