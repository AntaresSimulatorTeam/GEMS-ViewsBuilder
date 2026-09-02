# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import polars as pl

from gems_views_builder.aggregators.aggregation_operator import AggregationOperator
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import MetricView, TemporalMetricView

# Polars truncate windows are strings like "1h", "1d", "1w", "1mo", "1y".
TRUNCATE_WINDOWS: dict[TimeGranularity, str] = {
    TimeGranularity.HOUR: "1h",
    TimeGranularity.DAY: "1d",
    TimeGranularity.WEEK: "1w",
    TimeGranularity.MONTH: "1mo",
    TimeGranularity.YEAR: "1y",
}


class TimeAggregator(AggregationOperator):
    def __init__(self, time_granularity: TimeGranularity) -> None:
        super().__init__()
        self._time_granularity = time_granularity

    def _aggregate(self, frame: pl.LazyFrame, metric: Metric) -> pl.LazyFrame:
        """
        Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        logging.info(f"[{metric.id}] Aggregating temporally with operator {metric.time_operator.value}")
        aggreg_op = aggregate_into_column(metric.time_operator, "granular_metric_value")
        date_column = date_column_into_time_granularity(self._time_granularity)
        return (
            frame.with_columns(date_column)
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

    def _to_metric_view(self, path: Path, source: MetricView) -> MetricView:
        return TemporalMetricView(path, self._time_granularity)

    def _log_write(self, metric: Metric, path: Path) -> None:
        logging.info(f"[{metric.id}] Temporal aggregation written to {path}")


def date_column_into_time_granularity(time_granularity: TimeGranularity) -> pl.Expr:
    return pl.col("granular_date").dt.truncate(TRUNCATE_WINDOWS[time_granularity]).alias("view_date")


def aggregate_into_column(agg_operator: AggregOperatorType, column_name: str) -> pl.Expr:
    return (pl.col(column_name).sum() if agg_operator == AggregOperatorType.SUM else pl.col(column_name).mean()).alias(
        "metric_value"
    )
