import logging
from pathlib import Path

import polars as pl

from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE


class Aggregator:
    def __init__(self, output_data_path: Path) -> None:
        self.output_data_path = output_data_path
        self._part_counter = 0
        self._temporal_aggregation_dir = self._create_temporal_aggregation_directory()
        self._metric_view_dir = self._create_metric_view_directory()

    def _create_temporal_aggregation_directory(self) -> Path:
        temporal_aggregation_dir = self.output_data_path / "temporal_aggregation"
        temporal_aggregation_dir.mkdir(parents=True, exist_ok=True)
        return self.output_data_path / "temporal_aggregation"

    def _create_metric_view_directory(self) -> Path:
        metric_view_dir = self.output_data_path / "views" / "metric_view"
        metric_view_dir.mkdir(parents=True, exist_ok=True)
        return metric_view_dir

    def aggregate_metric_terms(
        self, joined_dataframe: pl.LazyFrame, metric_term_operator: TermsOperator, metric_id: str
    ) -> Path:
        """
        Step 2.B from POC[Computing the metric]: Right join TIME_FILTERED_SIMULATION_TABLE with METRIC_STRUCTURE_TABLE on component and output
        """
        logging.info(f"[{metric_id}] Aggregating terms with operator {metric_term_operator.value}")
        value_agg = pl.col("value").sum() if metric_term_operator == TermsOperator.SUM else pl.col("value").mean()
        metric_view = (
            joined_dataframe.with_columns(pl.col("scenario_index").alias("scenario"))
            .group_by(
                [
                    "metric_id",
                    "metric_location",
                    "breakdown_properties",
                    "absolute_time_index",
                    "scenario",
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
                    "scenario",
                    "granular_metric_value",
                    "granular_date",
                ]
            )
        )
        out_path = self._metric_view_dir / f"{metric_id}.parquet"
        metric_view.sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        logging.info(f"[{metric_id}] Terms aggregation written to {out_path}")
        return out_path

    def aggregate_metric_temporally(
        self, metric_view_parquet_path: Path, metric_time_operator: TimeOperator, metric_id: str
    ) -> Path:
        """
        Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
        """
        logging.info(f"[{metric_id}] Aggregating temporally with operator {metric_time_operator.value}")
        metric_view = pl.scan_parquet(metric_view_parquet_path)
        time_agg = (
            pl.col("granular_metric_value").sum()
            if metric_time_operator == TimeOperator.SUM
            else pl.col("granular_metric_value").mean()
        ).alias("metric_value")
        view_date_expr = pl.col("granular_date").alias("view_date")
        view = (
            metric_view.with_columns(view_date_expr)
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
        # Business view is meant to be created once, then appended to on future runs.
        # We implement this by writing a new parquet "part" file each time.
        out_path = self._temporal_aggregation_dir / f"{metric_id}-{self._part_counter}.parquet"
        self._part_counter += 1
        view.sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        logging.info(f"[{metric_id}] Temporal aggregation written to {out_path}")
        return out_path
