# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.view.view import View


class ViewSinker(ABC):
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    @abstractmethod
    def sink(self, merged: pl.LazyFrame) -> View:
        pass


class ParquetViewSinker(ViewSinker):
    def sink(self, merged: pl.LazyFrame) -> View:
        result_path = self.output_path / f"view{self.timestamp}.parquet"
        merged.sink_parquet(
            result_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        logging.info("Results merged into parquet file")
        return View(dataframe=pl.scan_parquet(result_path))


class CsvViewSinker(ViewSinker):
    def sink(self, merged: pl.LazyFrame) -> View:
        result_path = self.output_path / f"view{self.timestamp}.csv"
        merged.sink_csv(result_path)
        logging.info("Results merged into csv file")
        return View(dataframe=pl.scan_csv(result_path))
