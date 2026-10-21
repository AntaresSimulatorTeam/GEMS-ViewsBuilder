# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass

import polars as pl

from gems_views_builder.aggregators.aggregations_processor import AggregationProcessor
from gems_views_builder.input.component import Component
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import (
    FilteredSimulationTable,
    SimulationTable,
    filter_simulation_table,
)
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


@dataclass
class ViewBuildingInput:
    """Inputs of the view-building algorithm for one view config."""

    view_config: ViewConfig
    filtered_st: FilteredSimulationTable
    metric_structure_table_builder: MetricStructureTableBuilder
    aggregation_processor: AggregationProcessor


def make_filtered_simulation_table(raw_input_data: RawInputData) -> FilteredSimulationTable:
    concatenated_st = concat_simulation_tables(raw_input_data.simulation_tables)
    return filter_simulation_table(concatenated_st, raw_input_data.calendar)


def create_view_building_input(
    filtered_st: FilteredSimulationTable,
    view_config: ViewConfig,
    components_by_taxon: dict[str, list[Component]],
) -> ViewBuildingInput:
    return ViewBuildingInput(
        view_config=view_config,
        filtered_st=filtered_st,
        metric_structure_table_builder=MetricStructureTableBuilder(view_config, components_by_taxon),
        aggregation_processor=AggregationProcessor(view_config),
    )


def concat_simulation_tables(simulation_tables: list[SimulationTable]) -> pl.LazyFrame:
    return pl.concat([table.dataframe for table in simulation_tables])
