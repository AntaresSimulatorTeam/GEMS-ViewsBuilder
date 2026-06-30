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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.metric_view import MetricView


@dataclass
class View:
    dataframe: pl.LazyFrame
    # # Here we could store ViewConfig in future versions


def accumulate_on_disk(metric_views: list[MetricView], results_path: Path) -> View:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    result_path = results_path / f"view{timestamp}.parquet"
    pl.scan_parquet([v.persistence_path for v in metric_views]).sink_parquet(
        result_path,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        row_group_size=PARQUET_ROW_GROUP_SIZE,
    )
    logging.info(f"Results merged into {result_path}")
    return View(dataframe=pl.scan_parquet(result_path))
