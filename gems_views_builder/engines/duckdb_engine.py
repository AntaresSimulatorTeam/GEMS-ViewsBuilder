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

"""DuckDB backend engine (SQL on parquet files)."""

from pathlib import Path
from typing import Any

from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.engines.base import (
    PARQUET_COMPRESSION,
    PARQUET_ROW_GROUP_SIZE,
    DataEngine,
)


class DuckDBEngine(DataEngine):
    """Data engine backed by DuckDB SQL queries executed on parquet/CSV files."""

    def __init__(self) -> None:
        try:
            import duckdb

            self._con = duckdb.connect()
            # Consistent compression across all COPY statements.
            self._compression = PARQUET_COMPRESSION.upper()
            self._row_group_size = PARQUET_ROW_GROUP_SIZE
        except ImportError as exc:
            raise ImportError("DuckDB is required for the duckdb backend: pip install duckdb") from exc

    def _copy_opts(self) -> str:
        return f"FORMAT PARQUET, COMPRESSION {self._compression}, ROW_GROUP_SIZE {self._row_group_size}"

    def filter_simulation_table(
        self,
        simulation_path: Path,
        calendar_path: Path,
        output_path: Path,
    ) -> None:
        # Write time-dep rows first so we can inspect the granular_date type.
        time_dep_path = output_path.with_suffix(".time_dep.parquet")
        self._con.execute(f"""
            COPY (
                SELECT s.*, c.granular_date
                FROM read_parquet('{simulation_path}') s
                INNER JOIN read_csv('{calendar_path}', header = true, auto_detect = true) c
                    ON s.absolute_time_index = c.absolute_time_index
                WHERE s.block = c.block
            ) TO '{time_dep_path}' ({self._copy_opts()})
        """)

        # Reflect the granular_date type from the time-dep file so the UNION
        # schema matches (mirrors the polars read_parquet_schema pattern).
        # DuckDB ≥1.0 names the type column "column_type" in DESCRIBE output.
        row = self._con.execute(
            f"SELECT column_type FROM (DESCRIBE SELECT granular_date FROM read_parquet('{time_dep_path}')) LIMIT 1"
        ).fetchone()
        granular_date_type = row[0] if row else "DATE"

        non_time_dep_path = output_path.with_suffix(".non_time_dep.parquet")
        self._con.execute(f"""
            COPY (
                SELECT *, CAST(NULL AS {granular_date_type}) AS granular_date
                FROM read_parquet('{simulation_path}')
                WHERE absolute_time_index IS NULL
            ) TO '{non_time_dep_path}' ({self._copy_opts()})
        """)

        self._con.execute(f"""
            COPY (
                SELECT * FROM read_parquet(['{time_dep_path}', '{non_time_dep_path}'])
            ) TO '{output_path}' ({self._copy_opts()})
        """)
        time_dep_path.unlink()
        non_time_dep_path.unlink()

    def write_metric_structure(
        self,
        rows: list[dict[str, Any]],
        output_path: Path,
    ) -> None:
        if not rows:
            self._con.execute(f"""
                COPY (
                    SELECT
                        NULL::VARCHAR AS metric_id,
                        NULL::VARCHAR AS component,
                        NULL::VARCHAR AS metric_location,
                        NULL::VARCHAR AS breakdown_properties,
                        NULL::VARCHAR AS output,
                        NULL::BIGINT  AS weight_output_id
                    LIMIT 0
                ) TO '{output_path}' ({self._copy_opts()})
            """)
            return

        import pandas as pd

        df = pd.DataFrame(rows)
        # Register as a temporary view so DuckDB can query it.
        self._con.register("_metric_structure_rows", df)
        self._con.execute(f"""
            COPY (SELECT * FROM _metric_structure_rows)
            TO '{output_path}' ({self._copy_opts()})
        """)
        self._con.unregister("_metric_structure_rows")

    def aggregate_metric_terms(
        self,
        filtered_sim_path: Path,
        metric_structure_path: Path,
        operator: TermsOperator,
        output_path: Path,
    ) -> None:
        agg_fn = "SUM" if operator == TermsOperator.SUM else "AVG"
        # any_value() returns an arbitrary non-null value — equivalent to
        # polars drop_nulls().first() for the granular_date column.
        self._con.execute(f"""
            COPY (
                SELECT
                    m.metric_id,
                    m.metric_location,
                    m.breakdown_properties,
                    s.absolute_time_index,
                    s.scenario_index                AS scenario,
                    {agg_fn}(s.value)               AS granular_metric_value,
                    any_value(s.granular_date)       AS granular_date
                FROM read_parquet('{metric_structure_path}') m
                LEFT JOIN read_parquet('{filtered_sim_path}') s
                    ON m.component = s.component AND m.output = s.output
                GROUP BY
                    m.metric_id,
                    m.metric_location,
                    m.breakdown_properties,
                    s.absolute_time_index,
                    s.scenario_index
            ) TO '{output_path}' ({self._copy_opts()})
        """)

    def aggregate_metric_temporally(
        self,
        metric_view_path: Path,
        operator: TimeOperator,
        output_path: Path,
    ) -> None:
        agg_fn = "SUM" if operator == TimeOperator.SUM else "AVG"
        self._con.execute(f"""
            COPY (
                SELECT
                    metric_id,
                    metric_location,
                    breakdown_properties,
                    granular_date                          AS view_date,
                    scenario,
                    {agg_fn}(granular_metric_value)        AS metric_value
                FROM read_parquet('{metric_view_path}')
                GROUP BY
                    metric_id,
                    metric_location,
                    breakdown_properties,
                    granular_date,
                    scenario
            ) TO '{output_path}' ({self._copy_opts()})
        """)

    def consolidate(
        self,
        chunk_paths: list[Path],
        output_path: Path,
    ) -> None:
        paths_literal = ", ".join(f"'{p}'" for p in chunk_paths)
        self._con.execute(f"""
            COPY (
                SELECT * FROM read_parquet([{paths_literal}])
            ) TO '{output_path}' ({self._copy_opts()})
        """)
