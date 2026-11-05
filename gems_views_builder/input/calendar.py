# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from pathlib import Path

import polars as pl

CALENDAR_SCHEMA = {
    "absolute_time_index": pl.Int64,
    "block": pl.Int64,
    "granular_date": pl.Datetime,
}


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
    """Load and validate a calendar CSV file into a plain Calendar dataclass."""
    calendar = pl.scan_csv(calendar_file_path, schema=CALENDAR_SCHEMA)
    try:
        _check_calendar_columns(calendar=calendar)
    except ValueError as exc:
        raise ValueError(f"Calendar '{calendar_file_path.stem}' is invalid: {exc}") from exc
    return Calendar(id=calendar_file_path.stem, dataframe=calendar)


def _check_calendar_columns(calendar: pl.LazyFrame) -> None:
    # # calendar isn't big we could perform safely streaming
    calendar_df = calendar.collect(engine="streaming").drop_nulls()

    _check_time_indices_conformity(calendar_df=calendar_df)
    _check_dates_conformity(calendar_df=calendar_df)


def _check_time_indices_conformity(calendar_df: pl.DataFrame) -> None:
    # absolute_time_index must equal row index (contiguous 0..N-1, no misses)
    abs_time_ind = calendar_df.get_column("absolute_time_index")
    exp_abs_time_ind = pl.arange(0, calendar_df.height, eager=True).cast(abs_time_ind.dtype)
    if not (abs_time_ind == exp_abs_time_ind).all():
        raise ValueError("Calendar has non-contiguous or mismatched absolute_time_index values")


def _check_dates_conformity(calendar_df: pl.DataFrame) -> None:
    # granular_date difference between adjacent rows must be constant
    dates = calendar_df.get_column("granular_date")
    dates_diffs = dates.diff()[1:].n_unique()
    if dates_diffs > 1:
        raise ValueError("Calendar has non-constant differences between consecutive granular_date values")
