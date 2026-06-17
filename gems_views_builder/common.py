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


# # Utils functions for ViewBuilder class
# # They don't use any class attributes, so they are not part of the class
def clean_intermediate_metric(metric_view_parquet_path: Path, metric_structure_path: Path) -> None:
    logging.info(f"Cleaning intermediate metric {metric_view_parquet_path} and {metric_structure_path}")
    metric_view_parquet_path.unlink(missing_ok=True)
    metric_structure_path.unlink(missing_ok=True)


def clean_filtered_simulation_table(filtered_simulation_table_path: Path) -> None:
    logging.info(f"Cleaning filtered simulation table {filtered_simulation_table_path}")
    filtered_simulation_table_path.unlink(missing_ok=True)
