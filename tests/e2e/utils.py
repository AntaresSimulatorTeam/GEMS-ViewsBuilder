# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from gems_views_builder.input.component import (
    build_component_port_connections,
    create_components,
    group_components_by_taxon,
    supply_components_with_locations,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import Library
from gems_views_builder.input.simulation_table import FilteredSimulationTable
from gems_views_builder.input.taxonomy import Taxonomy
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.validation.catalog_taxonomy_validator import validate_catalogs_against_taxonomy
from gems_views_builder.view.views_builder import ViewBuilder


def make_raw_component(component_id: str, model_id: str, properties: dict[str, str]) -> Any:
    return SimpleNamespace(id=component_id, model=SimpleNamespace(id=model_id), properties=properties)


def make_raw_connection(component1: str, port1: str, component2: str, port2: str) -> Any:
    return SimpleNamespace(component1=component1, port1=port1, component2=component2, port2=port2)


def build_input_data(
    input_dir: Path,
    raw_components: list[Any],
    raw_connections: list[Any],
    taxonomy_category_by_model: dict[str, str],
    view_config: ViewConfig,
    filtered_st: FilteredSimulationTable,
) -> InputData:
    """
    Build a real InputData, skipping only the disk-reading Loader.load() step:
    system/library/taxonomy are minimal but real objects, populated with just
    enough to drive the pipeline steps under test.
    """
    return InputData(
        input_data_path=input_dir,
        taxonomy=Taxonomy(id="taxonomy"),
        library=Library(
            id="lib",
            description="",
            port_types=[],
            models={},
            models_by_taxonomy_category={},
            taxonomy_category_by_model=taxonomy_category_by_model,
        ),
        system=cast(Any, SimpleNamespace(components=raw_components, connections=raw_connections)),
        view_config=view_config,
        filtered_st=filtered_st,
    )


def run_pipeline(input_data: InputData, input_dir: Path) -> list[MetricView]:
    """
    Mirror run_view_building_process's body without Loader.load() step.
    """
    components = create_components(input_data.system.components)
    supply_components_with_taxonomy_categories(components, input_data.library.taxonomy_category_by_model)
    component_port_connections = build_component_port_connections(input_data.system.connections)
    supply_components_with_port_connections(components, component_port_connections)
    components_by_taxon = group_components_by_taxon(components)
    supply_components_with_locations(
        components_by_taxon,
        input_data.view_config.get_metrics(),
        input_data.view_config.location_taxonomy_category,
    )

    metric_structure_table_builder = MetricStructureTableBuilder(
        input_data.view_config.location_taxonomy_category,
        components_by_taxon,
        input_data.view_config.extra_locations,
    )
    validate_catalogs_against_taxonomy(input_dir, input_data.view_config.catalog_ids, input_data.taxonomy)

    return ViewBuilder(input_data, metric_structure_table_builder).build()
