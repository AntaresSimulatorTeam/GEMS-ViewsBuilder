# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl

# Expected CSV columns (name and order)
EXPECTED_CALENDAR_COLUMNS: set[str] = {"absolute_time_index", "block", "granular_date"}


@dataclass
class Calendar:
    """
    Calendar.csv representation backed by a lazy Polars frame.
    Id: calendar filename.
    1st col: absolute time index.
    2nd col: block
    3rd col: granular date
    """

    id: str
    dataframe: pl.LazyFrame
