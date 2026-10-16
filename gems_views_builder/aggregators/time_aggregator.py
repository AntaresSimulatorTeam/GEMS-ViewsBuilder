# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging

import polars as pl

from gems_views_builder.aggregators.base_persisting_view import CreatePersistingView
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import MetricView

# # Polars truncate windows are strings like "1h", "1d", "1w", "1mo", "1y".
TRUNCATE_WINDOWS: dict[TimeGranularity, str] = {
    TimeGranularity.HOUR: "1h",
    TimeGranularity.DAY: "1d",
    TimeGranularity.WEEK: "1w",
    TimeGranularity.MONTH: "1mo",
    TimeGranularity.YEAR: "1y",
}


def cache_view_by_time_granularity(cls: type["TimeAggregator"]) -> type["TimeAggregator"]:
    """Class decorator: returns a new class wrapping `cls`, whose run() caches the MetricView
    generated for each time_granularity (class-wide), delegating actual computation to the
    original run() via super(). Several aggregation patterns sharing the same time_granularity
    thus reuse the same generated view.
    """

    class _CachingAggregator(cls):
        views_storage: dict[TimeGranularity, MetricView] = {}

        def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
            if self._time_granularity not in self.views_storage:
                self.views_storage[self._time_granularity] = super().run(metric_view, metric)
            return self.views_storage[self._time_granularity]

    _CachingAggregator.__name__ = cls.__name__
    _CachingAggregator.__qualname__ = cls.__qualname__
    return _CachingAggregator


@cache_view_by_time_granularity
class TimeAggregator(CreatePersistingView):
    _subdirectory = "time_aggregation"

    def __init__(self, time_granularity: TimeGranularity) -> None:
        self._time_granularity = time_granularity
        super().__init__()

    def _output_time_granularity(self, metric_view: MetricView) -> TimeGranularity:
        return self._time_granularity

    def _build_lazy_frame(self, metric_view: MetricView, metric: Metric) -> pl.LazyFrame:
        """
        Step 2.C from POC[time aggregation]: Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        logging.info(f"[{metric.id}] Aggregating temporally with operator {metric.time_operator.value}")
        aggreg_op = aggregate_into_column(metric.time_operator, "granular_metric_value")
        date_column = date_column_into_time_granularity(self._time_granularity)

        return (
            metric_view.lazy_data_frame()
            .with_columns(date_column)
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "scenario_id",
                    "view_date",
                ]
            )
            .agg(aggreg_op)
            .select(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "view_date",
                    "scenario_id",
                    pl.col("metric_value").cast(pl.Float64),
                ]
            )
        )


def date_column_into_time_granularity(time_granularity: TimeGranularity) -> pl.Expr:
    return pl.col("granular_date").dt.truncate(TRUNCATE_WINDOWS[time_granularity]).alias("view_date")


def aggregate_into_column(agg_operator: AggregOperatorType, column_name: str) -> pl.Expr:
    return (pl.col(column_name).sum() if agg_operator == AggregOperatorType.SUM else pl.col(column_name).mean()).alias(
        "metric_value"
    )
