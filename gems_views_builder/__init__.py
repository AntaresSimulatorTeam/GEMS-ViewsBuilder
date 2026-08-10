# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


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
    PropertySchema,
    Term,
    TermsOperator,
    TimeOperator,
    load_catalog,
    load_catalogs,
)
from gems_views_builder.input.input_data import InputData
from gems_views_builder.input.library import Library, load_library
from gems_views_builder.input.simulation_table import (
    FilteredSimulationTable,
    SimulationTable,
    filter_simulation_table,
    load_simulation_table,
)
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem, load_taxonomy
from gems_views_builder.input.view_config import TimeAggregation, ViewConfig, load_view_config
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.metric_view import MetricView
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from gems_views_builder.view import ViewBuilder

__all__ = [
    "Calendar",
    "load_calendar",
    "FilteredSimulationTable",
    "SimulationTable",
    "load_simulation_table",
    "filter_simulation_table",
    "Catalog",
    "load_catalog",
    "load_catalogs",
    "InputData",
    "Metric",
    "PropertySchema",
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
    "MetricStructureTable",
    "MetricStructureTableBuilder",
    "MetricView",
    "ViewBuilder",
    "System",
]
