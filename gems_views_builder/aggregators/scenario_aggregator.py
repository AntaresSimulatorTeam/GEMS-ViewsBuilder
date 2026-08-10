# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.metric_view import MetricView


class Operator(Enum):
    EXP = "exp"
    STD = "std"
    MIN = "min"
    MAX = "max"


# expectation (exp) == mean
SCENARIO_AGG_EXPRS = [
    pl.col("metric_value").mean().alias(Operator.EXP.value),
    pl.col("metric_value").std(ddof=0).alias(Operator.STD.value),
    pl.col("metric_value").min().alias(Operator.MIN.value),
    pl.col("metric_value").max().alias(Operator.MAX.value),
]


@dataclass
class ScenarioOperator(ABC):
    @abstractmethod
    def run(self, temporal_metric_view: MetricView, tmp_path: Path) -> None:
        pass


class ScenarioAggregation(ScenarioOperator):
    def run(self, temporal_metric_view: MetricView, tmp_path: Path) -> None:
        logging.info("Aggregating across scenarios (exp/std/min/max)")
        index_columns = ["metric_id", "metric_location", "breakdown_properties", "view_date"]
        (
            pl.scan_parquet(temporal_metric_view.persistence_path)
            .group_by(index_columns)
            .agg(SCENARIO_AGG_EXPRS)
            .unpivot(
                on=[op.value for op in Operator],
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


class ScenarioColumnsAddition(ScenarioOperator):
    def run(self, temporal_metric_view: MetricView, tmp_path: Path) -> None:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
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


def make_scenario_operator(scenario_aggregation: bool) -> ScenarioOperator:
    return ScenarioAggregation() if scenario_aggregation else ScenarioColumnsAddition()


def to_scenario_view(temporal_metric_view: MetricView, scenario_operator: ScenarioOperator) -> None:
    file_descriptor, tmp_path = tempfile.mkstemp(suffix=".parquet")
    os.close(file_descriptor)

    scenario_operator.run(temporal_metric_view, Path(tmp_path))

    os.replace(tmp_path, temporal_metric_view.persistence_path)
    logging.info(f"Scenario view written to {temporal_metric_view.persistence_path}")
