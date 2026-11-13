# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from polars import LazyFrame, PartitionBy

PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000

LOG_DIR = Path.cwd() / "logs"


def sink_to_parquet(dataframe: LazyFrame, path: Path | PartitionBy) -> None:
    dataframe.sink_parquet(
        path,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        row_group_size=PARQUET_ROW_GROUP_SIZE,
    )


def peak_rss_gib() -> float:
    """Peak resident memory of this process so far, in GiB (0 where unavailable)."""
    try:
        import resource
    except ImportError:  # Windows
        return 0.0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB, macOS reports bytes.
    return peak / 2**30 if sys.platform == "darwin" else peak / 2**20


@contextmanager
def timed_step(label: str) -> Iterator[None]:
    """Log the wall time of the enclosed block and the process's peak memory so far."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logging.info(f"TIMING {label}: {elapsed:.3f}s (peak RSS {peak_rss_gib():.2f} GiB)")


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
