# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import tempfile
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.metric_view import TemporalMetricView


class TermsAggregator:
    def __init__(self) -> None:
        self._root_dir = Path(tempfile.mkdtemp())
        self._metric_view_dir = self._root_dir / "views" / "metric_view"
        self._metric_view_dir.mkdir(parents=True, exist_ok=True)

    def run(self, structured_simulation_table: pl.LazyFrame, metric: Metric) -> TemporalMetricView:
        # # 2B group by
        logging.info(f"[{metric.id}] Aggregating terms with operator {metric.terms_operator.value}")
        value_agg = pl.col("value").sum() if metric.terms_operator == AggregOperatorType.SUM else pl.col("value").mean()
        metric_view = (
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
        out_path = self._metric_view_dir / f"{metric.id}.parquet"
        metric_view.sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        logging.info(f"[{metric.id}] Terms aggregation written to {out_path}")
        return TemporalMetricView(out_path)

    def __del__(self) -> None:
        rmtree(self._root_dir, ignore_errors=True)
