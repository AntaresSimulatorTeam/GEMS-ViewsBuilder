from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE, logger


class Writer:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def consolidate_results(self, chunk_paths: list[Path]) -> Path | None:
        if not chunk_paths:
            logger.info("No metric chunks to consolidate — skipping result file creation")
            return None
        results_dir = self.input_data_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = results_dir / f"view{timestamp}.parquet"
        logger.info(f"Consolidating {len(chunk_paths)} metric chunk(s) into {out_path}")
        pl.scan_parquet(chunk_paths).sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        for chunk_path in chunk_paths:
            chunk_path.unlink(missing_ok=True)
        logger.info(f"Results written to {out_path}")
        return out_path

    def write_metric_structure_table(self, metric_structure_table: pl.DataFrame, metric_id: str) -> Path:
        metric_structure_dir = self.input_data_path / "views" / "metric_structure"
        metric_structure_dir.mkdir(parents=True, exist_ok=True)
        metric_structure_path = metric_structure_dir / f"{metric_id}.parquet"
        logger.info(f"[{metric_id}] Writing metric structure table to {metric_structure_path}")
        metric_structure_table.write_parquet(
            metric_structure_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
            use_pyarrow=True,
            pyarrow_options={"data_page_version": "2.0"},
        )
        return metric_structure_path
