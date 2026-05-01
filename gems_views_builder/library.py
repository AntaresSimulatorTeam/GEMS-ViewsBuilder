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

"""Model library YAML with explicit local models"""

from pathlib import Path

import yaml
from gems.model.parsing import (  # type: ignore
    ConstraintSchema,
    ExtraOutputSchema,
    ModelPortSchema,
    ObjectiveContributionSchema,
    ParameterSchema,
    PortFieldDefinitionSchema,
    PortTypeSchema,
    VariableSchema,
)
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel


class ModelDefinition(ViewBuilderBasedModel):
    """Local model definition used by ViewsBuilder."""

    id: str
    description: str | None = None
    parameters: list[ParameterSchema] = Field(default_factory=list)
    variables: list[VariableSchema] = Field(default_factory=list)
    ports: list[ModelPortSchema] = Field(default_factory=list)
    port_field_definitions: list[PortFieldDefinitionSchema] = Field(default_factory=list)
    constraints: list[ConstraintSchema] = Field(default_factory=list)
    binding_constraints: list[ConstraintSchema] = Field(default_factory=list)
    objective_contributions: list[ObjectiveContributionSchema] = Field(default_factory=list)
    extra_outputs: list[ExtraOutputSchema] = Field(default_factory=list)

    taxonomy_category: str | None = Field(default=None, alias="taxonomy-category")


class LibraryData(ViewBuilderBasedModel):
    """Library root model for `library` yaml section."""

    id: str
    description: str | None = None
    port_types: list[PortTypeSchema] = Field(default_factory=list)
    models: list[ModelDefinition] = Field(default_factory=list)


class ModelLibrary:
    """
    Model library .yml representation with taxonomy indexes.

    Loads via GemsPy parsing types; builds taxonomy indexes for metric structure tables.
    """

    def __init__(self, library_file_path: Path) -> None:
        """
        Cheap constructor: keep only the file path.

        Use `ModelLibrary.load(...)` (or `load_into_self()`) to perform I/O and build indexes.
        """
        self.file = library_file_path
        self.id = ""
        self.description = ""
        self.port_types: list[PortTypeSchema] = []
        self.models: dict[str, ModelDefinition] = {}
        self.models_by_taxonomy_category: dict[str, list[str]] = {}

    @classmethod
    def load(cls, library_file_path: Path) -> "ModelLibrary":
        return cls(library_file_path).load_into_self()

    def load_into_self(self) -> "ModelLibrary":
        parsed = self._load_library_file(self.file)
        self.id = parsed.id
        self.description = parsed.description or ""
        self.port_types = parsed.port_types
        self.models = {m.id: m for m in parsed.models}
        self.models_by_taxonomy_category = {}
        for m in parsed.models:
            if not m.taxonomy_category:
                continue
            self.models_by_taxonomy_category.setdefault(m.taxonomy_category, []).append(m.id)
        return self

    def _load_library_file(self, library_file_path: Path) -> LibraryData:
        with open(library_file_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if "library" not in raw:
            raise ValueError(f"library.yml file {library_file_path} is missing the 'library' key at the root")
        return LibraryData.model_validate(raw["library"])

    def get_model(self, model_id: str) -> ModelDefinition | None:
        """Return the full model definition, or None if not found."""
        return self.models.get(model_id)

    def get_taxonomy_category(self, model_id: str) -> str | None:
        """Return the taxonomy category for a given model id, or None if unknown."""
        model = self.get_model(model_id)
        return model.taxonomy_category if model else None

    def get_components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        return self.models_by_taxonomy_category.get(taxonomy_category, [])
