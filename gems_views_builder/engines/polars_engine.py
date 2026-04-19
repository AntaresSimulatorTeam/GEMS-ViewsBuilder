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

"""Polars backend engine (lazy API, current default implementation)."""

from pathlib import Path
from typing import Any

import polars as pl

from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.engines.base import (
    PARQUET_COMPRESSION,
    PARQUET_COMPRESSION_LEVEL,
    PARQUET_ROW_GROUP_SIZE,
    DataEngine,
)

_METRIC_STRUCTURE_SCHEMA = pl.Schema(
    {
        "metric_id": pl.Utf8,
        "component": pl.Utf8,
        "metric_location": pl.Utf8,
        "breakdown_properties": pl.Utf8,
        "output": pl.Utf8,
        "weight_output_id": pl.Int64,
    }
)


class PolarsEngine(DataEngine):
    """Data engine backed by Polars lazy frames."""

    def filter_simulation_table(
        self,
        simulation_path: Path,
        calendar_path: Path,
        output_path: Path,
    ) -> None:
        sim_df = pl.scan_parquet(simulation_path)
        calendar_df = pl.scan_csv(calendar_path, try_parse_dates=True)

        # Time-dependent rows: inner join + block match
        time_dep_path = output_path.with_suffix(".time_dep.parquet")
        (
            sim_df.join(calendar_df, on="absolute_time_index", how="inner")
            .filter(pl.col("block") == pl.col("block_right"))
            .drop("block_right")
        ).sink_parquet(time_dep_path, compression=PARQUET_COMPRESSION, compression_level=PARQUET_COMPRESSION_LEVEL)

        # Non-time-dependent rows: pass through with null granular_date typed
        # to match the time-dep column so schemas align on union.
        non_time_dep_path = output_path.with_suffix(".non_time_dep.parquet")
        granular_date_dtype = pl.read_parquet_schema(time_dep_path)["granular_date"]
        (
            sim_df.filter(pl.col("absolute_time_index").is_null()).with_columns(
                pl.lit(None).cast(granular_date_dtype).alias("granular_date")
            )
        ).sink_parquet(non_time_dep_path, compression=PARQUET_COMPRESSION, compression_level=PARQUET_COMPRESSION_LEVEL)

        pl.scan_parquet([time_dep_path, non_time_dep_path]).sink_parquet(
            output_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        time_dep_path.unlink()
        non_time_dep_path.unlink()

    def write_metric_structure(
        self,
        rows: list[dict[str, Any]],
        output_path: Path,
    ) -> None:
        df = (
            pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA)
            if not rows
            else pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA)
        )
        df.write_parquet(
            output_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
            use_pyarrow=True,
            pyarrow_options={"data_page_version": "2.0"},
        )

    def aggregate_metric_terms(
        self,
        filtered_sim_path: Path,
        metric_structure_path: Path,
        operator: TermsOperator,
        output_path: Path,
    ) -> None:
        filtered_sim = pl.scan_parquet(filtered_sim_path)
        metric_structure = pl.scan_parquet(metric_structure_path)

        value_agg = pl.col("value").sum() if operator == TermsOperator.SUM else pl.col("value").mean()
        (
            filtered_sim.join(metric_structure, on=["component", "output"], how="right")
            .with_columns(pl.col("scenario_index").alias("scenario"))
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
        ).sink_parquet(
            output_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )

    def aggregate_metric_temporally(
        self,
        metric_view_path: Path,
        operator: TimeOperator,
        output_path: Path,
    ) -> None:
        metric_view = pl.scan_parquet(metric_view_path)
        time_agg = (
            pl.col("granular_metric_value").sum()
            if operator == TimeOperator.SUM
            else pl.col("granular_metric_value").mean()
        ).alias("metric_value")
        (
            metric_view.with_columns(pl.col("granular_date").alias("view_date"))
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
        ).sink_parquet(
            output_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )

    def consolidate(
        self,
        chunk_paths: list[Path],
        output_path: Path,
    ) -> None:
        pl.scan_parquet(chunk_paths).sink_parquet(
            output_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
