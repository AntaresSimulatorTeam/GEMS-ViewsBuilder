# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import polars as pl

from gems_views_builder.aggregators.aggregator_operator import AggregationOperation
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.metric_view import MetricView, sink


class TermsAggregator(AggregationOperation):
    def __init__(self) -> None:
        super().__init__()

    def run(self, structured_simulation_table: pl.LazyFrame, metric: Metric) -> MetricView:
        # # 2B group by
        logging.info(f"[{metric.id}] Aggregating terms with operator {metric.terms_operator.value}")
        value_agg = pl.col("value").sum() if metric.terms_operator == AggregOperatorType.SUM else pl.col("value").mean()
        view = (
            structured_simulation_table.with_columns(pl.col("scenario_index").alias("scenario_id"))
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
                    # take first non-null value of group
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
        out_path = self._root_dir / f"{metric.id}.parquet"
        sink(view, out_path)
        logg_write(metric, out_path)
        return MetricView(out_path)


def logg_write(metric: Metric, file_path: Path) -> None:
    logging.info(f"[{metric.id}] Terms aggregation written to {file_path}")
