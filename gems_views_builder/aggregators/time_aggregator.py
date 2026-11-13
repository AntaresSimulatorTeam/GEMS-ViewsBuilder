# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import atexit
import logging
import tempfile
import time
import uuid
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.common import sink_to_parquet
from gems_views_builder.input.catalog import AggregOperatorType, Metric
from gems_views_builder.input.view_config import TimeGranularity
from gems_views_builder.metric_view import MetricView, TemporalMetricView

# # Polars truncate windows are strings like "1h", "1d", "1w", "1mo", "1y".
TRUNCATE_WINDOWS: dict[TimeGranularity, str] = {
    TimeGranularity.HOUR: "1h",
    TimeGranularity.DAY: "1d",
    TimeGranularity.WEEK: "1w",
    TimeGranularity.MONTH: "1mo",
    TimeGranularity.YEAR: "1y",
}


class TimeAggregator:
    def __init__(self, time_granularity: TimeGranularity) -> None:
        self._time_granularity = time_granularity
        self._root_dir = Path(tempfile.mkdtemp())
        self._temporal_aggregation_dir = self._root_dir / "views" / "temporal_aggregation"
        self._temporal_aggregation_dir.mkdir(parents=True, exist_ok=True)
        # # The temporal aggregation files are the pipeline's final output: they must
        # # outlive this aggregator because accumulate_on_disk() reads them after build() returns and
        # # the ViewBuilder (and this aggregator) has already been garbage collected.
        # # Cleaning up in __del__ would delete them too early, so we defer removal of
        # # the whole temp tree until interpreter exit instead.
        atexit.register(rmtree, self._root_dir, True)

    def run(self, metric_view: MetricView, metric: Metric, locations: list[str] | None = None) -> TemporalMetricView:
        """
        Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        logging.info(f"[{metric.id}] Aggregating temporally with operator {metric.time_operator.value}")
        # # Safest and most elegant option to remove part counter
        # # https://www.researchgate.net/publication/215758035_A_Universally_Unique_IDentifier_UUID_URN_Namespace
        file_path = (
            self._temporal_aggregation_dir / f"{self._time_granularity.value}_{metric.id}_{uuid.uuid4()}.parquet"
        )
        aggregate_time(metric_view.persistence_path, file_path, self._time_granularity, metric.time_operator, locations)
        logg_write(metric, file_path)
        return TemporalMetricView(persistence_path=file_path)


def aggregate_time(
    input_path: Path,
    output_path: Path,
    time_granularity: TimeGranularity,
    time_operator: AggregOperatorType,
    locations: list[str] | None = None,
) -> float:
    """Aggregate a terms-aggregated metric view to ``time_granularity``; return the elapsed seconds.

    Only rows whose location is in ``locations`` are kept, when given. Takes file paths, not
    metric views: a view deletes its file when garbage-collected, so worker threads must not own one.
    """
    start = time.perf_counter()
    lazy_metric_view = pl.scan_parquet(input_path)
    if locations:
        lazy_metric_view = lazy_metric_view.filter(pl.col("metric_location").is_in(locations))
    view = (
        lazy_metric_view.with_columns(date_column_into_time_granularity(time_granularity))
        .group_by(
            [
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "scenario_id",
                "view_date",
            ]
        )
        .agg(aggregate_into_column(time_operator, "granular_metric_value"))
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
    sink_to_parquet(view, output_path)
    return time.perf_counter() - start


def logg_write(metric: Metric, file_path: Path) -> None:
    logging.info(f"[{metric.id}] Temporal aggregation written to {file_path}")


def date_column_into_time_granularity(time_granularity: TimeGranularity) -> pl.Expr:
    return pl.col("granular_date").dt.truncate(TRUNCATE_WINDOWS[time_granularity]).alias("view_date")


def aggregate_into_column(agg_operator: AggregOperatorType, column_name: str) -> pl.Expr:
    return (pl.col(column_name).sum() if agg_operator == AggregOperatorType.SUM else pl.col(column_name).mean()).alias(
        "metric_value"
    )
