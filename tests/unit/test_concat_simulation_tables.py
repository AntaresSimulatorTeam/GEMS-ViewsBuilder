# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import polars as pl

from gems_views_builder.input.simulation_table import SimulationTable
from gems_views_builder.input.view_building_input_data import concat_simulation_tables
from tests.common import SIMULATION_TABLE_ROW


def test_concat_simulation_tables_combines_rows_from_every_table() -> None:
    # Arrange
    first_table = SimulationTable(pl.DataFrame([SIMULATION_TABLE_ROW]).lazy())
    second_table = SimulationTable(pl.DataFrame([SIMULATION_TABLE_ROW]).lazy())

    # Act
    concatenated = concat_simulation_tables([first_table, second_table])

    # Assert
    result = concatenated.collect()
    assert result.height == 2
    assert result["component"].to_list() == ["comp", "comp"]
