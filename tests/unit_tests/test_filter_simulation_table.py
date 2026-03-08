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


# ---- Parametrized integration test: logical assertions (no golden overwrite) ----
@pytest.mark.parametrize(
    "calendar_file, simulation_table_file",
    [
        (
            CALENDARS_DIR / "calendar_daily_block1.csv",
            SIMULATION_TABLES_DIR / "simulation_table_daily_one_year.csv",
        ),
    ],
)
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


def test_filter_simulation_table_writes_csv() -> None:
    """When output_path is set, the filtered table is written to CSV and matches the returned DataFrame.
    Output is written under SIMULATION_TABLES_DIR and removed at the end of the test."""
    calendar = Calendar(CALENDARS_DIR / "calendar_daily_block1.csv")
    simulation_table = SimulationTable(SIMULATION_TABLES_DIR / "simulation_table_daily_one_year.csv")
    out_file = SIMULATION_TABLES_DIR / "filtered.csv"
    try:
        result = simulation_table.filter_simulation_table(calendar, output_path=out_file)
        assert out_file.exists(), "Output CSV should be created"
        written = pl.read_csv(out_file, null_values=["None"])
        assert result.equals(written), "Written CSV content should match returned DataFrame"
    finally:
        if out_file.exists():
            out_file.unlink()
