# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Component model and factory helpers."""

from gems_views_builder.input.component.component import Component
from gems_views_builder.input.component.component_factory import (
    build_component_port_connections,
    create_components,
    endpoint,
    group_components_by_taxon,
    supply_components_with_locations,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.component.connection import ConnectionsThroughPort

__all__ = [
    "Component",
    "ConnectionsThroughPort",
    "build_component_port_connections",
    "create_components",
    "endpoint",
    "group_components_by_taxon",
    "supply_components_with_locations",
    "supply_components_with_port_connections",
    "supply_components_with_taxonomy_categories",
]
