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
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView


class Operator(Enum):
    EXP = "exp"
    STD = "std"
    MIN = "min"
    MAX = "max"


# expectation (exp) == mean
AGGREGATION_OPERATORS = [
    pl.col("metric_value").mean().alias(Operator.EXP.value),
    pl.col("metric_value").std(ddof=0).alias(Operator.STD.value),
    pl.col("metric_value").min().alias(Operator.MIN.value),
    pl.col("metric_value").max().alias(Operator.MAX.value),
]


@dataclass
class ScenarioPatternOperator(ABC):
    @abstractmethod
    def run(self, temporal_metric_view: MetricView, tmp_path: Path) -> None:
        pass


class ScenarioPatternAggregation(ScenarioPatternOperator):
    def run(self, temporal_metric_view: MetricView, tmp_path: Path) -> None:
        logging.info("Aggregating across scenarios (exp/std/min/max)")
        index_columns = ["metric_id", "metric_location", "breakdown_properties", "view_date"]
        view = (
            pl.scan_parquet(temporal_metric_view.persistence_path)
            .group_by(index_columns)
            .agg(AGGREGATION_OPERATORS)
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
        )
        view.sink_parquet(
            tmp_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )


class ScenarioPatternColumnsAddition(ScenarioPatternOperator):
    def run(self, temporal_metric_view: MetricView, tmp_path: Path) -> None:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
        view = pl.scan_parquet(temporal_metric_view.persistence_path).with_columns(
            [
                pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
            ]
        )
        view.sink_parquet(
            tmp_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )


def make_scenario_operator(scenario_aggregation: bool) -> ScenarioPatternOperator:
    return ScenarioPatternAggregation() if scenario_aggregation else ScenarioPatternColumnsAddition()


@dataclass
class ScenarioAggregator:
    scenario_pattern_operator: ScenarioPatternOperator

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        tmp_path: str | None = None
        try:
            file_descriptor, tmp_path = tempfile.mkstemp(suffix=".parquet")
            os.close(file_descriptor)
            self.scenario_pattern_operator.run(metric_view, Path(tmp_path))
            os.replace(tmp_path, metric_view.persistence_path)
        except Exception:
            if tmp_path is not None:
                os.remove(tmp_path)
            raise
        logging.info(f"[{metric.id}] Scenario view written to {metric_view.persistence_path}")
        return metric_view
