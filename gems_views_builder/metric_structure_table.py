# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import shutil
import tempfile
from pathlib import Path

import polars as pl

from gems_views_builder.common import (
    PARQUET_COMPRESSION,
    PARQUET_COMPRESSION_LEVEL,
    PARQUET_ROW_GROUP_SIZE,
)

METRIC_STRUCTURE_TABLE_SCHEMA = pl.Schema(
    {
        "metric_id": pl.Utf8,
        "component": pl.Utf8,
        "metric_location": pl.Utf8,
        "breakdown_properties": pl.Utf8,
        "output": pl.Utf8,
        "weight_output_id": pl.UInt8,  # In order to save data because it isn't used
        "pair_id": pl.Int64,
        "chunk_id": pl.UInt8,
    }
)


class MetricStructureTable:
    """On-disk metric structure table, ready for lazy scanning."""

    # # One edge case here is that directories never be cleaned up, only will be cleaned while calling destructor
    def __init__(self, rows: list[dict[str, object]], metric_id: str) -> None:
        self._tmp_root = Path(tempfile.mkdtemp())
        logging.info(f"[{metric_id}] Metric structure table has {len(rows)} rows")

        self.rows = pl.DataFrame(rows, schema=METRIC_STRUCTURE_TABLE_SCHEMA)
        metric_structure_dir = self._tmp_root / "views" / "metric_structure"
        metric_structure_dir.mkdir(parents=True, exist_ok=True)
        file_path = metric_structure_dir / f"{metric_id}.parquet"
        self.rows.write_parquet(
            file_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
            use_pyarrow=True,
            pyarrow_options={"data_page_version": "2.0"},
        )
        # # The real advantage of polars - later we will use it to perform SQL operations
        # # It's better to perform operations on lazy data frame, rather than one pl.dataframe && pl.lazyDataFrame
        self.dataframe: pl.LazyFrame = pl.scan_parquet(file_path)

    def get_unique_pair_lookup_rows(self) -> pl.LazyFrame:
        """Distinct (component, output) pairs by pair_id, keeping already-computed ids."""
        return self.dataframe.select(["component", "output", "pair_id", "chunk_id"]).unique(subset=["pair_id"])

    def get_unique_chunk_ids(self) -> list[int]:
        return [int(chunk_id) for chunk_id in self.rows.get_column("chunk_id").unique().to_list()]

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric structure {self._tmp_root}")
        shutil.rmtree(self._tmp_root, ignore_errors=True)


def get_pair_lookup_rows(ms_tables_by_view_config: dict[str, dict[str, MetricStructureTable]]) -> pl.LazyFrame:
    """Merge distinct pair-lookup rows across MSTs (dedupe by pair_id, no re-hash)."""
    frames = [
        ms_table.get_unique_pair_lookup_rows()
        for ms_tables_by_metric in ms_tables_by_view_config.values()
        for ms_table in ms_tables_by_metric.values()
    ]
    if not frames:
        raise ValueError("No metric structure tables provided")
    return pl.concat(frames).unique(subset=["pair_id"])
