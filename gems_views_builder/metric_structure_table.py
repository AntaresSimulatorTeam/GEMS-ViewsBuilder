import logging
import shutil
import tempfile
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE


class MetricStructureTable:
    """On-disk metric structure table, ready for lazy scanning."""

    # # One edge case here is that directories never be cleaned up, only will be cleaned while calling destructor
    def __init__(self, rows: pl.DataFrame, metric_id: str) -> None:
        self._tmp_root = Path(tempfile.mkdtemp())
        if rows.is_empty():
            logging.info(f"[{metric_id}] No matching components found — metric structure table is empty")
        else:
            logging.info(f"[{metric_id}] Metric structure table built with {len(rows)} row(s)")

        metric_structure_dir = self._tmp_root / "views" / "metric_structure"
        metric_structure_dir.mkdir(parents=True, exist_ok=True)
        file_path = metric_structure_dir / f"{metric_id}.parquet"
        rows.write_parquet(
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

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric structure {self._tmp_root}")
        shutil.rmtree(self._tmp_root, ignore_errors=True)
