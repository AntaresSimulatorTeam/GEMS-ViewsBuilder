# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.common import sink_to_parquet


@dataclass
class MetricView:
    lazyframe: pl.LazyFrame
    view_config_id: str
    aggregation_pattern_id: str

    def __init__(self, lazyframe: pl.LazyFrame, view_config_id: str = "", aggregation_pattern_id: str = ""):
        self.view_config_id = view_config_id
        self.aggregation_pattern_id = aggregation_pattern_id
        self.lazyframe = lazyframe

    def lazy_data_frame(self) -> pl.LazyFrame:
        return self.lazyframe

    def ids_as_str(self) -> str:
        return f"{self.view_config_id}_{self.aggregation_pattern_id}"


@dataclass
class PersistentMetricView(MetricView):
    persistence_path: Path

    def __init__(self, lazyframe: pl.LazyFrame, path: Path, view_config_id: str = "", aggregation_pattern_id: str = ""):
        super().__init__(lazyframe, view_config_id, aggregation_pattern_id)
        self.persistence_path = path
        sink_to_parquet(self.lazyframe, self.persistence_path)

    def lazy_data_frame(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.persistence_path)

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)