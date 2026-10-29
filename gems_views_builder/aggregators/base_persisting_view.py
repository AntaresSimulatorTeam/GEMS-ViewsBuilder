# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
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

    # Default method to compute the output path for the persisted view.
    # Can be overridden by subclasses if needed.
    def _out_path(self, metric_view: MetricView, metric: Metric) -> Path:
        return self._save_dir / f"{metric_view.ids_as_str()}_{metric.id}.parquet"

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        lazy_frame = self._build_lazy_frame(metric_view, metric)

        out_path = self._out_path(metric_view, metric)
        logging.info(f"[{metric.id}] {type(self).__name__} view written to {out_path}")
        return PersistentMetricView(lazyframe=lazy_frame,
                                    path=out_path,
                                    view_config_id=metric_view.view_config_id,
                                    aggregation_pattern_id=metric_view.aggregation_pattern_id)
