# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import polars as pl

from gems_views_builder.aggregators.base_persisting_view import CreatePersistingView
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern
from gems_views_builder.metric_view import MetricView


class LocationFiltering(CreatePersistingView):
    _subdirectory = "location_filtering"

    def __init__(self, aggregation_pattern: AggregationPattern) -> None:
        self.locations = aggregation_pattern.location_filter
        super().__init__()

    def _build_lazy_frame(self, metric_view: MetricView, metric: Metric) -> pl.LazyFrame:
        lazy_frame = metric_view.lazy_data_frame()
        if self.locations:
            lazy_frame = lazy_frame.filter(pl.col("metric_location").is_in(self.locations))
        return lazy_frame
