# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.common import sink_to_parquet


@dataclass
class View:
    dataframe: pl.LazyFrame


class ViewSinker(ABC):
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    @abstractmethod
    def sink(self, frame: pl.LazyFrame, file_name: str) -> View:
        pass


class ParquetViewSinker(ViewSinker):
    def sink(self, frame: pl.LazyFrame, file_name: str) -> View:
        file_path = self.output_path / f"{file_name}_{self.timestamp}.parquet"
        sink_to_parquet(frame, file_path)
        logging.info("Results merged into parquet file")
        return View(dataframe=pl.scan_parquet(file_path))


class CsvViewSinker(ViewSinker):
    def sink(self, frame: pl.LazyFrame, file_name: str) -> View:
        file_path = self.output_path / f"{file_name}_{self.timestamp}.csv"
        frame.sink_csv(file_path)
        logging.info("Results merged into csv file")
        return View(dataframe=pl.scan_csv(file_path))
