# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl

from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import (
    PERSISTENT_SIMULATION_TABLE_COLUMNS,
    PersistentSimulationTable,
    SimulationTable,
    filter_simulation_table,
)
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.validation.simulation_tables import validate_columns


@dataclass
class ViewBuildingInputData:
    """Inputs required by the view-building algorithm after preparation steps."""

    persistent_st: PersistentSimulationTable
    view_config: ViewConfig


def create_view_building_input(raw_input_data: RawInputData) -> ViewBuildingInputData:
    """Resolve catalog metrics, filter the simulation table, and assemble view-building inputs."""
    raw_input_data.view_config.fetch_metrics(raw_input_data.catalogs)
    concatenated_st = concat_simulation_tables(raw_input_data.simulation_tables)
    persistent_st = filter_simulation_table(concatenated_st, raw_input_data.calendar)
    validate_columns(persistent_st.dataframe, PERSISTENT_SIMULATION_TABLE_COLUMNS, "PersistentSimulationTable")

    return ViewBuildingInputData(
        persistent_st=persistent_st,
        view_config=raw_input_data.view_config,
    )


def concat_simulation_tables(simulation_tables: list[SimulationTable]) -> pl.LazyFrame:
    return pl.concat([table.dataframe for table in simulation_tables])
