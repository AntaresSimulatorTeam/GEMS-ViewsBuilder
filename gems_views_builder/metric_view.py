# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from gems_views_builder.input.view_config import TimeGranularity


@dataclass
class MetricView(ABC):
    time_granularity: TimeGranularity = TimeGranularity.HOUR

    @abstractmethod
    def lazy_data_frame(self) -> pl.LazyFrame:
        pass


@dataclass
class PersistentMetricView(MetricView):
    persistence_path: Path = field(kw_only=True)

    def lazy_data_frame(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.persistence_path)

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)


@dataclass
class RamMetricView(MetricView):
    lazyframe: pl.LazyFrame = field(kw_only=True)

    def lazy_data_frame(self) -> pl.LazyFrame:
        return self.lazyframe
