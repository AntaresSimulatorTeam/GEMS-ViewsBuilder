import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000

log_file = (
    Path(__file__).resolve().parent.parent
    / "logs"
    / f"gems-views-builder-pipeline-run-{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M-%S-%fZ')}.log"
)
log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=str(log_file),
    filemode="a",
    encoding="utf-8",  # Ensure logs are written in UTF-8
    force=True,  # Always attach file handler even under pytest, needed for logger tests
)
