# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import tempfile
from pathlib import Path
from shutil import rmtree

import polars as pl

from gems_views_builder.common import sink_to_parquet

PAIR_LOOKUP_TABLE_SCHEMA = pl.Schema(
    {
        "component": pl.Utf8,
        "output": pl.Utf8,
        "pair_id": pl.Int64,
        "chunk_id": pl.UInt8,
    }
)


class PersistentPairLookupTable:
    def __init__(self, pair_lookup_rows: pl.LazyFrame) -> None:
        self._tmp_root = Path(tempfile.mkdtemp())
        self.path = self._tmp_root / "pair_lookup_table.parquet"
        sink_to_parquet(pair_lookup_rows.cast(PAIR_LOOKUP_TABLE_SCHEMA).lazy(), self.path)
        self.dataframe = pl.scan_parquet(self.path)

    def __del__(self) -> None:
        logging.debug(f"Cleaning pair lookup table {self._tmp_root}")
        rmtree(self._tmp_root, ignore_errors=True)
