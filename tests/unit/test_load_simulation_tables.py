# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.input.simulation_table import SimulationTable, load_simulation_tables
from tests.common import SIMULATION_TABLE_ROW


def write_simulation_table(path: Path) -> None:
    pl.DataFrame([SIMULATION_TABLE_ROW]).write_parquet(path)


def test_load_simulation_tables_returns_one_table_per_path(tmp_path: Path) -> None:
    # Arrange
    first_path = tmp_path / "simulation_table-1.parquet"
    second_path = tmp_path / "simulation_table-2.parquet"
    write_simulation_table(first_path)
    write_simulation_table(second_path)

    # Act
    simulation_tables = load_simulation_tables([first_path, second_path])

    # Assert
    assert len(simulation_tables) == 2
    assert all(isinstance(table, SimulationTable) for table in simulation_tables)
    assert [table.dataframe.collect().item(0, "value") for table in simulation_tables] == [1.0, 1.0]


def test_load_simulation_tables_raises_when_one_of_several_files_has_invalid_extension(tmp_path: Path) -> None:
    # Arrange
    valid_path = tmp_path / "simulation_table-1.parquet"
    write_simulation_table(valid_path)
    invalid_path = tmp_path / "simulation_table-2.txt"
    invalid_path.touch()

    # Act & Assert
    with pytest.raises(ValueError, match=r"is not a parquet or csv file"):
        load_simulation_tables([valid_path, invalid_path])
