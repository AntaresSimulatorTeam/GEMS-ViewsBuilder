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
        "weight_output_id": pl.Utf8,
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

    def get_unique_component_output_pairs(self) -> set[tuple[str, str]]:
        return set(zip(self.rows["component"], self.rows["output"]))

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric structure {self._tmp_root}")
        shutil.rmtree(self._tmp_root, ignore_errors=True)


def get_component_output_pairs(ms_table_by_view_config_metric: dict[str, MetricStructureTable]) -> set[tuple[str, str]]:
    component_output_pairs: set[tuple[str, str]] = set()
    for ms_table in ms_table_by_view_config_metric.values():
        component_output_pairs.update(ms_table.get_unique_component_output_pairs())
    return component_output_pairs
