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

"""Component model and factory helpers."""

from gems_views_builder.input.component.component import Component, format_metric_location
from gems_views_builder.input.component.component_factory import (
    build_component_port_connections,
    create_components,
    endpoint,
    group_components_by_taxon,
    supply_components_with_locations,
    supply_components_with_port_connections,
    supply_components_with_taxonomy_categories,
)
from gems_views_builder.input.component.connection import ConnectionThroughPort

__all__ = [
    "Component",
    "ConnectionThroughPort",
    "build_component_port_connections",
    "create_components",
    "endpoint",
    "format_metric_location",
    "group_components_by_taxon",
    "supply_components_with_locations",
    "supply_components_with_port_connections",
    "supply_components_with_taxonomy_categories",
]
