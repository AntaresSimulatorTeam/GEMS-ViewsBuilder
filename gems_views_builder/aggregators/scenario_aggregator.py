# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

import polars as pl

from gems_views_builder.input.view_config import AggregationPattern
from gems_views_builder.metric_view import MetricView, PersistentMetricView, RamMetricView
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
    def run(self, metric_view: MetricView) -> pl.LazyFrame:
        pass


class ScenarioAggregation(ScenarioOperator):
    def run(self, metric_view: MetricView) -> MetricView:
        logging.info("Aggregating across scenarios (exp/std/min/max)")
        index_columns = ["metric_id", "metric_location", "breakdown_properties", "view_date"]
        lazyframe = (
            metric_view.lazy_data_frame()
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
        return RamMetricView(lazyframe=lazyframe, time_granularity=metric_view.time_granularity)

class ScenarioColumnsAddition(ScenarioOperator):
    def run(self, metric_view: MetricView) -> MetricView:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
        lazyframe = metric_view.lazy_data_frame().with_columns(
            [
                pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
            ]
        )
        return RamMetricView(lazyframe=lazyframe, time_granularity=metric_view.time_granularity)


def make_scenario_operator(scenario_aggregation: bool) -> ScenarioOperator:
    return ScenarioAggregation() if scenario_aggregation else ScenarioColumnsAddition()


class ScenarioAggregator:
    def __init__(self, aggregation_pattern: AggregationPattern):
        self.scenario_operator = make_scenario_operator(aggregation_pattern.scenario)
        self.spatial_filter = SpatialFilter(aggregation_pattern.spatial_filter)

    def run(self, metric_view: MetricView) -> MetricView:
        new_path = metric_view.persistence_path.parent / f"{uuid4()}.parquet"
        view = self.scenario_operator.run(metric_view)
        view = apply_spatial_filter(view, self.spatial_filter)
        logging.info(f"Scenario view written to {new_path}")
        return PersistentMetricView(metric_view.time_granularity, view=view, persistence_path=new_path)
