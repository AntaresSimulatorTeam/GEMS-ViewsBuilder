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

from src.base_model import ViewBuilderBasedModel


class TermsOperator(Enum):
    SUM = "sum"
    AVG = "avg"


class TimeOperator(Enum):
    SUM = "sum"
    AVG = "avg"


class Term(ViewBuilderBasedModel):
    taxonomy_category: str
    output_id: str
    location_ports: str | None
    weight_output_id: str | None = None


class Metric(ViewBuilderBasedModel):
    id: str
    terms: list[Term]
    terms_operator: TermsOperator
    time_operator: TimeOperator
    breakdown_property: str | None = None
    filter: tuple[str, str] | None = None


class CatalogLocation(ViewBuilderBasedModel):
    taxonomy_category: str


class CatalogData(ViewBuilderBasedModel):
    id: str
    taxonomy: str
    location: CatalogLocation
    metrics_definition: list[Metric]


class Catalog:
    def __init__(self, catalog_file_path: Path) -> None:
        parsed = self._load_catalog_file(catalog_file_path)
        self.id = parsed.id
        self.taxonomy = parsed.taxonomy
        self.location_taxonomy_category = parsed.location.taxonomy_category
        self.metrics: dict[str, Metric] = {metric.id: metric for metric in parsed.metrics_definition}

    def _load_catalog_file(self, catalog_file_path: Path) -> CatalogData:
        with open(catalog_file_path) as f:
            raw = yaml.safe_load(f)
        return CatalogData.model_validate(raw["catalog"])

    def get_metric(self, metric_id: str) -> Metric:
        if metric_id not in self.metrics:
            raise ValueError(f"Metric {metric_id} not found in catalog {self.id}")
        return self.metrics[metric_id]
