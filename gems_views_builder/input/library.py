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

import logging
from pathlib import Path
from typing import cast

import yaml
from gems.model.parsing import LibrarySchema, ModelSchema, PortTypeSchema  # type: ignore


class Library:
    """
    library .yml representation with taxonomy indexes.
    Loads via GemsPy parsing types; builds taxonomy indexes for metric structure tables.
    """

    def __init__(self) -> None:
        """
        Initialize an empty model library.
        # # TODO: GEMS Craft future library could keep all data in structured in memory format
        # # Current implementation inside gemspy drop everything after pydantic validation, what is keept:
        # # id, description, port_types, models, internal parsing should be done there for later faster access to the data
        """
        self.id = ""
        self.description = ""
        self.port_types: list[PortTypeSchema] = []
        self.models: dict[str, ModelSchema] = {}
        self.models_by_taxonomy_category: dict[str, list[str]] = {}

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

    def get_components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
        return self.models_by_taxonomy_category.get(taxonomy_category, [])


def load_library(library_file_path: Path) -> Library:
    logging.info(f"Loading model library from {library_file_path}")
    library = Library()
    parsed = load_library_file(library_file_path)
    library.id = parsed.id
    library.description = parsed.description or ""
    library.port_types = parsed.port_types
    library.models = {m.id: m for m in parsed.models}
    logging.info(
        f"Library {library.id!r} loaded, containing {len(library.port_types)} port type(s) and {len(library.models)} model(s)"
    )
    library.models_by_taxonomy_category = {}
    for m in parsed.models:
        if not m.taxonomy_category:
            continue
        library.models_by_taxonomy_category.setdefault(m.taxonomy_category, []).append(m.id)
    logging.debug(
        f"Library indexing complete: {len(library.models_by_taxonomy_category)} taxonomy categor"
        f"{'y' if len(library.models_by_taxonomy_category) == 1 else 'ies'}"
    )
    return library


def load_library_file(library_file_path: Path) -> LibrarySchema:
    # # GEMS Craft future library could have option to load library model from path
    # # Current blueprint of method inside gemspy is typing.TextIO idk why ?
    logging.debug(f"Loading library YAML from {library_file_path}")
    with open(library_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "library" not in raw:
        raise ValueError(f"library.yml file {library_file_path} is missing the 'library' key at the root")
    logging.debug("Library YAML parsed successfully")
    return LibrarySchema.model_validate(raw["library"])
