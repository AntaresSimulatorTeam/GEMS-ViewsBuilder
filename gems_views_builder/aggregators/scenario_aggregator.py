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

from gems_views_builder.common import sink_to_parquet
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import TemporalMetricView


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
class ScenarioOperator(ABC):
    @abstractmethod
    def run(self, temporal_metric_view: TemporalMetricView, tmp_path: Path) -> None:
        pass


class ScenarioAggregation(ScenarioOperator):
    def run(self, temporal_metric_view: TemporalMetricView, tmp_path: Path) -> None:
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
        sink_to_parquet(view, tmp_path)


class ScenarioColumnsAddition(ScenarioOperator):
    def run(self, temporal_metric_view: TemporalMetricView, tmp_path: Path) -> None:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
        view = pl.scan_parquet(temporal_metric_view.persistence_path).with_columns(
            [
                pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
            ]
        )
        sink_to_parquet(view, tmp_path)


def make_scenario_operator(scenario_aggregation: bool) -> ScenarioOperator:
    return ScenarioAggregation() if scenario_aggregation else ScenarioColumnsAddition()


@dataclass
class ScenarioAggregator:
    scenario_operator: ScenarioOperator

    def run(self, metric_view: TemporalMetricView, metric: Metric) -> TemporalMetricView:
        try:
            file_descriptor, tmp_path = tempfile.mkstemp(suffix=".parquet")
            os.close(file_descriptor)

            self.scenario_operator.run(metric_view, Path(tmp_path))

            os.replace(src=tmp_path, dst=metric_view.persistence_path)
        except Exception:
            os.remove(tmp_path)
        logg_write(metric, metric_view.persistence_path)
        return metric_view


def logg_write(metric: Metric, file_path: Path) -> None:
    logging.info(f"[{metric.id}] Scenario view written to {file_path}")
