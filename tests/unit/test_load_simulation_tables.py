# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import polars as pl
import pytest

from gems_views_builder.input.simulation_table import (
    SimulationTable,
    concat_simulation_tables,
    load_simulation_tables,
)

SIMULATION_TABLE_ROW = {
    "block": "b1",
    "component": "comp",
    "output": "out",
    "absolute_time_index": 1,
    "block_time_index": 1,
    "scenario_index": 1,
    "value": 1.0,
    "basis_status": "ok",
}


def write_simulation_table(path: Path) -> None:
    pl.DataFrame([SIMULATION_TABLE_ROW]).write_parquet(path)


def test_load_simulation_tables_returns_one_table_per_path_in_order(tmp_path: Path) -> None:
    # Arrange
    first_path = tmp_path / "simulation_table-1.parquet"
    second_path = tmp_path / "simulation_table-2.parquet"
    write_simulation_table(first_path)
    write_simulation_table(second_path)

    # Act
    simulation_tables = load_simulation_tables([first_path, second_path])

    # Assert
    assert len(simulation_tables) == 2
    assert type(simulation_tables) == list[SimulationTable]
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


def test_concat_simulation_tables_raises_when_list_is_empty() -> None:
    # Act & Assert
    with pytest.raises(ValueError, match="No simulation tables to concat"):
        concat_simulation_tables([])


def test_concat_simulation_tables_combines_rows_from_every_table() -> None:
    # Arrange
    first_table = SimulationTable(pl.DataFrame([SIMULATION_TABLE_ROW]).lazy())
    second_table = SimulationTable(pl.DataFrame([SIMULATION_TABLE_ROW]).lazy())

    # Act
    concatenated = concat_simulation_tables([first_table, second_table])

    # Assert
    result = concatenated.collect()
    assert result.height == 2
    assert result["component"].to_list() == ["comp","comp"]
