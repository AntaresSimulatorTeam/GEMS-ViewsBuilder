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

from pathlib import Path

import yaml
from pydantic import Field

from src.base_model import GEMSViewBuilderBaseModel


class TaxonomyItem(GEMSViewBuilderBaseModel):
    id: str


class TaxonomyCategory(GEMSViewBuilderBaseModel):
    id: str
    parent_category: str | None = Field(
        None, alias="parent-category"
    )  # for now keep like this because taxonomy.yml used for testing isn't completed
    variables: list[TaxonomyItem] = []
    parameters: list[TaxonomyItem] = []
    ports: list[TaxonomyItem] = []
    constraints: list[TaxonomyItem] = []
    extra_outputs: list[TaxonomyItem] = Field(default=[], alias="extra-outputs")
    properties: list[TaxonomyItem] = []


class TaxonomyData(GEMSViewBuilderBaseModel):
    id: str
    description: str = ""
    categories: list[TaxonomyCategory] = []


class Taxonomy:
    """
    In memory representation of the taxonomy.yml file.
    """

    def __init__(self, taxonomy_file_path: Path) -> None:
        with open(taxonomy_file_path) as f:
            raw = yaml.safe_load(f)
        parsed = TaxonomyData.model_validate(raw["taxonomy"])
        self.id = parsed.id
        self.description = parsed.description
        self.categories: list[TaxonomyCategory] = parsed.categories
