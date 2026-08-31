# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.input.view_config import TimeGranularity


@dataclass
class MetricView:
    """View for a single computed metric, stored as a parquet file."""

    persistence_path: Path

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.persistence_path}")
        self.persistence_path.unlink(missing_ok=True)


@dataclass
class TemporalMetricView(MetricView):
    time_granularity: TimeGranularity


def sink_to_parquet(view: pl.LazyFrame, path: Path) -> None:
    view.sink_parquet(
        path,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        row_group_size=PARQUET_ROW_GROUP_SIZE,
    )
