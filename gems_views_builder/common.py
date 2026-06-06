import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000

_LOG_FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("gems_views_builder")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(_console_handler)

_file_handler: logging.FileHandler | None = None


def configure_pipeline_run(input_data_path: Path) -> Path:
    global _file_handler
    close_pipeline_run()
    logs_dir = input_data_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    log_path = logs_dir / f"pipeline-{timestamp}.log"
    _file_handler = logging.FileHandler(log_path, encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(_file_handler)
    return log_path


def close_pipeline_run() -> None:
    global _file_handler
    if _file_handler is None:
        return
    logger.removeHandler(_file_handler)
    _file_handler.close()
    _file_handler = None
