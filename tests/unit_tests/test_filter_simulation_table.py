import sys
from pathlib import Path

# Project root on path so "from src import ..." works
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402

from src import Calendar, SimulationTable  # noqa: E402

CALENDARS_DIR = ROOT_DIR / "resources" / "test_files" / "calendars"
SIMULATION_TABLES_DIR = ROOT_DIR / "resources" / "test_files" / "simulation_tables"


@pytest.mark.parametrize(
    "calendar_file, simulation_table_file, expected_filtered_simulation_table_file",
    [
        (
            CALENDARS_DIR / "calendar_daily_block1.csv",
            SIMULATION_TABLES_DIR / "simulation_table_daily_one_year.csv",
            SIMULATION_TABLES_DIR / "filtered_simulation_table_daily_block1.csv",
        ),
    ],
)
def test_filter_simulation_table(
    calendar_file: Path, simulation_table_file: Path, expected_filtered_simulation_table_file: Path
) -> None:
    calendar = Calendar(calendar_file)
    simulation_table = SimulationTable(simulation_table_file)

    filtered_simulation_table = simulation_table.filter_simulation_table(
        calendar, output_path=expected_filtered_simulation_table_file
    )
    # Filtered table should match original (calendar includes all relevant blocks)
    assert filtered_simulation_table.equals(simulation_table.dataframe)
