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

from dataclasses import dataclass
from datetime import datetime

import polars as pl


@dataclass
class Calendar:
    """
    In memory representation of the calendar.csv file.
    Id: calendar filename.
    1st col: absolute time index.
    2nd col: block
    3rd col: granular date
    """

    id: str
    dataframe: pl.DataFrame

    def abs_time_index_to_block(self, abs_time_index: int) -> int:
        raise NotImplementedError()

    def abs_time_index_to_date(self, abs_time_index: int) -> datetime:
        raise NotImplementedError()
