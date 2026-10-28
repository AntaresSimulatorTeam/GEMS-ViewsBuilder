# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from gems_views_builder.common import sink_to_parquet


@dataclass
class MetricView:
    lazyframe: pl.LazyFrame
    view_config_id: str | None = field(init=False, default=None)
    aggregation_pattern_id: str | None = field(init=False, default=None)

    @classmethod
    def from_metric_view(cls, mv: "MetricView", lazyframe: pl.LazyFrame) -> "MetricView":
        """Build a MetricView carrying over the ids of an existing MetricView."""
        new_view = cls(lazyframe)
        new_view.view_config_id = mv.view_config_id
        new_view.aggregation_pattern_id = mv.aggregation_pattern_id
        return new_view

    def lazy_data_frame(self) -> pl.LazyFrame:
        return self.lazyframe

    def ids_as_str(self) -> str:
        return f"{self.view_config_id}_{self.aggregation_pattern_id}"


@dataclass
class PersistentMetricView(MetricView):
    persistence_path: Path = None

    @classmethod
    def from_metric_view(cls, mv: "MetricView", lazyframe: pl.LazyFrame, path: Path) -> "PersistentMetricView":
        """Build a PersistentMetricView carrying over the ids of an existing MetricView."""
        new_view = cls(lazyframe, path)
        new_view.view_config_id = mv.view_config_id
        new_view.aggregation_pattern_id = mv.aggregation_pattern_id
        return new_view

    def __post_init__(self) -> None:
        sink_to_parquet(self.lazyframe, self.persistence_path)

    def lazy_data_frame(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.persistence_path)

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)