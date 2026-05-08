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
from typing import cast

from gems.model.parsing import (  # type: ignore
    LibrarySchema,
    ModelSchema,
    PortTypeSchema,
    parse_yaml_library,
)
from gems.model.resolve_library import resolve_library  # type: ignore[import-untyped]


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
        self.models: dict[str, ModelSchema] = {}
        self.models_by_taxonomy_category: dict[str, list[str]] = {}
        self.library_schema: LibrarySchema | None = None

    @classmethod
    def load(cls, library_file_path: Path) -> "ModelLibrary":
        return cls(library_file_path).load_into_self()

    def load_into_self(self) -> "ModelLibrary":
        parsed = self._load_library_schema(self.file)
        self.library_schema = parsed

        self.id = parsed.id
        self.description = parsed.description or ""
        self.port_types = parsed.port_types
        self.models = {m.id: m for m in parsed.models}
        self.models_by_taxonomy_category = {}
        for m in self.models.values():
            taxonomy_category = getattr(m, "taxonomy_category", None)
            if not taxonomy_category:
                continue
            self.models_by_taxonomy_category.setdefault(taxonomy_category, []).append(m.id)
        return self

    def _load_library_schema(self, library_file_path: Path) -> LibrarySchema:
        with open(library_file_path, encoding="utf-8") as f:
            return parse_yaml_library(f)

    def resolve_libraries(self) -> dict[str, object]:
        """
        Resolve this library via GemsPy to obtain `dict[library_id, Library]`
        suitable for resolving a system (`resolve_system`).
        """
        if self.library_schema is None:
            raise RuntimeError("ModelLibrary is not loaded (missing LibrarySchema)")
        return cast(dict[str, object], resolve_library([self.library_schema]))

    def get_model(self, model_id: str) -> ModelSchema | None:
        """Return the full model definition, or None if not found."""
        return self.models.get(model_id)

    def get_taxonomy_category(self, model_id: str) -> str | None:
        """Return the taxonomy category for a given model id, or None if unknown."""
        model = self.get_model(model_id)
        return model.taxonomy_category if model else None

    def get_components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        return self.models_by_taxonomy_category.get(taxonomy_category, [])
