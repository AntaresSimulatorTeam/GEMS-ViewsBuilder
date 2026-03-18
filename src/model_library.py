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

"""In memory representation of a model library .yml file (e.g. pypsa_models.yml)."""

from pathlib import Path

import yaml
from pydantic import Field

from src.base_model import ViewBuilderBasedModel

# ---------------------------------------------------------------------------
# Nested structures (parameters, variables, ports, etc.)
# ---------------------------------------------------------------------------


class ParameterDef(ViewBuilderBasedModel):
    id: str
    time_dependent: bool | None = Field(None, alias="time-dependent")
    scenario_dependent: bool | None = Field(None, alias="scenario-dependent")
    lower_bound: str | None = Field(None, alias="lower-bound")
    upper_bound: str | None = Field(None, alias="upper-bound")
    value: str | int | float | None = None


class VariableDef(ViewBuilderBasedModel):
    id: str
    time_dependent: bool | None = Field(None, alias="time-dependent")
    scenario_dependent: bool | None = Field(None, alias="scenario-dependent")
    lower_bound: str | int | float | None = Field(None, alias="lower-bound")
    upper_bound: str | int | float | None = Field(None, alias="upper-bound")


class PortDef(ViewBuilderBasedModel):
    id: str
    type: str | None = None


class PortFieldDefinition(ViewBuilderBasedModel):
    port: str
    field: str
    definition: str


class ConstraintDef(ViewBuilderBasedModel):
    id: str
    expression: str


class BindingConstraintDef(ViewBuilderBasedModel):
    id: str
    expression: str


class ExtraOutputDef(ViewBuilderBasedModel):
    id: str
    expression: str


class ObjectiveContributionDef(ViewBuilderBasedModel):
    id: str
    expression: str


class ModelDefinition(ViewBuilderBasedModel):
    """Full model definition with all nested structures."""

    id: str
    taxonomy_category: str | None = Field(None, alias="taxonomy-category")
    parameters: list[ParameterDef] = []
    variables: list[VariableDef] = []
    ports: list[PortDef] = []
    port_field_definitions: list[PortFieldDefinition] = Field(default=[], alias="port-field-definitions")
    constraints: list[ConstraintDef] = []
    binding_constraints: list[BindingConstraintDef] = Field(default=[], alias="binding-constraints")
    extra_outputs: list[ExtraOutputDef] = Field(default=[], alias="extra-outputs")
    objective_contributions: list[ObjectiveContributionDef] = Field(default=[], alias="objective-contributions")


# ---------------------------------------------------------------------------
# Port types (library-level)
# ---------------------------------------------------------------------------


class PortTypeField(ViewBuilderBasedModel):
    id: str


class PortTypeDef(ViewBuilderBasedModel):
    id: str
    description: str = ""
    fields: list[PortTypeField] = []


# ---------------------------------------------------------------------------
# Library root
# ---------------------------------------------------------------------------


class LibraryData(ViewBuilderBasedModel):
    """Root structure of a library yml file."""

    id: str
    description: str = ""
    port_types: list[PortTypeDef] = Field(default=[], alias="port-types")
    models: list[ModelDefinition] = []


class ModelLibrary:
    """
    In memory representation of a model library .yml file.

    Loads the full library structure including all models with their parameters,
    variables, ports, constraints, extra-outputs, etc.
    """

    def __init__(self, library_file_path: Path) -> None:
        parsed = self._load_library_file(library_file_path)
        self.id = parsed.id
        self.description = parsed.description
        self.port_types: list[PortTypeDef] = parsed.port_types
        self.models: dict[str, ModelDefinition] = {m.id: m for m in parsed.models}
        # Index: taxonomy_category -> [model_id, ...]
        self.models_by_taxonomy_category: dict[str, list[str]] = {}
        for m in parsed.models:
            if not m.taxonomy_category:
                continue
            self.models_by_taxonomy_category.setdefault(m.taxonomy_category, []).append(m.id)

    def _load_library_file(self, library_file_path: Path) -> LibraryData:
        with open(library_file_path) as f:
            raw = yaml.safe_load(f)
        return LibraryData.model_validate(raw["library"])

    def get_model(self, model_id: str) -> ModelDefinition | None:
        """Return the full model definition, or None if not found."""
        return self.models.get(model_id)

    def get_taxonomy_category(self, model_id: str) -> str | None:
        """Return the taxonomy category for a given model id, or None if unknown."""
        model = self.get_model(model_id)
        return model.taxonomy_category if model else None

    def get_components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        # Return all model ids that belong to this taxonomy category.
        return self.models_by_taxonomy_category.get(taxonomy_category, [])
