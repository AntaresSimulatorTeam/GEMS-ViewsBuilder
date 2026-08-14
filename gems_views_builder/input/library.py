# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Model library YAML with explicit local models"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from gems_craft.model.parsing import LibrarySchema, ModelSchema, PortTypeSchema, parse_yaml_library  # type: ignore


@dataclass
class Library:
    """
    library .yml representation with taxonomy indexes.
    Loads via GemsPy parsing types; builds taxonomy indexes for metric structure tables.
    """

    id: str
    description: str
    port_types: list[PortTypeSchema]
    models: dict[str, ModelSchema]
    models_by_taxonomy_category: dict[str, list[str]]
    taxonomy_category_by_model: dict[str, str]

    def get_model(self, model_id: str) -> ModelSchema:
        """Return the full model definition, or None if not found."""
        try:
            return self.models[model_id]
        except KeyError:
            raise ValueError(f"Model {model_id} not found in library")

    def get_taxonomy_category(self, model_id: str) -> str:
        """Return the taxonomy category for a given model id."""
        model = self.get_model(model_id)
        if model.taxonomy_category is None:
            raise ValueError(f"Model {model_id} has no taxonomy category in library")
        return cast(str, model.taxonomy_category)

    def get_models_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        return self.models_by_taxonomy_category.get(taxonomy_category, [])


def create_lib_from_schema(parsed: LibrarySchema) -> Library:
    return Library(
        id=parsed.id,
        description=parsed.description or "",
        port_types=parsed.port_types,
        models={m.id: m for m in parsed.models},
        models_by_taxonomy_category={
            cat: [m.id for m in parsed.models if m.taxonomy_category == cat]
            for cat in {m.taxonomy_category for m in parsed.models if m.taxonomy_category}
        },
        taxonomy_category_by_model={m.id: m.taxonomy_category for m in parsed.models if m.taxonomy_category},
    )


def load_library_schemas(library_dir: Path) -> list[LibrarySchema]:
    """Parse every library YAML file in library_dir, rejecting duplicate library ids."""
    logging.info(f"Loading model libraries from {library_dir}")
    schemas: list[LibrarySchema] = []
    seen_ids: set[str] = set()
    for library_file_path in collect_lib_files(library_dir):
        parsed = load_library_file(library_file_path)
        if parsed.id in seen_ids:
            raise ValueError(
                f"Library id {parsed.id!r} defined more than once in {library_dir} (also found in a different file)"
            )
        seen_ids.add(parsed.id)
        schemas.append(parsed)
    return schemas


def load_libraries(library_dir: Path) -> dict[str, Library]:
    """
    Load every library YAML file (any file name) in library_dir, keyed by library id.
    """
    return {parsed.id: create_lib_from_schema(parsed) for parsed in load_library_schemas(library_dir)}


def collect_lib_files(library_dir: Path) -> list[Path]:
    return list(library_dir.glob("*.yml"))


def merge_taxonomy_category_by_model(libraries: dict[str, Library]) -> dict[str, str]:
    """
    Merge each library's taxonomy_category_by_model into one dict keyed by qualified
    model id (<library_id>.<model_id>).
    """
    merged: dict[str, str] = {}
    for library_id, library in libraries.items():
        for model_id, category in library.taxonomy_category_by_model.items():
            merged[f"{library_id}.{model_id}"] = category
    return merged


def load_library_file(library_file_path: Path) -> LibrarySchema:
    # # GEMS Craft future library could have option to load library model from path
    # # Current blueprint of method inside gemspy is typing.TextIO idk why ?
    logging.debug(f"Loading library YAML from {library_file_path}")
    with open(library_file_path, encoding="utf-8") as f:
        parsed = parse_yaml_library(f)
    logging.debug("Library YAML parsed successfully")
    return parsed
