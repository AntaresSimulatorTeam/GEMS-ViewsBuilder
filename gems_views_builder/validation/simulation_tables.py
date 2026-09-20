# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from polars import LazyFrame

from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import SIMULATION_TABLE_COLUMNS


def validate_simulation_tables_consistency(raw_input_data: RawInputData) -> None:
    for simulation_table in raw_input_data.simulation_tables:
        validate_columns(simulation_table.dataframe, SIMULATION_TABLE_COLUMNS, "SimulationTable")


def validate_columns(dataframe: LazyFrame, expected_columns: frozenset[str], label: str) -> None:
    columns = frozenset(dataframe.collect_schema().names())
    missing = expected_columns - columns
    extra = columns - expected_columns
    errors: list[str] = []
    if missing:
        errors.append(f"Missing columns: {missing}")
    if extra:
        errors.append(f"Unexpected columns: {extra}")
    if errors:
        raise ValueError(f"{label} has invalid columns: {'; '.join(errors)}")
