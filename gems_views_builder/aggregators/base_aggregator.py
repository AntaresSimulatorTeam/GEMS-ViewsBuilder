# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import MetricView, PersistentMetricView


class PersistingAggregator(ABC):
    """Shared scaffolding for aggregators that transform a MetricView's lazy frame and persist the
    result as a new parquet-backed MetricView.

    Subclasses must set the `_subdirectory` class attribute and implement `_build_lazy_frame`.
    """
    _subdirectory: str

    def __init__(self) -> None:
        self._root_dir = Path(tempfile.mkdtemp())
        self._save_dir = self._root_dir / "views" / self._subdirectory
        self._save_dir.mkdir(parents=True, exist_ok=True)
        # # Deferred cleanup: outputs may be read later in the pipeline, after this aggregator
        # # instance has already been garbage collected, so cleaning up in __del__ would be unsafe.
        # # Removing the whole temp tree at interpreter exit is safe for every aggregator.
        atexit.register(rmtree, self._root_dir, True)

    @abstractmethod
    def _build_lazy_frame(self, metric_view: MetricView, metric: Metric) -> pl.LazyFrame:
        """Return the transformed lazy frame to persist."""

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        lazy_frame = self._build_lazy_frame(metric_view, metric)

        time_granularity = metric_view.time_granularity
        out_path = self._save_dir / f"{time_granularity.value}_{metric.id}_{uuid.uuid4()}.parquet"
        logging.info(f"[{metric.id}] {type(self).__name__} view written to {out_path}")
        return PersistentMetricView(time_granularity, lazyframe=lazy_frame, persistence_path=out_path)
