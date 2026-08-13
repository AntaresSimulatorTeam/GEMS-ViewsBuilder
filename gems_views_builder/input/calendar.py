# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from pathlib import Path

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
    calendar: pl.LazyFrame


def load_calendar(calendar_file_path: Path) -> Calendar:
    """Load and validate a calendar CSV file into a plain Calendar dataclass."""
    calendar = pl.scan_csv(calendar_file_path, try_parse_dates=True)
    _check_calendar_columns(calendar_id=calendar_file_path.stem, calendar=calendar)
    return Calendar(id=calendar_file_path.stem, calendar=calendar)


def _check_calendar_columns(calendar_id: str, calendar: pl.LazyFrame) -> None:
    calendar_df = calendar.collect(
        engine="streaming"
    ).drop_nulls()  # # calendar isn't big we could perform safely streaming
    if calendar_df.is_empty():
        return

    _check_for_missing_or_unexpected_columns(calendar_id=calendar_id, calendar_df=calendar_df)
    _check_time_indices_conformity(calendar_id=calendar_id, calendar_df=calendar_df)
    _check_dates_conformity(calendar_id=calendar_id, calendar_df=calendar_df)


def _check_for_missing_or_unexpected_columns(calendar_id: str, calendar_df: pl.DataFrame) -> None:
    actual_column_titles = calendar_df.schema.keys()
    if actual_column_titles != EXPECTED_CALENDAR_COLUMNS:
        missing = EXPECTED_CALENDAR_COLUMNS - actual_column_titles
        unexpected = actual_column_titles - EXPECTED_CALENDAR_COLUMNS
        parts: list[str] = []
        if missing:
            parts.append(f"missing columns: {missing}")
        if unexpected:
            parts.append(f"unexpected columns: {unexpected}")
        if not missing and not unexpected:
            parts.append(f"wrong column order: expected {EXPECTED_CALENDAR_COLUMNS}, got {actual_column_titles}")
        else:
            parts.append(f"actual columns: {actual_column_titles}")
        raise ValueError(f"Calendar '{calendar_id}' has invalid columns: {'; '.join(parts)}")


def _check_time_indices_conformity(calendar_id: str, calendar_df: pl.DataFrame) -> None:
    # absolute_time_index must equal row index (contiguous 0..N-1, no misses)
    abs_time_ind = calendar_df.get_column("absolute_time_index")
    exp_abs_time_ind = pl.arange(0, calendar_df.height, eager=True).cast(abs_time_ind.dtype)
    if not (abs_time_ind == exp_abs_time_ind).all():
        raise ValueError(f"Calendar '{calendar_id}' has non-contiguous or mismatched absolute_time_index values")


def _check_dates_conformity(calendar_id: str, calendar_df: pl.DataFrame) -> None:
    # granular_date difference between adjacent rows must be constant
    dates = calendar_df.get_column("granular_date")
    if dates.is_empty():
        return

    time_index_difference = dates.diff()[1:]

    if not (time_index_difference == time_index_difference[0]).all():
        raise ValueError(
            f"Calendar '{calendar_id}' has non-constant differences between consecutive granular_date values"
        )
