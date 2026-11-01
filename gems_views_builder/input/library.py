# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Model library YAML with explicit local models"""

import logging
from pathlib import Path
from typing import cast

from gems_craft.model.parsing import LibrarySchema, parse_yaml_library  # type: ignore


class Library(LibrarySchema):  # type: ignore[misc]
    """
    library .yml representation with taxonomy indexes.
    Loads via GemsPy parsing types; builds taxonomy indexes for metric structure tables.
    """

    taxon_by_model: dict[str, str]


def create_lib_from_yml(yml_lib: LibrarySchema) -> Library:
    return cast(
        Library,
        Library.model_validate(
            {
                **yml_lib.model_dump(),
                "taxon_by_model": {
                    model.id: model.taxonomy_category for model in yml_lib.models if model.taxonomy_category
                },
            }
        ),
    )


def load_yml_libs(library_files: list[Path]) -> list[LibrarySchema]:
    logging.info(f"Loading {len(library_files)} model library file(s)")
    yml_libs: list[LibrarySchema] = []
    already_loaded_libs: set[str] = set()
    for library_file_path in library_files:
        yml_lib = load_lib_file(library_file_path)
        if yml_lib.id in already_loaded_libs:
            raise ValueError(
                f"Library id {yml_lib.id!r} defined more than once in {library_file_path.parent}"
                " (also found in a different file)"
            )
        already_loaded_libs.add(yml_lib.id)
        yml_libs.append(yml_lib)
    return yml_libs


def associate_models_with_a_taxon(libraries: list[Library]) -> dict[str, str]:
    taxon_by_model: dict[str, str] = {}
    for library in libraries:
        for model_id, taxon in library.taxon_by_model.items():
            taxon_by_model[f"{library.id}.{model_id}"] = taxon
    return taxon_by_model


def load_lib_file(library_file_path: Path) -> LibrarySchema:
    # # GEMS Craft future library could have option to load library model from path
    # # Current blueprint of method inside gemspy is typing.TextIO idk why ?
    logging.debug(f"Loading library YAML from {library_file_path}")
    with open(library_file_path, encoding="utf-8") as f:
        yml_lib = parse_yaml_library(f)
    logging.debug("Library YAML parsed successfully")
    return yml_lib
