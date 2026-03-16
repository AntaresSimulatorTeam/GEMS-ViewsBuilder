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

"""In memory representation of a catalog .yml file."""

from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field

from src.base_model import ViewBuilderBasedModel


class TermsOperator(Enum):
    SUM = "sum"
    AVG = "avg"


class TimeOperator(Enum):
    SUM = "sum"
    AVG = "avg"


class Term(ViewBuilderBasedModel):
    taxonomy_category: str = Field(alias="taxonomy-category")
    output_id: str = Field(alias="output-id")
    location_ports: str | None = Field(alias="location-ports")
    weight_output_id: str | None = Field(None, alias="weight-output-id")


class Metric(ViewBuilderBasedModel):
    id: str
    terms: list[Term]
    terms_operator: TermsOperator = Field(alias="terms-operator")
    time_operator: TimeOperator = Field(alias="time-operator")
    breakdown_property: str | None = None
    filter: tuple[str, str] | None = None


class CatalogLocation(ViewBuilderBasedModel):
    taxonomy_category: str = Field(alias="taxonomy-category")


class CatalogData(ViewBuilderBasedModel):
    id: str
    taxonomy: str
    location: CatalogLocation
    metrics_definition: list[Metric] = Field(alias="metrics-definition")


class Catalog:
    def __init__(self, catalog_file_path: Path) -> None:
        parsed = self._load_catalog_file(catalog_file_path)
        self.id = parsed.id
        self.taxonomy = parsed.taxonomy
        self.location_taxonomy_category = parsed.location.taxonomy_category
        self.metrics_definition: list[Metric] = parsed.metrics_definition

    def _load_catalog_file(self, catalog_file_path: Path) -> CatalogData:
        with open(catalog_file_path) as f:
            raw = yaml.safe_load(f)
        return CatalogData.model_validate(raw["catalog"])
