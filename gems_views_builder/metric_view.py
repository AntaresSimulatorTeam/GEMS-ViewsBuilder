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
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MetricView:
    """Temporal aggregation result for a single metric, stored as a parquet file."""

    file: Path

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.file}")
        self.file.unlink(missing_ok=True)
