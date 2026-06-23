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


class Writer:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def merge_results(self, metric_views: list[MetricView]) -> Path | None:
        logging.info(f"Merging {len(metric_views)} metric view(s) into results")
        if not metric_views:
            return None
        results_dir = self.input_data_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = results_dir / f"view{timestamp}.parquet"
        pl.scan_parquet([v.file for v in metric_views]).sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        for metric_view in metric_views:
            del metric_view
        logging.info(f"Results merged into {out_path}")
        return out_path

    def write_metric_structure_table(self, metric_structure_table: pl.DataFrame, metric_id: str) -> Path:
        metric_structure_dir = self.input_data_path / "views" / "metric_structure"
        metric_structure_dir.mkdir(parents=True, exist_ok=True)
        metric_structure_path = metric_structure_dir / f"{metric_id}.parquet"
        metric_structure_table.write_parquet(
            metric_structure_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
            use_pyarrow=True,
            pyarrow_options={"data_page_version": "2.0"},
        )
        return metric_structure_path


@dataclass
class MergedView:
    """Final merged view written to the results directory."""

    file: Path | None

    @classmethod
    def merge_views(cls, metric_views: list[MetricView], writer: "Writer") -> "MergedView":
        return cls(file=writer.merge_results(metric_views))
