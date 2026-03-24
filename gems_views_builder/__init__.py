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

from src.calendar import Calendar, load_calendar
from src.catalog import Catalog, Metric, Term, TermsOperator, TimeOperator, get_catalog_metric, load_catalog
from src.library import (
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
from src.metrics import TimeAggregation, ViewConfig
from src.metrics_builder import MetricStructureBuilder, MetricStructureTable
from src.simulation_table import FilteredSimulationTable, SimulationTable
from src.system import InputSystem
from src.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem, load_taxonomy
from src.views import ViewBuilder

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
]
