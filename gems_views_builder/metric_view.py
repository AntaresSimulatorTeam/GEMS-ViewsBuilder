# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import Field
import polars as pl

from gems_views_builder.common import sink_to_parquet


@dataclass
class MetricView:
    # id part : useful for accumulation, after view building.
    view_config_id: str = Field(init=False)
    aggregation_pattern_id: str = Field(init=False)

    lazyframe: pl.LazyFrame = field(kw_only=True)

    def lazy_data_frame(self) -> pl.LazyFrame:
        return self.lazyframe

@dataclass
class PersistentMetricView(MetricView):
    persistence_path: Path = field(kw_only=True)

    def __post_init__(self) -> None:
        sink_to_parquet(self.lazyframe, self.persistence_path)

    def lazy_data_frame(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.persistence_path)

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)
