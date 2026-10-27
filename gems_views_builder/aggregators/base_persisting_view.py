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
from gems_views_builder.metric_view import MetricView, PersistentMetricView


class CreatePersistingView(ABC):
    """Shared parent class for aggregators.
    Subclasses will transform a MetricView's lazy frame and persists the result as a new parquet-backed MetricView.
    Subclasses just has to implement _build_lazy_frame(...) and set _subdirectory.
    """
    _subdirectory: str

    def __init__(self) -> None:
        self._root_dir = Path(tempfile.mkdtemp())
        self._save_dir = self._root_dir / "views" / self._subdirectory
        self._save_dir.mkdir(parents=True, exist_ok=True)
        
        # Deferred cleanup: outputs may be read later in the pipeline, after this aggregator
        # instance has already been garbage collected, so cleaning up in __del__ would be unsafe.
        # Removing the whole temp tree at interpreter exit is safe for every aggregator.
        atexit.register(rmtree, self._root_dir, True)

    @abstractmethod
    def _build_lazy_frame(self, metric_view: MetricView, metric: Metric) -> pl.LazyFrame:
        pass

    def _output_aggregation_pattern_id(self, metric_view: MetricView) -> str:
        """Return the aggregation pattern id to tag the persisted output with.
        This function returns the default aggregation pattern id.
        Caution : this function can be overridden by subclasses to return a different aggregation pattern id.
        """
        return metric_view.aggregation_pattern_id

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        lazy_frame = self._build_lazy_frame(metric_view, metric)

        aggregation_pattern_id = self._output_aggregation_pattern_id(metric_view)

        out_path = self._save_dir / f"{aggregation_pattern_id}_{metric.id}_{uuid.uuid4()}.parquet"
        logging.info(f"[{metric.id}] {type(self).__name__} view written to {out_path}")
        return PersistentMetricView(aggregation_pattern_id, lazyframe=lazy_frame, persistence_path=out_path)
