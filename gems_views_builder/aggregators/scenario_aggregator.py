# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from abc import ABC, abstractmethod
from enum import Enum

import polars as pl

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

class ScenarioOperator(ABC):
    @abstractmethod
    def run(self, metric_view: MetricView) -> MetricView:
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
        )
        return MetricView(lazyframe=lazyframe,
                          view_config_id=metric_view.view_config_id,
                          aggregation_pattern_id=metric_view.aggregation_pattern_id)


class NullScenarioAggregation(ScenarioOperator):
    def run(self, metric_view: MetricView) -> MetricView:
        logging.info("Scenario aggregation disabled, preserving per-scenario rows")
        return metric_view


def make_scenario_operator(scenario: bool) -> ScenarioOperator:
    if scenario:
        return ScenarioAggregation()
    return NullScenarioAggregation()


class ScenarioAggregator:
    def __init__(self, scenario: bool):
        self.scenario_operator = make_scenario_operator(scenario)

    def run(self, metric_view: MetricView) -> MetricView:
        return self.scenario_operator.run(metric_view)
