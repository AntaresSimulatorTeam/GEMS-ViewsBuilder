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

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel


class TaxonomyItem(ViewBuilderBasedModel):
    id: str


class TaxonomyCategory(ViewBuilderBasedModel):
    id: str
    parent_category: str | None = Field(
        None, alias="parent-category"
    )  # for now keep like this because taxonomy.yml used for testing isn't completed
    variables: list[TaxonomyItem] = Field(default_factory=list)
    parameters: list[TaxonomyItem] = Field(default_factory=list)
    ports: list[TaxonomyItem] = Field(default_factory=list)
    constraints: list[TaxonomyItem] = Field(default_factory=list)
    extra_outputs: list[TaxonomyItem] = Field(default_factory=list, alias="extra-outputs")
    port_fields: list[TaxonomyItem] = Field(default_factory=list, alias="port-fields")
    properties: list[TaxonomyItem] = Field(default_factory=list)


class TaxonomyData(ViewBuilderBasedModel):
    id: str
    description: str = ""
    categories: list[TaxonomyCategory] = Field(default_factory=list)


@dataclass
class Taxonomy:
    """
    Parsed taxonomy.yml representation used by the view builder.
    """

    id: str
    description: str = ""
    categories: list[TaxonomyCategory] = field(default_factory=list)


def load_taxonomy(taxonomy_file_path: Path) -> Taxonomy:
    logging.info(f"Loading taxonomy from {taxonomy_file_path}")
    parsed = load_taxonomy_file(taxonomy_file_path)
    taxonomy = Taxonomy(
        id=parsed.id,
        description=parsed.description,
        categories=parsed.categories,
    )
    logging.info(f"Taxonomy {taxonomy.id!r} loaded with {len(taxonomy.categories)} categor(ies)")
    return taxonomy


def load_taxonomy_file(taxonomy_file_path: Path) -> TaxonomyData:
    logging.debug(f"Loading taxonomy YAML from {taxonomy_file_path}")
    with open(taxonomy_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "taxonomy" not in raw:
        raise ValueError(f"taxonomy.yml file {taxonomy_file_path} is missing the 'taxonomy' key at the root")
    logging.debug(f"Taxonomy YAML parsed successfully from {taxonomy_file_path}")
    return TaxonomyData.model_validate(raw["taxonomy"])
