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

"""Model library YAML: parsed with GemsPy (gems.model.parsing) plus taxonomy-category on models."""

from pathlib import Path
from typing import List, cast

import yaml
from gems.model.parsing import (
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
from gems.model.parsing import (
    InputLibrary as GemsInputLibrary,
)
from gems.model.parsing import (
    InputModel as GemsInputModel,
)
from pydantic import Field

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


class ModelDefinition(GemsInputModel):  # type: ignore[misc]
    """GemsPy `InputModel` plus optional `taxonomy-category` for ViewsBuilder indexing."""

    taxonomy_category: str | None = Field(default=None, alias="taxonomy-category")


class LibraryData(GemsInputLibrary):  # type: ignore[misc]
    """Library root: GemsPy shape with extended model type."""

    models: List[ModelDefinition] = Field(default_factory=list)


class ModelLibrary:
    """
    In memory representation of a model library .yml file.

    Loads via GemsPy parsing types; builds taxonomy indexes for metric structure tables.
    """

    def __init__(self, library_file_path: Path) -> None:
        parsed = self._load_library_file(library_file_path)
        self.id = parsed.id
        self.description = parsed.description or ""
        self.port_types: list[InputPortType] = parsed.port_types
        self.models: dict[str, ModelDefinition] = {m.id: m for m in parsed.models}
        self.models_by_taxonomy_category: dict[str, list[str]] = {}
        for m in parsed.models:
            if not m.taxonomy_category:
                continue
            self.models_by_taxonomy_category.setdefault(m.taxonomy_category, []).append(m.id)

    def _load_library_file(self, library_file_path: Path) -> LibraryData:
        with open(library_file_path) as f:
            raw = yaml.safe_load(f)
        return cast(LibraryData, LibraryData.model_validate(raw["library"]))

    def get_model(self, model_id: str) -> ModelDefinition | None:
        """Return the full model definition, or None if not found."""
        return self.models.get(model_id)

    def get_taxonomy_category(self, model_id: str) -> str | None:
        """Return the taxonomy category for a given model id, or None if unknown."""
        model = self.get_model(model_id)
        return model.taxonomy_category if model else None

    def get_components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        return self.models_by_taxonomy_category.get(taxonomy_category, [])
