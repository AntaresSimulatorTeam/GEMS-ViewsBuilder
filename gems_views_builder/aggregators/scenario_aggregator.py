# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import polars as pl

from gems_views_builder.aggregators.aggregation_operator import AggregationOperator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView, TemporalMetricView
from gems_views_builder.spatial_filter import SpatialFilter, apply_spatial_filter


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
    def run(self, frame: pl.LazyFrame) -> pl.LazyFrame:
        pass


class ScenarioAggregation(ScenarioOperator):
    def run(self, frame: pl.LazyFrame) -> pl.LazyFrame:
        logging.info("Aggregating across scenarios (exp/std/min/max)")
        index_columns = ["metric_id", "metric_location", "breakdown_properties", "view_date"]
        return (
            frame.group_by(index_columns)
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


class ScenarioColumnsAddition(ScenarioOperator):
    def run(self, frame: pl.LazyFrame) -> pl.LazyFrame:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
        return frame.with_columns(
            [
                pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
            ]
        )


def make_scenario_operator(scenario_aggregation: bool) -> ScenarioOperator:
    return ScenarioAggregation() if scenario_aggregation else ScenarioColumnsAddition()


class ScenarioAggregator(AggregationOperator):
    def __init__(self, scenario: bool, spatial_filter: list[str] | None = None) -> None:
        super().__init__()
        self.scenario_operator = make_scenario_operator(scenario)
        self.spatial_filter = SpatialFilter(spatial_filter)

    def _aggregate(self, frame: pl.LazyFrame, metric: Metric) -> pl.LazyFrame:
        return apply_spatial_filter(self.scenario_operator.run(frame), self.spatial_filter)

    def _to_metric_view(self, path: Path, source: MetricView) -> MetricView:
        if isinstance(source, TemporalMetricView):
            return TemporalMetricView(path, source.time_granularity)
        return MetricView(path)

    def _log_write(self, metric: Metric, path: Path) -> None:
        logging.info(f"Scenario view written to {path}")
