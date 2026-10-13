# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
import tempfile
import uuid
import logging
from pathlib import Path
import polars as pl
from gems_views_builder.input.view_config import AggregationPattern
from gems_views_builder import MetricView, PersistentMetricView
from gems_views_builder.input.catalog import Metric


class SpatialFiltering:
    def __init__(self, aggregation_pattern: AggregationPattern):
        self._root_dir = Path(tempfile.mkdtemp())
        self._persistence_dir = self._root_dir / "views" / "spatial_filtering"
        self._persistence_dir.mkdir(parents=True, exist_ok=True)
        self.locations = aggregation_pattern.spatial_filter

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        file_path = self._persistence_dir / f"{metric_view.time_granularity.value}_{metric.id}_{uuid.uuid4()}.parquet"
        logging.info(f"Spatial filtered view written to {file_path}")
        if self.locations:
            lazy_frame = metric_view.lazy_data_frame().filter(pl.col("metric_location").is_in(self.locations))
            return PersistentMetricView(lazy_frame=lazy_frame,
                                        time_granularity=metric_view.time_granularity,
                                        persistence_path=file_path)
        return PersistentMetricView(lazy_frame=metric_view.lazy_data_frame(),
                                    time_granularity=metric_view.time_granularity,
                                    persistence_path=file_path)