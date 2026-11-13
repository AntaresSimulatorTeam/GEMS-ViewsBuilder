# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from abc import ABC, abstractmethod

import polars as pl

from gems_views_builder.metric_view import MetricView

class ColumnsAdditionBase(ABC):
    @abstractmethod
    def run(self, metric_view: MetricView) -> MetricView:
        pass


class ScenarioColumnsAddition(ColumnsAdditionBase):
    def run(self, metric_view: MetricView) -> MetricView:
        logging.info("Aggregating across scenarios (exp/std/min/max)")
        lazyframe = metric_view.lazy_data_frame().with_columns(
            [
                pl.lit(None, dtype=pl.Int64).alias("scenario_id"),
                pl.lit(True, dtype=pl.Boolean).alias("scenario_aggregation"),
            ]
        )
        return MetricView(lazyframe=lazyframe,
                          view_config_id=metric_view.view_config_id,
                          aggregation_pattern_id=metric_view.aggregation_pattern_id)


class NoScenarioColumnsAddition(ColumnsAdditionBase):
    def run(self, metric_view: MetricView) -> MetricView:
        lazyframe = metric_view.lazy_data_frame().with_columns(
            [
                pl.lit(False, dtype=pl.Boolean).alias("scenario_aggregation"),
                pl.lit(None, dtype=pl.Utf8).alias("scenario_stat"),
            ]
        )
        return MetricView(lazyframe=lazyframe,
                          view_config_id=metric_view.view_config_id,
                          aggregation_pattern_id=metric_view.aggregation_pattern_id)


def make_columns_additioner(scenario: bool) -> ColumnsAdditionBase:
    if scenario:
        return ScenarioColumnsAddition()
    return NoScenarioColumnsAddition()


class ColumnsAdditioner:
    def __init__(self, scenario: bool):
        self.column_additioner = make_columns_additioner(scenario)

    def run(self, metric_view: MetricView) -> MetricView:
        return self.column_additioner.run(metric_view)
