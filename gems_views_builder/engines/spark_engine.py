# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""PySpark backend engine.

Requirements:
  pip install pyspark

Notes:
  - Spark writes parquet to *directories*, not single files.  This engine uses
    coalesce(1) and moves the single part file to the requested output_path so
    the rest of the pipeline can treat all backends uniformly.
  - A single SparkSession is created lazily and reused for the lifetime of the
    engine instance.  Shut it down explicitly with engine.stop() if needed.
  - Compression is set via Spark config; zstd is supported in Spark 3.2+.
"""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.engines.base import DataEngine

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


class SparkEngine(DataEngine):
    """Data engine backed by PySpark DataFrames."""

    def __init__(self) -> None:
        self._spark: "SparkSession | None" = None

    @property
    def spark(self) -> "SparkSession":
        if self._spark is None:
            try:
                from pyspark.sql import SparkSession

                self._spark = (
                    SparkSession.builder.appName("GEMS-ViewsBuilder")
                    .config("spark.sql.parquet.compression.codec", "zstd")
                    # Write timestamps without timezone info (matches polars Datetime dtype).
                    .config("spark.sql.parquet.outputTimestampType", "TIMESTAMP_MICROS")
                    # Force UTC so CSV datetime strings are not shifted by the
                    # JVM's local timezone when parsed into TimestampType.
                    .config("spark.sql.session.timeZone", "UTC")
                    .getOrCreate()
                )
            except ImportError as exc:
                raise ImportError(
                    "PySpark is required for the spark backend: pip install pyspark"
                ) from exc
        return self._spark

    def stop(self) -> None:
        """Stop the underlying SparkSession (call when benchmarking is done)."""
        if self._spark is not None:
            self._spark.stop()
            self._spark = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_single_parquet(self, df: "DataFrame", output_path: Path) -> None:
        """Write a Spark DataFrame as a single parquet file.

        Spark natively writes to a directory; this helper coalesces to one
        partition, writes to a temp directory, and moves the part file to the
        requested output_path.
        """
        tmp_dir = output_path.parent / f"_tmp_{output_path.name}"
        df.coalesce(1).write.mode("overwrite").parquet(str(tmp_dir))
        part_file = next(tmp_dir.glob("part-*.parquet"))
        shutil.copy2(part_file, output_path)
        shutil.rmtree(tmp_dir)

    def _read_parquet(self, path: Path) -> "DataFrame":
        return self.spark.read.parquet(str(path))

    def _read_csv(self, path: Path) -> "DataFrame":
        return (
            self.spark.read.option("header", "true")
            .option("inferSchema", "true")
            .csv(str(path))
        )

    # ------------------------------------------------------------------
    # DataEngine interface
    # ------------------------------------------------------------------

    def filter_simulation_table(
        self,
        simulation_path: Path,
        calendar_path: Path,
        output_path: Path,
    ) -> None:
        from pyspark.sql import functions as F

        sim = self._read_parquet(simulation_path)
        cal = self._read_csv(calendar_path).withColumnRenamed("block", "block_cal")

        # Time-dependent rows: inner join + block-match filter.
        time_dep = (
            sim.join(cal, on="absolute_time_index", how="inner")
            .filter(F.col("block") == F.col("block_cal"))
            .drop("block_cal")
        )

        # Reflect granular_date type from time_dep so UNION schemas match.
        granular_date_type = dict(time_dep.dtypes)["granular_date"]

        # Non-time-dependent rows: pass through with null granular_date.
        non_time_dep = sim.filter(F.col("absolute_time_index").isNull()).withColumn(
            "granular_date", F.lit(None).cast(granular_date_type)
        )

        combined = time_dep.unionByName(non_time_dep)
        self._write_single_parquet(combined, output_path)

    def write_metric_structure(
        self,
        rows: list[dict[str, Any]],
        output_path: Path,
    ) -> None:
        from pyspark.sql.types import LongType, StringType, StructField, StructType

        schema = StructType(
            [
                StructField("metric_id", StringType(), nullable=True),
                StructField("component", StringType(), nullable=True),
                StructField("metric_location", StringType(), nullable=True),
                StructField("breakdown_properties", StringType(), nullable=True),
                StructField("output", StringType(), nullable=True),
                StructField("weight_output_id", LongType(), nullable=True),
            ]
        )
        df = self.spark.createDataFrame(rows or [], schema=schema)
        self._write_single_parquet(df, output_path)

    def aggregate_metric_terms(
        self,
        filtered_sim_path: Path,
        metric_structure_path: Path,
        operator: TermsOperator,
        output_path: Path,
    ) -> None:
        from pyspark.sql import functions as F

        sim = self._read_parquet(filtered_sim_path)
        struct = self._read_parquet(metric_structure_path)

        agg_fn = F.sum("value") if operator == TermsOperator.SUM else F.avg("value")

        result = (
            struct.join(sim, on=["component", "output"], how="left")
            .withColumn("scenario", F.col("scenario_index"))
            .groupBy(
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "absolute_time_index",
                "scenario",
            )
            .agg(
                agg_fn.alias("granular_metric_value"),
                F.first("granular_date", ignorenulls=True).alias("granular_date"),
            )
            .select(
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "absolute_time_index",
                "scenario",
                "granular_metric_value",
                "granular_date",
            )
        )
        self._write_single_parquet(result, output_path)

    def aggregate_metric_temporally(
        self,
        metric_view_path: Path,
        operator: TimeOperator,
        output_path: Path,
    ) -> None:
        from pyspark.sql import functions as F

        view = self._read_parquet(metric_view_path)
        agg_fn = (
            F.sum("granular_metric_value") if operator == TimeOperator.SUM else F.avg("granular_metric_value")
        )

        result = (
            view.withColumnRenamed("granular_date", "view_date")
            .groupBy(
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "view_date",
                "scenario",
            )
            .agg(agg_fn.alias("metric_value"))
            .select(
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "view_date",
                "scenario",
                "metric_value",
            )
        )
        self._write_single_parquet(result, output_path)

    def consolidate(
        self,
        chunk_paths: list[Path],
        output_path: Path,
    ) -> None:
        df = self.spark.read.parquet(*[str(p) for p in chunk_paths])
        self._write_single_parquet(df, output_path)
