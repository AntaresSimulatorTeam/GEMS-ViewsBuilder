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

from pathlib import Path

import polars as pl


class Calendar:
    """
    In memory representation of the calendar.csv file.
    Id: calendar filename.
    1st col: absolute time index.
    2nd col: block
    3rd col: granular date
    """

    def __init__(self, calendar_file_path: Path) -> None:
        """
        calendar_file: Path to the calendar.csv file
        """
        self.id = calendar_file_path.stem
        self.dataframe = self._read_calendar_file(calendar_file_path)
        self._check_calendar_columns()

    def _read_calendar_file(self, calendar_file_path: Path) -> pl.LazyFrame:
        if not calendar_file_path.exists():
            raise FileNotFoundError(f"Calendar file {calendar_file_path} not found")
        if calendar_file_path.suffix.lower() != ".csv":
            raise ValueError(f"Calendar file {calendar_file_path} is not a CSV file")
        return pl.scan_csv(calendar_file_path, try_parse_dates=True)

    def _check_calendar_columns(self) -> None:
        df = self.dataframe.collect()

        if df.columns != ["absolute_time_index", "block", "granular_date"]:
            raise ValueError(f"Calendar '{self.id}' has invalid columns")

        if df.is_empty():
            return

        # absolute_time_index must equal row index (contiguous 0..N-1, no misses)
        abs_idx = df.get_column("absolute_time_index")
        expected = pl.arange(0, df.height, eager=True).cast(abs_idx.dtype)
        if not (abs_idx == expected).all():
            raise ValueError(f"Calendar '{self.id}' has non-contiguous or mismatched absolute_time_index values")

        # granular_date difference between adjacent rows must be constant
        dates = df.get_column("granular_date")
        if dates.len() <= 1:
            return

        diffs = dates.diff()
        diffs_non_null = diffs.drop_nulls()
        if diffs_non_null.is_empty():
            return

        first_diff = diffs_non_null[0]
        if not (diffs_non_null == first_diff).all():
            raise ValueError(
                f"Calendar '{self.id}' has non-constant differences between consecutive granular_date values"
            )
