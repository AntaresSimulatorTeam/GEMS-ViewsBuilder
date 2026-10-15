# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


"""GEMS-ViewsBuilder public package namespace."""

from gems_craft.model.parsing import (  # type: ignore
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
    AggregOperatorType,
    Catalog,
    Metric,
    PropertySchema,
    Term,
    load_catalog,
    load_catalogs,
)
from gems_views_builder.input.library import Library, associate_models_with_a_taxon
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import (
    FilteredSimulationTable,
    SimulationTable,
    filter_simulation_table,
    load_simulation_table,
)
from gems_views_builder.input.system import System
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem, load_taxonomy
from gems_views_builder.input.view_building_input_data import ViewBuildingInputData, create_view_building_input
from gems_views_builder.input.view_config import TimeGranularity, ViewConfig, load_view_config
from gems_views_builder.metric_structure_table import MetricStructureTable
from gems_views_builder.metric_view import MetricView, TemporalMetricView
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
    "RawInputData",
    "ViewBuildingInputData",
    "create_view_building_input",
    "Metric",
    "PropertySchema",
    "Term",
    "AggregOperatorType",
    "ConstraintSchema",
    "ExtraOutputSchema",
    "Library",
    "LibrarySchema",
    "associate_models_with_a_taxon",
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
    "TimeGranularity",
    "ViewConfig",
    "load_view_config",
    "MetricStructureTable",
    "MetricStructureTableBuilder",
    "MetricView",
    "TemporalMetricView",
    "ViewBuilder",
    "System",
]
