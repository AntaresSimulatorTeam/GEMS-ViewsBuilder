import logging
import tempfile
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.input.catalog import Metric, TimeOperator
from gems_views_builder.metric_view import MetricView


class TimeAggregator:
    def __init__(self) -> None:
        self._temporal_aggregation_dir = Path(tempfile.mkdtemp()) / "views" / "temporal_aggregation"
        self._temporal_aggregation_dir.mkdir(parents=True, exist_ok=True)
        self._part_counter = 0

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        """
        Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        logging.info(f"[{metric.id}] Aggregating temporally with operator {metric.time_operator.value}")
        lazy_metric_view = pl.scan_parquet(metric_view.file_path)
        time_agg = (
            pl.col("granular_metric_value").sum()
            if metric.time_operator == TimeOperator.SUM
            else pl.col("granular_metric_value").mean()
        ).alias("metric_value")
        view_date_expr = pl.col("granular_date").alias("view_date")
        view = (
            lazy_metric_view.with_columns(view_date_expr)
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "scenario",
                    "view_date",
                ]
            )
            .agg(time_agg)
            .select(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "view_date",
                    "scenario",
                    "metric_value",
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

    def __del__(self) -> None:
        # # This is also safe because time aggregator is class member so it will be garbage collected when pipeline is finished
        rmtree(self._temporal_aggregation_dir, ignore_errors=True)
