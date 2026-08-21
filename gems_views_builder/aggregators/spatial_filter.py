# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView


@dataclass
class SpatialFilter:
    locations: list[str] | None

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        if self.locations is None:
            return metric_view

        try:
            file_descriptor, tmp_path = tempfile.mkstemp(suffix=".parquet")
            os.close(file_descriptor)

            view = pl.scan_parquet(metric_view.persistence_path).filter(pl.col("metric_location").is_in(self.locations))
            view.sink_parquet(
                tmp_path,
                compression=PARQUET_COMPRESSION,
                compression_level=PARQUET_COMPRESSION_LEVEL,
                row_group_size=PARQUET_ROW_GROUP_SIZE,
            )
            os.replace(src=tmp_path, dst=metric_view.persistence_path)
        except Exception:
            os.remove(tmp_path)
        logg_write(metric, metric_view.persistence_path)
        return metric_view


def logg_write(metric: Metric, file_path: Path) -> None:
    logging.info(f"[{metric.id}] Spatial filter applied to {file_path}")
