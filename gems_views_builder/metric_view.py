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
    """View for a single computed metric, stored as a parquet file."""

    file_path: Path

    def __del__(self) -> None:
        logging.debug(f"Cleaning metric view {self.file_path}")
        self.file_path.unlink(missing_ok=True)
