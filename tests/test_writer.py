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

import re
from pathlib import Path
from typing import Any, cast

import polars as pl
import pyarrow.parquet as pq
import pytest

from gems_views_builder.common import PARQUET_ROW_GROUP_SIZE
from gems_views_builder.writer import Writer

# Schema matching temporal aggregation chunk output
_CHUNK_SCHEMA = {
    "metric_id": pl.Utf8,
    "metric_location": pl.Utf8,
    "breakdown_properties": pl.Utf8,
    "view_date": pl.Utf8,
    "scenario": pl.Int64,
    "metric_value": pl.Float64,
}

_RESULT_FILENAME_PATTERN = re.compile(r"^view\d{8}T\d{6}\.parquet$")


def _write_chunk(path: Path, rows: list[dict[str, object]]) -> Path:
    pl.DataFrame(rows, schema=_CHUNK_SCHEMA).write_parquet(path)
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def two_chunks(tmp_path: Path) -> list[Path]:
    chunks_dir = tmp_path / "temporal_aggregation"
    chunks_dir.mkdir()
    chunk_a = _write_chunk(
        chunks_dir / "metric_a-0.parquet",
        [
            {
                "metric_id": "a",
                "metric_location": "loc1",
                "breakdown_properties": "{}",
                "view_date": "2024-01-01",
                "scenario": 1,
                "metric_value": 10.0,
            },
            {
                "metric_id": "a",
                "metric_location": "loc2",
                "breakdown_properties": "{}",
                "view_date": "2024-01-01",
                "scenario": 2,
                "metric_value": 20.0,
            },
        ],
    )
    chunk_b = _write_chunk(
        chunks_dir / "metric_b-1.parquet",
        [
            {
                "metric_id": "b",
                "metric_location": "loc1",
                "breakdown_properties": "{}",
                "view_date": "2024-01-02",
                "scenario": 1,
                "metric_value": 30.0,
            },
        ],
    )
    return [chunk_a, chunk_b]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_merge_results_returns_none_and_writes_nothing_when_no_chunks(tmp_path: Path) -> None:
    assert Writer(tmp_path).merge_results([]) is None
    assert not (tmp_path / "results").exists()


def test_result_file_is_created_in_results_dir(tmp_path: Path, two_chunks: list[Path]) -> None:
    Writer(tmp_path).merge_results(two_chunks)
    results = list((tmp_path / "results").glob("*.parquet"))
    assert len(results) == 1


def test_result_filename_matches_pattern(tmp_path: Path, two_chunks: list[Path]) -> None:
    Writer(tmp_path).merge_results(two_chunks)
    result_file = next((tmp_path / "results").glob("*.parquet"))
    assert _RESULT_FILENAME_PATTERN.match(result_file.name), f"Unexpected filename: {result_file.name}"


def test_results_dir_is_created_if_absent(tmp_path: Path, two_chunks: list[Path]) -> None:
    assert not (tmp_path / "results").exists()
    Writer(tmp_path).merge_results(two_chunks)
    assert (tmp_path / "results").is_dir()


def test_chunk_files_are_deleted_after_merging(tmp_path: Path, two_chunks: list[Path]) -> None:
    Writer(tmp_path).merge_results(two_chunks)
    for chunk in two_chunks:
        assert not chunk.exists(), f"Chunk {chunk.name} was not deleted"


def test_merged_file_contains_all_rows(tmp_path: Path, two_chunks: list[Path]) -> None:
    Writer(tmp_path).merge_results(two_chunks)
    result_file = next((tmp_path / "results").glob("*.parquet"))
    df = pl.read_parquet(result_file)
    assert len(df) == 3  # 2 rows from chunk_a + 1 row from chunk_b


def test_merged_file_contains_correct_metric_ids(tmp_path: Path, two_chunks: list[Path]) -> None:
    Writer(tmp_path).merge_results(two_chunks)
    result_file = next((tmp_path / "results").glob("*.parquet"))
    metric_ids = set(pl.read_parquet(result_file)["metric_id"].to_list())
    assert metric_ids == {"a", "b"}


def test_parquet_compression_is_zstd(tmp_path: Path, two_chunks: list[Path]) -> None:
    Writer(tmp_path).merge_results(two_chunks)
    result_file = next((tmp_path / "results").glob("*.parquet"))
    meta = cast(Any, pq).read_metadata(result_file)
    for rg_idx in range(meta.num_row_groups):
        for col_idx in range(meta.num_columns):
            compression = meta.row_group(rg_idx).column(col_idx).compression
            assert compression.lower() == "snappy" or compression.lower() == "zstd", compression
            assert compression.lower() == "zstd", f"Expected zstd, got {compression}"


def test_parquet_row_group_size_respected(tmp_path: Path) -> None:
    """Write more rows than the row group size and verify multiple row groups are created."""
    chunks_dir = tmp_path / "temporal_aggregation"
    chunks_dir.mkdir()
    n_rows = PARQUET_ROW_GROUP_SIZE + 1
    chunk = _write_chunk(
        chunks_dir / "big-0.parquet",
        [
            {
                "metric_id": "x",
                "metric_location": "l",
                "breakdown_properties": "{}",
                "view_date": "2024-01-01",
                "scenario": i,
                "metric_value": float(i),
            }
            for i in range(n_rows)
        ],
    )
    Writer(tmp_path).merge_results([chunk])
    result_file = next((tmp_path / "results").glob("*.parquet"))
    meta = cast(Any, pq).read_metadata(result_file)
    assert meta.num_row_groups >= 2, "Expected at least 2 row groups for data exceeding row_group_size"


def test_merge_with_single_chunk(tmp_path: Path) -> None:
    chunks_dir = tmp_path / "temporal_aggregation"
    chunks_dir.mkdir()
    chunk = _write_chunk(
        chunks_dir / "only-0.parquet",
        [
            {
                "metric_id": "z",
                "metric_location": "l",
                "breakdown_properties": "{}",
                "view_date": "2024-01-01",
                "scenario": 1,
                "metric_value": 99.0,
            }
        ],
    )
    Writer(tmp_path).merge_results([chunk])
    result_file = next((tmp_path / "results").glob("*.parquet"))
    df = pl.read_parquet(result_file)
    assert len(df) == 1
    assert df["metric_value"][0] == pytest.approx(99.0)
