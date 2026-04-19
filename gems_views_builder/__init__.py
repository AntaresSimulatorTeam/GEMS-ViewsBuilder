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

from gems_views_builder.calendar import Calendar, load_calendar
from gems_views_builder.catalog import (
    Catalog,
    Metric,
    Term,
    TermsOperator,
    TimeOperator,
    get_catalog_metric,
    load_catalog,
)
from gems_views_builder.library import (
    BindingConstraintDef,
    ConstraintDef,
    ExtraOutputDef,
    LibraryData,
    ModelDefinition,
    ModelLibrary,
    ObjectiveContributionDef,
    ParameterDef,
    PortDef,
    PortFieldDefinition,
    PortTypeDef,
    VariableDef,
)
from gems_views_builder.metrics import TimeAggregation, ViewConfig
from gems_views_builder.metrics_builder import MetricStructureBuilder, MetricStructureTable
from gems_views_builder.simulation_table import FilteredSimulationTable, SimulationTable
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem, load_taxonomy
from gems_views_builder.engines.base import BackendName, DataEngine, make_engine
from gems_views_builder.views import ViewBuilder

__all__ = [
    "Calendar",
    "load_calendar",
    "FilteredSimulationTable",
    "SimulationTable",
    "Catalog",
    "load_catalog",
    "get_catalog_metric",
    "Metric",
    "Term",
    "TermsOperator",
    "TimeOperator",
    "BindingConstraintDef",
    "ConstraintDef",
    "ExtraOutputDef",
    "LibraryData",
    "ModelDefinition",
    "ModelLibrary",
    "ObjectiveContributionDef",
    "ParameterDef",
    "PortDef",
    "PortFieldDefinition",
    "PortTypeDef",
    "VariableDef",
    "Taxonomy",
    "TaxonomyCategory",
    "TaxonomyItem",
    "load_taxonomy",
    "TimeAggregation",
    "ViewConfig",
    "MetricStructureBuilder",
    "MetricStructureTable",
    "ViewBuilder",
    "InputSystem",
    "BackendName",
    "DataEngine",
    "make_engine",
]
