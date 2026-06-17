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

"""GEMS-ViewsBuilder public package namespace."""

from gems.model.parsing import (  # type: ignore
    ConstraintSchema,
    ExtraOutputSchema,
    LibrarySchema,
    ModelPortSchema,
    ModelSchema,
    ObjectiveContributionSchema,
    ParameterSchema,
    PortFieldDefinitionSchema,
    PortTypeSchema,
    VariableSchema,
)

from gems_views_builder.input.calendar import Calendar, load_calendar
from gems_views_builder.input.catalog import (
    Catalog,
    Metric,
    Term,
    TermsOperator,
    TimeOperator,
    load_catalog,
)
from gems_views_builder.input.library import Library, load_library
from gems_views_builder.input.simulation_table import FilteredSimulationTable, SimulationTable
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem, load_taxonomy
from gems_views_builder.input.view_config import TimeAggregation, ViewConfig, load_view_config
from gems_views_builder.metrics_builder import MetricStructureBuilder, MetricStructureTable
from gems_views_builder.views_builder import ViewBuilder

__all__ = [
    "Calendar",
    "load_calendar",
    "FilteredSimulationTable",
    "SimulationTable",
    "Catalog",
    "load_catalog",
    "Metric",
    "Term",
    "TermsOperator",
    "TimeOperator",
    "ConstraintSchema",
    "ExtraOutputSchema",
    "Library",
    "LibrarySchema",
    "load_library",
    "ModelSchema",
    "ModelPortSchema",
    "ObjectiveContributionSchema",
    "ParameterSchema",
    "PortFieldDefinitionSchema",
    "PortTypeSchema",
    "VariableSchema",
    "Taxonomy",
    "TaxonomyCategory",
    "TaxonomyItem",
    "load_taxonomy",
    "TimeAggregation",
    "ViewConfig",
    "load_view_config",
    "MetricStructureBuilder",
    "MetricStructureTable",
    "ViewBuilder",
    "System",
]
