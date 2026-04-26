from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from gems_views_builder.common import PARQUET_COMPRESSION, PARQUET_COMPRESSION_LEVEL, PARQUET_ROW_GROUP_SIZE
from gems_views_builder.metrics_builder import MetricStructureTable


class Writer:
    def __init__(self, input_data_path: Path) -> None:
        self.input_data_path = input_data_path

    def consolidate_results(self, chunk_paths: list[Path]) -> Path | None:
        if not chunk_paths:
            return None
        results_dir = self.input_data_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_path = results_dir / f"view{timestamp}.parquet"
        pl.scan_parquet(chunk_paths).sink_parquet(
            out_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
        )
        for chunk_path in chunk_paths:
            chunk_path.unlink(missing_ok=True)
        return out_path

    def write_metric_structure_table(self, metric_structure_table: MetricStructureTable, metric_id: str) -> Path:
        metric_structure_dir = self.input_data_path / "views" / "metric_structure"
        metric_structure_dir.mkdir(parents=True, exist_ok=True)
        metric_structure_path = metric_structure_dir / f"{metric_id}.parquet"
        metric_structure_table.dataframe.write_parquet(
            metric_structure_path,
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            row_group_size=PARQUET_ROW_GROUP_SIZE,
            use_pyarrow=True,
            pyarrow_options={"data_page_version": "2.0"},
        )
        return metric_structure_path
