# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.input.catalog import Metric, TimeOperator
from gems_views_builder.input.view_config import TimeAggregation
from gems_views_builder.metric_view import MetricView

# # Polars truncate windows are strings like "1h", "1d", "1w", "1mo", "1y".
TRUNCATE_WINDOWS: dict[TimeAggregation, str] = {
    TimeAggregation.HOUR: "1h",
    TimeAggregation.DAY: "1d",
    TimeAggregation.WEEK: "1w",
    TimeAggregation.MONTH: "1mo",
    TimeAggregation.YEAR: "1y",
}


class TimeAggregator:
    def __init__(self, time_aggregation: TimeAggregation | None) -> None:
        self._time_aggregation = time_aggregation
        self._root_dir = Path(tempfile.mkdtemp())
        self._temporal_aggregation_dir = self._root_dir / "views" / "temporal_aggregation"
        self._temporal_aggregation_dir.mkdir(parents=True, exist_ok=True)
        self._part_counter = 0
        # # The temporal aggregation files are the pipeline's final output: they must
        # # outlive this aggregator because accumulate_on_disk() reads them after build() returns and
        # # the ViewBuilder (and this aggregator) has already been garbage collected.
        # # Cleaning up in __del__ would delete them too early, so we defer removal of
        # # the whole temp tree until interpreter exit instead.
        atexit.register(rmtree, self._root_dir, True)

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        """
        Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        logging.info(f"[{metric.id}] Aggregating temporally with operator {metric.time_operator.value}")
        lazy_metric_view = pl.scan_parquet(metric_view.persistence_path)

        agg_expr = time_aggregation_expression(metric.time_operator)
        date_expr = granular_date_expression(self._time_aggregation)

        view = (
            lazy_metric_view.with_columns(date_expr)
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "scenario_id",
                    "view_date",
                ]
            )
            .agg(agg_expr)
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
        # # Business view is meant to be created once, then appended to on future runs.
        # # We implement this by writing a new parquet "part" file each time.
        # # If you wonder why part_counter this is because if user reference same metric into multiple catalogs
        # # we need to have different file names.
        out_path = self._temporal_aggregation_dir / f"{metric.id}-{self._part_counter}.parquet"
        self._part_counter += 1
        view.sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        logging.info(f"[{metric.id}] Temporal aggregation written to {out_path}")
        return MetricView(out_path)


def granular_date_expression(time_aggregation: TimeAggregation | None) -> pl.Expr:
    if time_aggregation:
        return pl.col("granular_date").dt.truncate(TRUNCATE_WINDOWS[time_aggregation]).alias("view_date")
    return pl.col("granular_date").alias("view_date")


def time_aggregation_expression(time_operator: TimeOperator) -> pl.Expr:
    return (
        pl.col("granular_metric_value").sum()
        if time_operator == TimeOperator.SUM
        else pl.col("granular_metric_value").mean()
    ).alias("metric_value")
