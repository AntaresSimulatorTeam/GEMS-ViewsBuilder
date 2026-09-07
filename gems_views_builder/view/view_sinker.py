# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import sink_to_parquet
from gems_views_builder.view.accumulate_views import View


class ViewSinker(ABC):
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    @abstractmethod
    def sink(self, merged: pl.LazyFrame, time_granularity: TimeGranularity) -> View:
        pass


class ParquetViewSinker(ViewSinker):
    def sink(self, merged: pl.LazyFrame, time_granularity: TimeGranularity) -> View:
        result_path = self.output_path / f"view_{time_granularity.value}_{self.timestamp}.parquet"
        sink_to_parquet(merged, result_path)
        logging.info("Results merged into parquet file")
        return View(dataframe=pl.scan_parquet(result_path))


class CsvViewSinker(ViewSinker):
    def sink(self, merged: pl.LazyFrame, time_granularity: TimeGranularity) -> View:
        result_path = self.output_path / f"view_{time_granularity.value}_{self.timestamp}.csv"
        merged.sink_csv(result_path)
        logging.info("Results merged into csv file")
        return View(dataframe=pl.scan_csv(result_path))
