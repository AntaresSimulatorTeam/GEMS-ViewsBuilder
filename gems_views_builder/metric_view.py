# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

import polars as pl

from gems_views_builder.common import sink_to_parquet
from gems_views_builder.input.view_config import TimeGranularity

_PERSIST_DIR = Path(tempfile.mkdtemp())
atexit.register(rmtree, _PERSIST_DIR, True)


@dataclass
class MetricView:
    """View for a single computed metric, stored as a parquet file."""

    persistence_path: Path

    def scan(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.persistence_path)

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)


@dataclass
class TemporalMetricView(MetricView):
    time_granularity: TimeGranularity


def persist_metric_view(frame: pl.LazyFrame) -> MetricView:
    path = _PERSIST_DIR / f"{uuid4()}.parquet"
    sink_to_parquet(frame, path)
    return MetricView(path)
