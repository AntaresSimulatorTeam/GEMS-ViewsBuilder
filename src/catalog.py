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

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

from src.base_model import ViewBuilderBasedModel

"""
They are the same for now but we could keep them separated for future use.
In fact they represent the different operators
"""


class TermsOperator(Enum):
    SUM = "sum"
    AVG = "avg"


class TimeOperator(Enum):
    SUM = "sum"
    AVG = "avg"


class Term(ViewBuilderBasedModel):
    taxonomy_category: str
    output_id: str
    location_ports: str | tuple[str, ...] | None
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


@dataclass
class Catalog:
    id: str
    taxonomy: str
    location_taxonomy_category: str
    metrics: dict[str, Metric]


def load_catalog(catalog_file_path: Path) -> Catalog:
    parsed = _load_catalog_file(catalog_file_path)
    return Catalog(
        id=parsed.id,
        taxonomy=parsed.taxonomy,
        location_taxonomy_category=parsed.location.taxonomy_category,
        metrics={metric.id: metric for metric in parsed.metrics_definition},
    )


def _load_catalog_file(catalog_file_path: Path) -> CatalogData:
    with open(catalog_file_path) as f:
        raw = yaml.safe_load(f)
    return CatalogData.model_validate(raw["catalog"])


def get_catalog_metric(catalog: Catalog, metric_id: str) -> Metric:
    if metric_id not in catalog.metrics:
        raise ValueError(f"Metric {metric_id} not found in catalog {catalog.id}")
    return catalog.metrics[metric_id]
