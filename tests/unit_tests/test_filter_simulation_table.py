import sys
from pathlib import Path

# Project root on path so "from src import ..." works
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import polars as pl  # noqa: E402
import pytest  # noqa: E402

from src import Calendar, SimulationTable  # noqa: E402

CALENDARS_DIR = ROOT_DIR / "resources" / "test_files" / "calendars"
SIMULATION_TABLES_DIR = ROOT_DIR / "resources" / "test_files" / "simulation_tables"


# Calendar + simulation table pairs to run the same tests on
FILTER_TEST_CASES = [
    (CALENDARS_DIR / "calendar_daily_block1.csv", SIMULATION_TABLES_DIR / "simulation_table_daily_one_year.csv"),
    (CALENDARS_DIR / "calendar_daily_random_blocks.csv", SIMULATION_TABLES_DIR / "simulation_table_daily_one_year.csv"),
    (CALENDARS_DIR / "calendar_hourly_block1.csv", SIMULATION_TABLES_DIR / "simulation_table_hourly_one_week.csv"),
    (
        CALENDARS_DIR / "calendar_hourly_random_blocks.csv",
        SIMULATION_TABLES_DIR / "simulation_table_hourly_one_week.csv",
    ),
]


# ---- Parametrized integration test: logical assertions (no golden overwrite) ----
@pytest.mark.parametrize("calendar_file, simulation_table_file", FILTER_TEST_CASES)
def test_filter_simulation_table_logical(calendar_file: Path, simulation_table_file: Path) -> None:
    """Filtered result must satisfy: every row (absolute_time_index, block) in calendar, correct count, rows from sim table."""
    calendar = Calendar(calendar_file)
    simulation_table = SimulationTable(simulation_table_file)

    filtered = simulation_table.filter_simulation_table(calendar, output_path=None)

    # 1. Every row in the result has (absolute_time_index, block) present in the calendar
    in_calendar = filtered.join(calendar.dataframe, on=["absolute_time_index", "block"], how="semi")
    assert in_calendar.height == filtered.height, (
        "Every filtered row must have (absolute_time_index, block) in the calendar"
    )

    # 2. Result has exactly the rows that belong to the calendar block (spec: inner join + block match)
    expected_count = (
        simulation_table.dataframe.join(calendar.dataframe, on="absolute_time_index", how="inner")
        .filter(pl.col("block") == pl.col("block_right"))
        .height
    )
    assert filtered.height == expected_count, (
        "Filtered row count must equal simulation rows whose (absolute_time_index, block) is in the calendar"
    )


@pytest.mark.parametrize("calendar_file, simulation_table_file", FILTER_TEST_CASES)
def test_filter_simulation_table_writes_csv(calendar_file: Path, simulation_table_file: Path) -> None:
    """When output_path is set, the filtered table is written to CSV and matches the returned DataFrame.
    Output is written under SIMULATION_TABLES_DIR and removed at the end of the test."""
    calendar = Calendar(calendar_file)
    simulation_table = SimulationTable(simulation_table_file)
    out_file = SIMULATION_TABLES_DIR / f"filtered_{calendar_file.stem}.csv"
    try:
        result = simulation_table.filter_simulation_table(calendar, output_path=out_file)
        assert out_file.exists(), "Output CSV should be created"
        written = pl.read_csv(out_file, null_values=["None"])
        assert result.equals(written), "Written CSV content should match returned DataFrame"
    finally:
        if out_file.exists():
            out_file.unlink()
