# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import tempfile
import uuid
from pathlib import Path

import polars as pl

from gems_views_builder import MetricView, PersistentMetricView
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern


class SpatialFiltering:
    def __init__(self, aggregation_pattern: AggregationPattern):
        self._root_dir = Path(tempfile.mkdtemp())
        self._save_dir = self._root_dir / "views" / "spatial_filtering"
        self._save_dir.mkdir(parents=True, exist_ok=True)
        self.locations = aggregation_pattern.spatial_filter

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        out_path = self._save_dir / f"{metric_view.time_granularity.value}_{metric.id}_{uuid.uuid4()}.parquet"
        logging.info(f"Spatial filtered view written to {out_path}")
        if self.locations:
            lazy_frame = metric_view.lazy_data_frame().filter(pl.col("metric_location").is_in(self.locations))
            return PersistentMetricView(
                lazyframe=lazy_frame, time_granularity=metric_view.time_granularity, persistence_path=out_path
            )
        return PersistentMetricView(
            lazyframe=metric_view.lazy_data_frame(),
            time_granularity=metric_view.time_granularity,
            persistence_path=out_path
        )
