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
from pathlib import Path

import polars as pl

# Expected CSV columns (name and order)
EXPECTED_CALENDAR_COLUMNS: tuple[str, ...] = (
    "absolute_time_index",
    "block",
    "granular_date",
)

# Expected CSV columns (name and order)
EXPECTED_CALENDAR_COLUMNS: tuple[str, ...] = (
    "absolute_time_index",
    "block",
    "granular_date",
)


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


def load_calendar(calendar_file_path: Path) -> Calendar:
    """
    Load and validate a calendar.csv file into a plain Calendar dataclass.
    """
    calendar_id = calendar_file_path.stem
    dataframe = _read_calendar_file(calendar_file_path)
    _check_calendar_columns(calendar_id=calendar_id, dataframe=dataframe)
    return Calendar(id=calendar_id, dataframe=dataframe)


def _read_calendar_file(calendar_file_path: Path) -> pl.LazyFrame:
    if not calendar_file_path.exists():
        raise FileNotFoundError(f"Calendar file {calendar_file_path} not found")
    if calendar_file_path.suffix.lower() != ".csv":
        raise ValueError(f"Calendar file {calendar_file_path} is not a CSV file")
    return pl.scan_csv(calendar_file_path, try_parse_dates=True)


def _check_calendar_columns(calendar_id: str, dataframe: pl.LazyFrame) -> None:
    df = dataframe.collect(
        engine="streaming"
    )  # # calendar isn't big too much,so I think we could perform safely streaming

    actual = list(df.schema.keys())
    expected_columns = list(EXPECTED_CALENDAR_COLUMNS)
    if actual != expected_columns:
        actual_set = set(actual)
        expected_set = set(expected_columns)
        missing = sorted(expected_set - actual_set)
        unexpected = sorted(actual_set - expected_set)
        parts: list[str] = []
        if missing:
            parts.append(f"missing columns: {missing}")
        if unexpected:
            parts.append(f"unexpected columns: {unexpected}")
        if not missing and not unexpected:
            parts.append(f"wrong column order: expected {expected_columns}, got {actual}")
        else:
            parts.append(f"actual columns: {actual}")
        raise ValueError(f"Calendar '{calendar_id}' has invalid columns: {'; '.join(parts)}")
    if df.is_empty():
        return

    # absolute_time_index must equal row index (contiguous 0..N-1, no misses)
    abs_idx = df.get_column("absolute_time_index")
    expected_abs_idx = pl.arange(0, df.height, eager=True).cast(abs_idx.dtype)
    if not (abs_idx == expected_abs_idx).all():
        raise ValueError(f"Calendar '{calendar_id}' has non-contiguous or mismatched absolute_time_index values")

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
            f"Calendar '{calendar_id}' has non-constant differences between consecutive granular_date values"
        )
