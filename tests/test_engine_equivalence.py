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

"""Cross-engine behavioral equivalence tests for DataEngine implementations.

These tests run polars, duckdb, and pyarrow on identical synthetic data and
assert that outputs are identical (modulo row ordering). Spark is excluded
because it requires a JVM and is too heavy for unit tests.
"""

import datetime
from pathlib import Path

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.engines.base import make_engine

ENGINES = ["polars", "duckdb", "pyarrow"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_sorted(path: Path, sort_cols: list[str]) -> pl.DataFrame:
    """Read a parquet file and sort it for deterministic comparison."""
    df = pl.read_parquet(path)
    # Only sort by columns that actually exist
    cols = [c for c in sort_cols if c in df.columns]
    return df.sort(cols)


def _write_sim_parquet(path: Path, rows: list[dict]) -> None:
    """Write a minimal simulation-table parquet (matches schema used in real code)."""
    df = pl.DataFrame(
        rows,
        schema={
            "block": pl.Int64,
            "component": pl.Utf8,
            "output": pl.Utf8,
            "absolute_time_index": pl.Int64,
            "block_time_index": pl.Int64,
            "scenario_index": pl.Int64,
            "value": pl.Float64,
        },
    )
    df.write_parquet(path)


def _write_calendar_csv(path: Path, rows: list[dict]) -> None:
    """Write a minimal calendar CSV."""
    df = pl.DataFrame(
        rows,
        schema={
            "absolute_time_index": pl.Int64,
            "block": pl.Int64,
            "granular_date": pl.Date,
        },
    )
    df.write_csv(path)


# ---------------------------------------------------------------------------
# Test 1: write_metric_structure — null weight_output_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine_name", ["polars", "pyarrow"])
def test_write_metric_structure_null_weight_output_id_is_int64(tmp_path: Path, engine_name: str) -> None:
    """Polars and PyArrow write int64 for weight_output_id even when the input is all-None."""
    engine = make_engine(engine_name)
    rows = [
        {
            "metric_id": "m1",
            "component": "comp_a",
            "metric_location": "loc_a",
            "breakdown_properties": "{}",
            "output": "out_a",
            "weight_output_id": None,
        }
    ]
    out = tmp_path / f"metric_structure_{engine_name}.parquet"
    engine.write_metric_structure(rows, out)

    table = pq.read_table(str(out))
    field_type = table.schema.field("weight_output_id").type
    assert field_type == pa.int64(), f"[{engine_name}] weight_output_id should be int64, got {field_type}"


def test_write_metric_structure_duckdb_null_weight_output_id_type_differs(tmp_path: Path) -> None:
    """Document known DuckDB type divergence: weight_output_id written as int32 (not int64) for all-None input.

    DuckDB infers the type from a pandas DataFrame where all-None columns have dtype=object.
    DuckDB maps object→int32 rather than applying the intended schema (int64).
    Polars and PyArrow use explicit schemas and always write int64.
    """
    rows = [{"metric_id": "m1", "component": "c", "metric_location": "l",
              "breakdown_properties": "{}", "output": "o", "weight_output_id": None}]

    out_duckdb = tmp_path / "ms_duckdb.parquet"
    out_polars = tmp_path / "ms_polars.parquet"
    make_engine("duckdb").write_metric_structure(rows, out_duckdb)
    make_engine("polars").write_metric_structure(rows, out_polars)

    duckdb_type = pq.read_table(str(out_duckdb)).schema.field("weight_output_id").type
    polars_type = pq.read_table(str(out_polars)).schema.field("weight_output_id").type

    assert polars_type == pa.int64(), f"polars should write int64, got {polars_type}"
    # DuckDB writes int32 instead of int64 for all-None weight_output_id
    assert duckdb_type == pa.int32(), f"DuckDB divergence: expected int32, got {duckdb_type}"


def test_write_metric_structure_duckdb_mixed_weight_output_id_type_is_double(tmp_path: Path) -> None:
    """Document known DuckDB type divergence: weight_output_id written as double when mix of int+None.

    When pandas infers int+None as float64 (NaN for missing), DuckDB propagates that as double.
    Polars and PyArrow apply their explicit schemas and write int64 with proper null handling.
    """
    rows = [
        {"metric_id": "m1", "component": "c", "metric_location": "l",
         "breakdown_properties": "{}", "output": "o1", "weight_output_id": 42},
        {"metric_id": "m2", "component": "c", "metric_location": "l",
         "breakdown_properties": "{}", "output": "o2", "weight_output_id": None},
    ]

    out_duckdb = tmp_path / "ms_duckdb.parquet"
    out_polars = tmp_path / "ms_polars.parquet"
    make_engine("duckdb").write_metric_structure(rows, out_duckdb)
    make_engine("polars").write_metric_structure(rows, out_polars)

    duckdb_type = pq.read_table(str(out_duckdb)).schema.field("weight_output_id").type
    polars_type = pq.read_table(str(out_polars)).schema.field("weight_output_id").type

    assert polars_type == pa.int64(), f"polars should write int64, got {polars_type}"
    # DuckDB writes double (float64) because pandas infers int+None as float64
    assert pa.types.is_floating(duckdb_type), (
        f"DuckDB divergence: expected a float type for int+None mix, got {duckdb_type}"
    )


@pytest.mark.parametrize("engine_name", ENGINES)
def test_write_metric_structure_integer_weight_output_id_is_int64(tmp_path: Path, engine_name: str) -> None:
    """All engines write int64 when weight_output_id has a concrete integer value (no None)."""
    engine = make_engine(engine_name)
    rows = [
        {
            "metric_id": "m1",
            "component": "comp_a",
            "metric_location": "loc_a",
            "breakdown_properties": "{}",
            "output": "out_a",
            "weight_output_id": 42,
        }
    ]
    out = tmp_path / f"metric_structure_{engine_name}.parquet"
    engine.write_metric_structure(rows, out)

    table = pq.read_table(str(out))
    field_type = table.schema.field("weight_output_id").type
    assert field_type == pa.int64(), f"[{engine_name}] weight_output_id should be int64, got {field_type}"


def test_write_metric_structure_cross_engine_values_equivalent(tmp_path: Path) -> None:
    """All engines write equivalent values for write_metric_structure (ignoring type width).
    Note: DuckDB diverges on weight_output_id type (int32/double vs int64) — see dedicated tests.
    """
    rows = [
        {
            "metric_id": "m1",
            "component": "comp_a",
            "metric_location": "loc_a",
            "breakdown_properties": "{}",
            "output": "out_a",
            "weight_output_id": 7,
        },
    ]
    sort_cols = ["metric_id"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"ms_{name}.parquet"
        make_engine(name).write_metric_structure(rows, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    for name in ["duckdb", "pyarrow"]:
        other = outputs[name]
        # Cast both to int64 to normalize DuckDB's type divergence and compare values
        ref_cast = ref.with_columns(pl.col("weight_output_id").cast(pl.Int64))
        other_cast = other.select(ref.columns).with_columns(pl.col("weight_output_id").cast(pl.Int64))
        assert ref_cast.equals(other_cast), f"[{name}] write_metric_structure values differ from polars"


# ---------------------------------------------------------------------------
# Test 2: filter_simulation_table — basic equivalence
# ---------------------------------------------------------------------------


def test_filter_simulation_table_cross_engine_equivalence(tmp_path: Path) -> None:
    """All engines must produce identical filtered simulation table."""
    sim_path = tmp_path / "sim.parquet"
    cal_path = tmp_path / "calendar.csv"

    _write_sim_parquet(
        sim_path,
        [
            # Time-dependent rows that match the calendar
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 1, "value": 100.0},
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 20, "block_time_index": 0, "scenario_index": 1, "value": 200.0},
            # Time-dependent row with wrong block — should be dropped
            {"block": 2, "component": "c1", "output": "o1", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 1, "value": 999.0},
            # Non-time-dependent row (null index) — always passes through
            {"block": 1, "component": "c2", "output": "o2", "absolute_time_index": None, "block_time_index": None, "scenario_index": 1, "value": 50.0},
        ],
    )
    _write_calendar_csv(
        cal_path,
        [
            {"absolute_time_index": 10, "block": 1, "granular_date": datetime.date(2024, 1, 1)},
            {"absolute_time_index": 20, "block": 1, "granular_date": datetime.date(2024, 1, 2)},
        ],
    )

    sort_cols = ["component", "output", "absolute_time_index", "scenario_index"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"filtered_{name}.parquet"
        make_engine(name).filter_simulation_table(sim_path, cal_path, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    assert ref.height == 3, f"Expected 3 rows (2 time-dep + 1 non-time-dep), got {ref.height}"

    for name in ["duckdb", "pyarrow"]:
        other = outputs[name].select(ref.columns)
        # Compare with cast to handle minor type differences (e.g. Date vs Datetime)
        assert other.height == ref.height, f"[{name}] row count differs: {other.height} vs {ref.height}"
        for col in ["component", "output", "scenario_index", "value"]:
            assert ref[col].to_list() == other[col].to_list(), f"[{name}] column {col!r} differs"


def test_filter_simulation_table_empty_time_dep(tmp_path: Path) -> None:
    """When no time-dep rows match the calendar, only non-time-dep rows remain.
    granular_date column must exist and contain only nulls."""
    sim_path = tmp_path / "sim.parquet"
    cal_path = tmp_path / "calendar.csv"

    _write_sim_parquet(
        sim_path,
        [
            # absolute_time_index=99 does NOT appear in calendar → filtered out
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 99, "block_time_index": 0, "scenario_index": 1, "value": 1.0},
            # Non-time-dependent
            {"block": 1, "component": "c2", "output": "o2", "absolute_time_index": None, "block_time_index": None, "scenario_index": 1, "value": 2.0},
        ],
    )
    _write_calendar_csv(
        cal_path,
        [
            {"absolute_time_index": 10, "block": 1, "granular_date": datetime.date(2024, 1, 1)},
        ],
    )

    for name in ENGINES:
        out = tmp_path / f"filtered_empty_{name}.parquet"
        make_engine(name).filter_simulation_table(sim_path, cal_path, out)
        df = pl.read_parquet(out)
        assert df.height == 1, f"[{name}] expected 1 row (non-time-dep only), got {df.height}"
        assert "granular_date" in df.columns, f"[{name}] granular_date column missing"
        assert df["granular_date"].is_null().all(), f"[{name}] granular_date should be all-null"


# ---------------------------------------------------------------------------
# Test 3: aggregate_metric_terms — cross-engine equivalence
# ---------------------------------------------------------------------------


def _write_filtered_sim(path: Path, rows: list[dict]) -> None:
    """Write a filtered-simulation parquet (output of filter_simulation_table)."""
    df = pl.DataFrame(
        rows,
        schema={
            "block": pl.Int64,
            "component": pl.Utf8,
            "output": pl.Utf8,
            "absolute_time_index": pl.Int64,
            "block_time_index": pl.Int64,
            "scenario_index": pl.Int64,
            "value": pl.Float64,
            "granular_date": pl.Date,
        },
    )
    df.write_parquet(path)


def test_aggregate_metric_terms_cross_engine_sum(tmp_path: Path) -> None:
    """SUM aggregation must produce identical results across all engines."""
    sim_path = tmp_path / "filtered_sim.parquet"
    struct_path = tmp_path / "metric_structure.parquet"

    _write_filtered_sim(
        sim_path,
        [
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 1, "value": 10.0, "granular_date": datetime.date(2024, 1, 1)},
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 2, "value": 20.0, "granular_date": datetime.date(2024, 1, 1)},
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 20, "block_time_index": 0, "scenario_index": 1, "value": 30.0, "granular_date": datetime.date(2024, 1, 2)},
        ],
    )
    make_engine("polars").write_metric_structure(
        [{"metric_id": "m1", "component": "c1", "metric_location": "loc1", "breakdown_properties": "{}", "output": "o1", "weight_output_id": None}],
        struct_path,
    )

    sort_cols = ["metric_id", "absolute_time_index", "scenario"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"agg_terms_{name}.parquet"
        make_engine(name).aggregate_metric_terms(sim_path, struct_path, TermsOperator.SUM, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    assert ref.height == 3, f"Expected 3 rows, got {ref.height}"

    for name in ["duckdb", "pyarrow"]:
        other = outputs[name].select(ref.columns)
        assert other.height == ref.height, f"[{name}] row count differs"
        for col in ["metric_id", "metric_location", "granular_metric_value", "scenario"]:
            assert ref[col].to_list() == other[col].to_list(), f"[{name}] column {col!r} differs"


def test_aggregate_metric_terms_cross_engine_mean(tmp_path: Path) -> None:
    """MEAN aggregation must produce identical results across all engines."""
    sim_path = tmp_path / "filtered_sim.parquet"
    struct_path = tmp_path / "metric_structure.parquet"

    _write_filtered_sim(
        sim_path,
        [
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 1, "value": 10.0, "granular_date": datetime.date(2024, 1, 1)},
            {"block": 1, "component": "c1", "output": "o1", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 1, "value": 30.0, "granular_date": datetime.date(2024, 1, 1)},
        ],
    )
    make_engine("polars").write_metric_structure(
        [{"metric_id": "m1", "component": "c1", "metric_location": "loc1", "breakdown_properties": "{}", "output": "o1", "weight_output_id": None}],
        struct_path,
    )

    sort_cols = ["metric_id", "absolute_time_index", "scenario"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"agg_mean_{name}.parquet"
        make_engine(name).aggregate_metric_terms(sim_path, struct_path, TermsOperator.AVG, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    for name in ["duckdb", "pyarrow"]:
        other = outputs[name].select(ref.columns)
        assert other["granular_metric_value"].to_list() == ref["granular_metric_value"].to_list(), (
            f"[{name}] MEAN granular_metric_value differs"
        )


def test_aggregate_metric_terms_no_sim_match(tmp_path: Path) -> None:
    """Document the known SUM divergence when no simulation row matches a metric structure entry.

    Polars and PyArrow return 0.0 (SUM identity for empty group).
    DuckDB returns NULL (SQL standard: SUM of no rows = NULL).
    All three return NULL for MEAN (undefined for empty group — consistent).
    """
    sim_path = tmp_path / "filtered_sim.parquet"
    struct_path = tmp_path / "metric_structure.parquet"

    # sim has component c2, struct has c1 — no match
    _write_filtered_sim(
        sim_path,
        [
            {"block": 1, "component": "c2", "output": "o2", "absolute_time_index": 10, "block_time_index": 0, "scenario_index": 1, "value": 5.0, "granular_date": datetime.date(2024, 1, 1)},
        ],
    )
    make_engine("polars").write_metric_structure(
        [{"metric_id": "m1", "component": "c1", "metric_location": "loc1", "breakdown_properties": "{}", "output": "o1", "weight_output_id": None}],
        struct_path,
    )

    # SUM: polars and pyarrow return 0.0; duckdb returns NULL
    sum_outputs = {}
    for name in ENGINES:
        out = tmp_path / f"agg_nomatch_sum_{name}.parquet"
        make_engine(name).aggregate_metric_terms(sim_path, struct_path, TermsOperator.SUM, out)
        sum_outputs[name] = pl.read_parquet(out)

    assert sum_outputs["polars"]["granular_metric_value"].to_list() == [0.0], "polars SUM no-match: expected 0.0"
    assert sum_outputs["pyarrow"]["granular_metric_value"].to_list() == [0.0], "pyarrow SUM no-match: expected 0.0"
    # DuckDB follows SQL standard: SUM of no rows is NULL, not 0
    assert sum_outputs["duckdb"]["granular_metric_value"].is_null().all(), "duckdb SUM no-match: expected NULL (SQL standard)"

    # MEAN: all three agree — NULL (mean of no values is undefined)
    mean_outputs = {}
    for name in ENGINES:
        out = tmp_path / f"agg_nomatch_mean_{name}.parquet"
        make_engine(name).aggregate_metric_terms(sim_path, struct_path, TermsOperator.AVG, out)
        mean_outputs[name] = pl.read_parquet(out)

    for name in ENGINES:
        assert mean_outputs[name]["granular_metric_value"].is_null().all(), (
            f"[{name}] MEAN no-match: expected NULL"
        )


# ---------------------------------------------------------------------------
# Test 4: aggregate_metric_temporally — cross-engine equivalence
# ---------------------------------------------------------------------------


def _write_metric_view(path: Path, rows: list[dict]) -> None:
    """Write a metric-view parquet (output of aggregate_metric_terms)."""
    df = pl.DataFrame(
        rows,
        schema={
            "metric_id": pl.Utf8,
            "metric_location": pl.Utf8,
            "breakdown_properties": pl.Utf8,
            "absolute_time_index": pl.Int64,
            "scenario": pl.Int64,
            "granular_metric_value": pl.Float64,
            "granular_date": pl.Date,
        },
    )
    df.write_parquet(path)


def test_aggregate_metric_temporally_cross_engine_sum(tmp_path: Path) -> None:
    """Temporal SUM must produce identical results across all engines."""
    view_path = tmp_path / "metric_view.parquet"
    _write_metric_view(
        view_path,
        [
            {"metric_id": "m1", "metric_location": "loc1", "breakdown_properties": "{}", "absolute_time_index": 10, "scenario": 1, "granular_metric_value": 10.0, "granular_date": datetime.date(2024, 1, 1)},
            {"metric_id": "m1", "metric_location": "loc1", "breakdown_properties": "{}", "absolute_time_index": 20, "scenario": 1, "granular_metric_value": 30.0, "granular_date": datetime.date(2024, 1, 1)},
            {"metric_id": "m1", "metric_location": "loc1", "breakdown_properties": "{}", "absolute_time_index": 30, "scenario": 1, "granular_metric_value": 5.0,  "granular_date": datetime.date(2024, 1, 2)},
        ],
    )

    sort_cols = ["metric_id", "view_date", "scenario"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"agg_temporal_{name}.parquet"
        make_engine(name).aggregate_metric_temporally(view_path, TimeOperator.SUM, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    # date 2024-01-01 has 10+30=40, date 2024-01-02 has 5
    assert ref.height == 2, f"Expected 2 rows, got {ref.height}"
    vals = dict(zip(ref["view_date"].cast(pl.Utf8).to_list(), ref["metric_value"].to_list()))
    assert vals["2024-01-01"] == pytest.approx(40.0)
    assert vals["2024-01-02"] == pytest.approx(5.0)

    for name in ["duckdb", "pyarrow"]:
        other = outputs[name].select(ref.columns)
        assert other.height == ref.height, f"[{name}] row count differs"
        for col in ["metric_value"]:
            assert other[col].to_list() == pytest.approx(ref[col].to_list()), f"[{name}] column {col!r} differs"


def test_aggregate_metric_temporally_cross_engine_mean(tmp_path: Path) -> None:
    """Temporal MEAN must produce identical results across all engines."""
    view_path = tmp_path / "metric_view_mean.parquet"
    _write_metric_view(
        view_path,
        [
            {"metric_id": "m1", "metric_location": "loc1", "breakdown_properties": "{}", "absolute_time_index": 10, "scenario": 1, "granular_metric_value": 10.0, "granular_date": datetime.date(2024, 1, 1)},
            {"metric_id": "m1", "metric_location": "loc1", "breakdown_properties": "{}", "absolute_time_index": 20, "scenario": 1, "granular_metric_value": 30.0, "granular_date": datetime.date(2024, 1, 1)},
        ],
    )

    sort_cols = ["metric_id", "view_date", "scenario"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"agg_temporal_mean_{name}.parquet"
        make_engine(name).aggregate_metric_temporally(view_path, TimeOperator.AVG, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    assert ref["metric_value"][0] == pytest.approx(20.0), "MEAN of [10, 30] should be 20"

    for name in ["duckdb", "pyarrow"]:
        other = outputs[name].select(ref.columns)
        assert other["metric_value"].to_list() == pytest.approx(ref["metric_value"].to_list()), (
            f"[{name}] MEAN metric_value differs"
        )


# ---------------------------------------------------------------------------
# Test 5: consolidate — cross-engine equivalence
# ---------------------------------------------------------------------------


def test_consolidate_cross_engine_equivalence(tmp_path: Path) -> None:
    """consolidate must produce identical concatenated output across all engines."""
    chunks = []
    for i in range(3):
        p = tmp_path / f"chunk_{i}.parquet"
        pl.DataFrame({"x": [i * 10], "y": [float(i)]}).write_parquet(p)
        chunks.append(p)

    sort_cols = ["x"]
    outputs = {}
    for name in ENGINES:
        out = tmp_path / f"consolidated_{name}.parquet"
        make_engine(name).consolidate(chunks, out)
        outputs[name] = _read_sorted(out, sort_cols)

    ref = outputs["polars"]
    assert ref.height == 3
    for name in ["duckdb", "pyarrow"]:
        other = outputs[name].select(ref.columns)
        assert ref.equals(other), f"[{name}] consolidate output differs from polars"
