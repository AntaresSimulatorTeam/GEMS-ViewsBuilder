# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

import polars as pl

from gems_views_builder.common import sink_to_parquet
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView


class AggregationOperator(ABC):
    def __init__(self) -> None:
        self._root_dir = Path(tempfile.mkdtemp())
        # Output files must outlive this aggregator: accumulate_on_disk() reads them
        # after build() returns and the aggregator may already be garbage collected.
        atexit.register(rmtree, self._root_dir, True)

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        aggregated = self._aggregate(metric_view.scan(), metric)
        path = self._make_persistence_file(metric)
        sink_to_parquet(aggregated, path)
        self._log_write(metric, path)
        return self._to_metric_view(path, metric_view)

    def _make_persistence_file(self, metric: Metric) -> Path:
        return self._root_dir / f"{metric.id}_{uuid4()}.parquet"

    def _to_metric_view(self, path: Path, source: MetricView) -> MetricView:
        return MetricView(path)

    def _log_write(self, metric: Metric, path: Path) -> None:
        logging.info(f"[{metric.id}] View written to {path}")

    @abstractmethod
    def _aggregate(self, frame: pl.LazyFrame, metric: Metric) -> pl.LazyFrame:
        pass
