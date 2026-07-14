# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import polars as pl

PARQUET_COMPRESSION: Literal["zstd"] = "zstd"
PARQUET_COMPRESSION_LEVEL = 3
PARQUET_ROW_GROUP_SIZE = 64_000

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


LOG_DIR = Path.cwd() / "logs"


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
