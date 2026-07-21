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
import os
import tempfile
from dataclasses import dataclass
from enum import Enum

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.metric_view import MetricView


class ScenarioOperator(Enum):
    EXP = "exp"
    STD = "std"
    MIN = "min"
    MAX = "max"


# expectation (exp) == mean
SCENARIO_AGG_EXPRS = [
    pl.col("metric_value").mean().alias(ScenarioOperator.EXP.value),
    pl.col("metric_value").std(ddof=0).alias(ScenarioOperator.STD.value),
    pl.col("metric_value").min().alias(ScenarioOperator.MIN.value),
    pl.col("metric_value").max().alias(ScenarioOperator.MAX.value),
]


@dataclass
class ScenarioAggregator:
    scenario_aggregation: bool

    def run(self, temporal_metric_view: MetricView) -> None:
        file_descriptor, tmp_path = tempfile.mkstemp(suffix=".parquet")
        os.close(file_descriptor)

        if not self.scenario_aggregation:
            logging.info("Scenario aggregation disabled; preserving per-scenario rows")
            (
                pl.scan_parquet(temporal_metric_view.persistence_path)
                .with_columns(
                    [
                        pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                        pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
                    ]
                )
                .sink_parquet(
                    tmp_path,
                    compression=PARQUET_COMPRESSION,
                    compression_level=PARQUET_COMPRESSION_LEVEL,
                    row_group_size=PARQUET_ROW_GROUP_SIZE,
                )
            )
        else:
            logging.info("Aggregating across scenarios (exp/std/min/max)")
            index_columns = ["metric_id", "metric_location", "breakdown_properties", "view_date"]
            (
                pl.scan_parquet(temporal_metric_view.persistence_path)
                .group_by(index_columns)
                .agg(SCENARIO_AGG_EXPRS)
                .unpivot(
                    on=[op.value for op in ScenarioOperator],
                    index=index_columns,
                    variable_name="scenario_stat",
                    value_name="metric_value",
                )
                .with_columns(
                    [
                        pl.lit(None, dtype=pl.Int64).alias("scenario_id"),
                        pl.lit(True, dtype=pl.Boolean).alias("scenario_aggregation"),
                    ]
                )
                .sink_parquet(
                    tmp_path,
                    compression=PARQUET_COMPRESSION,
                    compression_level=PARQUET_COMPRESSION_LEVEL,
                    row_group_size=PARQUET_ROW_GROUP_SIZE,
                )
            )

        os.replace(tmp_path, temporal_metric_view.persistence_path)
        logging.info(f"Scenario aggregation written to {temporal_metric_view.persistence_path}")
