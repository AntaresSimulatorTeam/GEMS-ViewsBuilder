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

"""PyArrow backend engine.

Uses PyArrow for all parquet and CSV I/O.  Pandas DataFrames are used as the
intermediate computation layer for join and group-by operations because PyArrow
does not expose a high-level relational query API.  The round-trip cost
(Arrow → pandas → Arrow) is part of what this backend measures.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.engines.base import (
    PARQUET_COMPRESSION,
    PARQUET_ROW_GROUP_SIZE,
    DataEngine,
)

_METRIC_STRUCTURE_SCHEMA = pa.schema(
    [
        ("metric_id", pa.string()),
        ("component", pa.string()),
        ("metric_location", pa.string()),
        ("breakdown_properties", pa.string()),
        ("output", pa.string()),
        ("weight_output_id", pa.int64()),
    ]
)

_WRITE_OPTS = dict(
    compression=PARQUET_COMPRESSION,
    row_group_size=PARQUET_ROW_GROUP_SIZE,
    data_page_version="2.0",
)


def _write(table: pa.Table, path: Path) -> None:
    pq.write_table(table, str(path), **_WRITE_OPTS)


class PyArrowEngine(DataEngine):
    """Data engine backed by PyArrow I/O + pandas for relational operations."""

    def filter_simulation_table(
        self,
        simulation_path: Path,
        calendar_path: Path,
        output_path: Path,
    ) -> None:
        sim = pq.read_table(str(simulation_path)).to_pandas()
        cal = pa_csv.read_csv(str(calendar_path)).to_pandas()

        # Parse granular_date as datetime if it comes in as string.
        if cal["granular_date"].dtype == object:
            cal["granular_date"] = pd.to_datetime(cal["granular_date"])

        # Time-dependent rows: inner join + block-match filter.
        time_dep = sim.merge(cal, on="absolute_time_index", how="inner", suffixes=("", "_right"))
        time_dep = time_dep[time_dep["block"] == time_dep["block_right"]].drop(columns=["block_right"])

        # Non-time-dependent rows: null index, carry null granular_date typed
        # to the same dtype as the time-dep column so pandas concat doesn't
        # warn about NA-only column dtype coercion.
        non_time_dep = sim[sim["absolute_time_index"].isna()].copy()
        date_dtype = time_dep["granular_date"].dtype if not time_dep.empty else "datetime64[us]"
        non_time_dep["granular_date"] = pd.Series(pd.NaT, index=non_time_dep.index, dtype=date_dtype)

        combined = pd.concat([time_dep, non_time_dep], ignore_index=True)
        _write(pa.Table.from_pandas(combined, preserve_index=False), output_path)

    def write_metric_structure(
        self,
        rows: list[dict[str, Any]],
        output_path: Path,
    ) -> None:
        if not rows:
            table = _METRIC_STRUCTURE_SCHEMA.empty_table()
        else:
            table = pa.Table.from_pandas(
                pd.DataFrame(rows),
                schema=_METRIC_STRUCTURE_SCHEMA,
                preserve_index=False,
            )
        _write(table, output_path)

    def aggregate_metric_terms(
        self,
        filtered_sim_path: Path,
        metric_structure_path: Path,
        operator: TermsOperator,
        output_path: Path,
    ) -> None:
        sim = pq.read_table(str(filtered_sim_path)).to_pandas()
        struct = pq.read_table(str(metric_structure_path)).to_pandas()

        # Right-join from sim's perspective = left-join from struct's perspective.
        joined = struct.merge(sim, on=["component", "output"], how="left")
        joined["scenario"] = joined["scenario_index"]

        agg_fn = "sum" if operator == TermsOperator.SUM else "mean"
        # pandas GroupBy.first() skips NaN by default — matches polars
        # drop_nulls().first() semantics for granular_date.
        result = (
            joined.groupby(
                ["metric_id", "metric_location", "breakdown_properties", "absolute_time_index", "scenario"],
                as_index=False,
                dropna=False,
            )
            .agg(
                granular_metric_value=pd.NamedAgg("value", agg_fn),
                granular_date=pd.NamedAgg("granular_date", "first"),
            )
        )
        result = result[
            [
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "absolute_time_index",
                "scenario",
                "granular_metric_value",
                "granular_date",
            ]
        ]
        _write(pa.Table.from_pandas(result, preserve_index=False), output_path)

    def aggregate_metric_temporally(
        self,
        metric_view_path: Path,
        operator: TimeOperator,
        output_path: Path,
    ) -> None:
        view = pq.read_table(str(metric_view_path)).to_pandas()
        view = view.rename(columns={"granular_date": "view_date"})

        agg_fn = "sum" if operator == TimeOperator.SUM else "mean"
        result = (
            view.groupby(
                ["metric_id", "metric_location", "breakdown_properties", "view_date", "scenario"],
                as_index=False,
                dropna=False,
            )
            .agg(metric_value=pd.NamedAgg("granular_metric_value", agg_fn))
        )
        result = result[
            [
                "metric_id",
                "metric_location",
                "breakdown_properties",
                "view_date",
                "scenario",
                "metric_value",
            ]
        ]
        _write(pa.Table.from_pandas(result, preserve_index=False), output_path)

    def consolidate(
        self,
        chunk_paths: list[Path],
        output_path: Path,
    ) -> None:
        tables = [pq.read_table(str(p)) for p in chunk_paths]
        _write(pa.concat_tables(tables), output_path)
