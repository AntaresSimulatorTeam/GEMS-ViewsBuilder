# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

import polars as pl

from gems_views_builder.input.view_config import AggregationPattern
from gems_views_builder.metric_view import TemporalMetricView, sink_to_parquet
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
    def run(self, temporal_metric_view: TemporalMetricView) -> pl.LazyFrame:
        pass


class ScenarioAggregation(ScenarioOperator):
    def run(self, temporal_metric_view: TemporalMetricView) -> pl.LazyFrame:
        logging.info("Aggregating across scenarios (exp/std/min/max)")
        index_columns = ["metric_id", "metric_location", "breakdown_properties", "view_date"]
        return (
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


class ScenarioColumnsAddition(ScenarioOperator):
    def run(self, temporal_metric_view: TemporalMetricView) -> pl.LazyFrame:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
        return pl.scan_parquet(temporal_metric_view.persistence_path).with_columns(
            [
                pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
            ]
        )


def make_scenario_operator(scenario_aggregation: bool) -> ScenarioOperator:
    return ScenarioAggregation() if scenario_aggregation else ScenarioColumnsAddition()


"""
Indeed spatial filter is part of the pattern
Funtional design, why we're merging this 2 operations == We want to avoid multiple read/write operations
"""


class ScenarioAggregator:
    def __init__(self, aggregation_pattern: AggregationPattern):
        self.scenario_operator = make_scenario_operator(aggregation_pattern.scenario)
        self.spatial_filter = SpatialFilter(aggregation_pattern.spatial_filter)

    def run(self, metric_view: TemporalMetricView) -> TemporalMetricView:
        new_path = metric_view.persistence_path.parent / f"{uuid4()}.parquet"
        view = self.scenario_operator.run(metric_view)
        view = apply_spatial_filter(view, self.spatial_filter)
        sink_to_parquet(view, new_path)
        logging.info(f"Scenario view written to {new_path}")
        return TemporalMetricView(new_path, metric_view.time_granularity)
