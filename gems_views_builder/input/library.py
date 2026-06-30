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
from dataclasses import dataclass
from pathlib import Path
from typing import cast

<<<<<<< HEAD
import yaml
from gems.model.parsing import LibrarySchema, ModelSchema, PortTypeSchema  # type: ignore
=======
from gems.model.parsing import LibrarySchema, ModelSchema, PortTypeSchema, parse_yaml_library  # type: ignore
>>>>>>> origin/main


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

<<<<<<< HEAD
    def get_components_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
=======
    def get_models_in_taxonomy_category(self, taxonomy_category: str) -> list[str]:
>>>>>>> origin/main
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
    )


def load_library_file(library_file_path: Path) -> LibrarySchema:
    # # GEMS Craft future library could have option to load library model from path
    # # Current blueprint of method inside gemspy is typing.TextIO idk why ?
    logging.debug(f"Loading library YAML from {library_file_path}")
    with open(library_file_path, encoding="utf-8") as f:
<<<<<<< HEAD
        raw = yaml.safe_load(f)
    if "library" not in raw:
        raise ValueError(f"library.yml file {library_file_path} is missing the 'library' key at the root")
    logging.debug("Library YAML parsed successfully")
    return LibrarySchema.model_validate(raw["library"])
=======
        parsed = parse_yaml_library(f)
    logging.debug("Library YAML parsed successfully")
    return parsed
>>>>>>> origin/main
