# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import mmh3
import polars as pl
from polars import DataFrame, LazyFrame
from polars.io.partition import FileProviderArgs

PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000
BUCKET_COUNT = 64
LOG_DIR = Path.cwd() / "logs"


def murmur_hash(component: str, output: str) -> int:
    """
    Chance of at least one collision among n distinct pairs is about n(n-1)/2^65,
    or 100 * n(n-1)/2^65 percent.
    It grows with the square of n:
    1000 ~ 2.7e-12%,
    10 000 ~ 2.7e-10%,
    20 000 ~ 1.1e-9%,
    50 000 ~ 6.8e-9%,
    100 000 ~ 2.7e-8%,
    1 000 000 ~ 2.7e-6%.
    Important this computation is based on TYND2040 input data.
    """
    return mmh3.hash64(f"{component}\x1f{output}", signed=True)[0]  # 64bit


def sink_to_parquet(dataframe: LazyFrame | DataFrame, path: Path) -> None:
    dataframe.sink_parquet(
        path,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        row_group_size=PARQUET_ROW_GROUP_SIZE,
    )


def bucket_id_file_path(args: FileProviderArgs) -> str:
    bucket_id = args.partition_keys["bucket_id"][0]
    return f"filtered_simulation_table_bucket_{bucket_id}.parquet"


def sink_by_bucket_id(simulation_table: pl.LazyFrame, path: Path) -> None:
    logging.info("Decomposing simulation table into buckets")
    simulation_table.sink_parquet(
        pl.PartitionBy(
            path,
            key="bucket_id",
            include_key=True,
            file_path_provider=bucket_id_file_path,
        ),
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        row_group_size=PARQUET_ROW_GROUP_SIZE,
        mkdir=True,
    )
    logging.info("Decomposed simulation table into buckets")


def make_log_file(log_dir: Path | None = None) -> Path:
    log_dir = log_dir if log_dir is not None else LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%fZ")
    return log_dir / f"gems-views-builder-pipeline-run-{timestamp}.log"


def configure_logging(verbose: bool = False, log_dir: Path | None = None) -> None:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    log_file = make_log_file(log_dir)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
