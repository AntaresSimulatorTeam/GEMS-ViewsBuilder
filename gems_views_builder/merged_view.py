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
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.metric_view import MetricView


class MergedView:
    """Final merged view written to the results directory."""

    def __init__(self, result_path: Path, metric_views: list[MetricView]) -> None:
        self.result_path = result_path
        logging.info(f"Merging {len(metric_views)} metric view(s) into results")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.result_path = self.result_path / f"view{timestamp}.parquet"
        pl.scan_parquet([v.file_path for v in metric_views]).sink_parquet(
            self.result_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        logging.info(f"Results merged into {self.result_path}")
