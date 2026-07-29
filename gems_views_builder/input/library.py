# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Model library YAML with explicit local models"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from gems_craft.model.library import Library as GemsLibrary  # type: ignore
from gems_craft.model.parsing import LibrarySchema, ModelSchema, PortTypeSchema, parse_yaml_library  # type: ignore
from gems_craft.model.resolve_library import resolve_library  # type: ignore


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


def load_library(library_file_path: Path) -> Library:
    logging.info(f"Loading model library from {library_file_path}")
    parsed = load_library_file(library_file_path)
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


def load_libraries(library_dir: Path) -> dict[str, Library]:
    """
    Load every library YAML file (any file name) in library_dir, keyed by library id.
    """
    logging.info(f"Loading model libraries from {library_dir}")
    libraries: dict[str, Library] = {}
    for library_file_path in discover_library_files(library_dir):
        library = load_library(library_file_path)
        if library.id in libraries:
            raise ValueError(
                f"Library id {library.id!r} defined more than once in {library_dir} (also found in a different file)"
            )
        libraries[library.id] = library
    return libraries


def resolve_libraries(library_dir: Path) -> dict[str, GemsLibrary]:
    """Resolve library YAMLs in ``library_dir`` into GemsPy's fully-resolved libraries, keyed by library id.

    This is the shape ``gems_craft.study.resolve_components.resolve_system`` needs to resolve
    the study's components, distinct from the schema-level :class:`Library` wrapper above.
    """
    logging.info(f"Resolving model libraries from {library_dir}")
    parsed = [load_library_file(p) for p in discover_library_files(library_dir)]
    return cast(dict[str, GemsLibrary], resolve_library(parsed))


def discover_library_files(library_dir: Path) -> list[Path]:
    return list(library_dir.glob("*.yml"))


def merge_taxonomy_category_by_model(libraries: dict[str, Library]) -> dict[str, str]:
    """
    Merge each library's taxonomy_category_by_model into one dict keyed by qualified
    model id (<library_id>.<model_id>).
    Two libraries may define a model with the same id but a different taxonomy category
    (e.g. a "generator" role that behaves differently per library); qualifying the key keeps
    them distinct instead of one silently overwriting the other.
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
