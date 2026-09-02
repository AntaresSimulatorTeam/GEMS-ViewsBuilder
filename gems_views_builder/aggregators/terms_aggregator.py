# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import polars as pl

from gems_views_builder.aggregators.aggregation_operator import AggregationOperator
from gems_views_builder.input.catalog import AggregOperatorType, Metric


class TermsAggregator(AggregationOperator):
    def _aggregate(self, frame: pl.LazyFrame, metric: Metric) -> pl.LazyFrame:
        logging.info(f"[{metric.id}] Aggregating terms with operator {metric.terms_operator.value}")
        value_agg = pl.col("value").sum() if metric.terms_operator == AggregOperatorType.SUM else pl.col("value").mean()
        return (
            frame.with_columns(pl.col("scenario_index").alias("scenario_id"))
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "absolute_time_index",
                    "scenario_id",
                ]
            )
            .agg(
                [
                    value_agg.alias("granular_metric_value"),
                    pl.col("granular_date").drop_nulls().first(),
                ]
            )
            .select(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "absolute_time_index",
                    "scenario_id",
                    "granular_metric_value",
                    "granular_date",
                ]
            )
        )

    def _log_write(self, metric: Metric, path: Path) -> None:
        logging.info(f"[{metric.id}] Terms aggregation written to {path}")
