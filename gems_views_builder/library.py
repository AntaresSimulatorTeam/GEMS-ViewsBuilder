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
    InputConstraint,
    InputExtraOutput,
    InputField,
    InputModelPort,
    InputObjectiveContribution,
    InputParameter,
    InputPortFieldDefinition,
    InputPortType,
    InputVariable,
)
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.common import logger

# Public aliases — same names as the previous local Pydantic models.
ParameterDef = InputParameter
VariableDef = InputVariable
PortDef = InputModelPort
PortFieldDefinition = InputPortFieldDefinition
ConstraintDef = InputConstraint
BindingConstraintDef = InputConstraint
ObjectiveContributionDef = InputObjectiveContribution
PortTypeField = InputField
PortTypeDef = InputPortType
ExtraOutputDef = InputExtraOutput


class ModelDefinition(ViewBuilderBasedModel):
    """Local model definition used by ViewsBuilder."""

    id: str
    description: str | None = None
    parameters: list[InputParameter] = Field(default_factory=list)
    variables: list[InputVariable] = Field(default_factory=list)
    ports: list[InputModelPort] = Field(default_factory=list)
    port_field_definitions: list[InputPortFieldDefinition] = Field(default_factory=list)
    constraints: list[InputConstraint] = Field(default_factory=list)
    binding_constraints: list[InputConstraint] = Field(default_factory=list)
    objective_contributions: list[InputObjectiveContribution] = Field(default_factory=list)
    extra_outputs: list[InputExtraOutput] = Field(default_factory=list)

    taxonomy_category: str | None = Field(default=None, alias="taxonomy-category")


class LibraryData(ViewBuilderBasedModel):
    """Library root model for `library` yaml section."""

    id: str
    description: str | None = None
    port_types: list[InputPortType] = Field(default_factory=list)
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
        self.port_types: list[InputPortType] = []
        self.models: dict[str, ModelDefinition] = {}
        self.models_by_taxonomy_category: dict[str, list[str]] = {}

    @classmethod
    def load(cls, library_file_path: Path) -> "ModelLibrary":
        return cls(library_file_path).load_into_self()

    def load_into_self(self) -> "ModelLibrary":
        logger.info(f"Loading model library from {self.file}")
        parsed = self._load_library_file(self.file)
        self.id = parsed.id
        self.description = parsed.description or ""
        self.port_types = parsed.port_types
        self.models = {m.id: m for m in parsed.models}
        logger.info(
            f"Library schema loaded: id={self.id!r}, {len(self.port_types)} port type(s), {len(self.models)} model(s)"
        )
        self.models_by_taxonomy_category = {}
        for m in parsed.models:
            if not m.taxonomy_category:
                continue
            self.models_by_taxonomy_category.setdefault(m.taxonomy_category, []).append(m.id)
        logger.info(
            f"Library indexing complete: {len(self.models_by_taxonomy_category)} taxonomy categor"
            f"{'y' if len(self.models_by_taxonomy_category) == 1 else 'ies'}"
        )
        return self

    def _load_library_file(self, library_file_path: Path) -> LibraryData:
        logger.info(f"Parsing library YAML from {library_file_path}")
        with open(library_file_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if "library" not in raw:
            raise ValueError(f"library.yml file {library_file_path} is missing the 'library' key at the root")
        logger.info("Library YAML parsed successfully")
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
