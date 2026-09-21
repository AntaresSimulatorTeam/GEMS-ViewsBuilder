# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest
from polars import DataFrame

from gems_views_builder.input.simulation_table import FILTERED_SIMULATION_TABLE_COLUMNS, SimulationTable
from gems_views_builder.validation.simulation_tables import validate_columns, validate_simulation_tables_consistency
from tests.common import SIMULATION_TABLE_ROW, make_simulation_table_row


def test_validate_simulation_tables_consistency_pass() -> None:
    # Arrange
    simulation_table = SimulationTable(dataframe=DataFrame([SIMULATION_TABLE_ROW]).lazy())

    # Act + Assert
    validate_simulation_tables_consistency([simulation_table])


def test_validate_simulation_tables_consistency_fails_when_there_are_missing_columns() -> None:
    # Arrange
    row = make_simulation_table_row()
    del row["basis_status"]
    simulation_table = SimulationTable(dataframe=DataFrame([row]).lazy())

    # Act + Assert
    with pytest.raises(ValueError, match=r"SimulationTable has invalid columns: Missing columns:.*basis_status"):
        validate_simulation_tables_consistency([simulation_table])


def test_validate_filter_simulation_table_consistency_pass() -> None:
    # Arrange
    dataframe = DataFrame([make_simulation_table_row(granular_date="2026-01-01")]).lazy()

    # Act + Assert
    validate_columns(dataframe, FILTERED_SIMULATION_TABLE_COLUMNS, "FilteredSimulationTable")


def test_validate_filter_simulation_table_consistency_fails_when_there_are_missing_columns() -> None:
    # Arrange
    dataframe = DataFrame([SIMULATION_TABLE_ROW]).lazy()

    # Act + Assert
    with pytest.raises(
        ValueError, match=r"FilteredSimulationTable has invalid columns: Missing columns:.*granular_date"
    ):
        validate_columns(dataframe, FILTERED_SIMULATION_TABLE_COLUMNS, "FilteredSimulationTable")
