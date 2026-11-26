# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl

from gems_views_builder.aggregators.aggregations_processor import AggregationProcessor
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import (
    PersistentSimulationTable,
    SimulationTable,
    filter_simulation_table,
)
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_structure_table import MetricStructureTable


@dataclass
class ViewBuildingInput:
    """Inputs of the view-building algorithm for one view config."""

    view_config: ViewConfig
    simulation_table_buckets: dict[int, PersistentSimulationTable]
    metric_structure_tables: dict[str, MetricStructureTable]
    aggregation_processor: AggregationProcessor


def make_filtered_simulation_table(
    raw_input_data: RawInputData, pair_lookup_table: pl.LazyFrame
) -> dict[int, PersistentSimulationTable]:
    concatenated_st = concat_simulation_tables(raw_input_data.simulation_tables)
    return filter_simulation_table(concatenated_st, raw_input_data.calendar, pair_lookup_table)


def create_view_building_input(
    simulation_table_buckets: dict[int, PersistentSimulationTable],
    view_config: ViewConfig,
    metric_structure_tables: dict[str, MetricStructureTable],
) -> ViewBuildingInput:
    return ViewBuildingInput(
        view_config=view_config,
        simulation_table_buckets=simulation_table_buckets,
        metric_structure_tables=metric_structure_tables,
        aggregation_processor=AggregationProcessor(view_config),
    )


def concat_simulation_tables(simulation_tables: list[SimulationTable]) -> pl.LazyFrame:
    return pl.concat([table.dataframe for table in simulation_tables])
