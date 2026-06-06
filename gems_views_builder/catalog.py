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

"""Catalog .yml parsing models and typed representation."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from pydantic import field_validator

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.common import logger

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


class TermData(ViewBuilderBasedModel):
    taxonomy_category: str
    output_id: str
    location_ports: str | tuple[str, ...] | None
    weight_output_id: str | None = None


class PropertySchema(ViewBuilderBasedModel):
    """Reference to a system/taxonomy property by key; value is required only for metric filters."""

    key: str
    value: str | None = None


class MetricData(ViewBuilderBasedModel):
    id: str
    terms: list[TermData]
    terms_operator: TermsOperator
    time_operator: TimeOperator
    breakdown: list[PropertySchema] | None = None
    filter: PropertySchema | None = None

    @field_validator("filter")
    @classmethod
    def validate_filter(cls, value: PropertySchema | None) -> PropertySchema | None:
        if value is not None and value.value is None:
            raise ValueError("metric filter property must include a value")
        return value


class CatalogLocationData(ViewBuilderBasedModel):
    taxonomy_category: str


class CatalogData(ViewBuilderBasedModel):
    id: str
    taxonomy: str
    location: CatalogLocationData
    metrics_definition: list[MetricData]


@dataclass
class Term:
    taxonomy_category: str
    output_id: str
    location_ports: str | tuple[str, ...] | None
    weight_output_id: str | None = None


@dataclass
class Metric:
    id: str
    terms: list[Term]
    terms_operator: TermsOperator
    time_operator: TimeOperator
    breakdown: tuple[PropertySchema, ...] | None = None
    filter: PropertySchema | None = None


@dataclass
class Catalog:
    id: str
    taxonomy: str
    location_taxonomy_category: str
    metrics: dict[str, Metric] = field(default_factory=dict)


def _to_term(term_data: TermData) -> Term:
    return Term(
        taxonomy_category=term_data.taxonomy_category,
        output_id=term_data.output_id,
        location_ports=term_data.location_ports,
        weight_output_id=term_data.weight_output_id,
    )


def _to_metric(metric_data: MetricData) -> Metric:
    return Metric(
        id=metric_data.id,
        terms=[_to_term(term) for term in metric_data.terms],
        terms_operator=metric_data.terms_operator,
        time_operator=metric_data.time_operator,
        breakdown=tuple(metric_data.breakdown) if metric_data.breakdown else None,
        filter=metric_data.filter,
    )


def load_catalogs(input_data_path: Path, catalog_ids: list[str]) -> dict[str, Catalog]:
    catalogs_dir = input_data_path / "catalogs"
    catalogs: dict[str, Catalog] = {}
    for catalog_id in catalog_ids:
        catalogs[catalog_id] = load_catalog(catalogs_dir / f"{catalog_id}.yml")
    return catalogs


def load_catalog(catalog_file_path: Path) -> Catalog:
    logger.info(f"Loading catalog from {catalog_file_path}")
    parsed = _load_catalog_file(catalog_file_path)
    catalog = Catalog(
        id=parsed.id,
        taxonomy=parsed.taxonomy,
        location_taxonomy_category=parsed.location.taxonomy_category,
        metrics={metric.id: _to_metric(metric) for metric in parsed.metrics_definition},
    )
    logger.info(
        f"Catalog {catalog.id!r} loaded with taxonomy {catalog.taxonomy!r} and {len(catalog.metrics)} metric(s)"
    )
    return catalog


def _load_catalog_file(catalog_file_path: Path) -> CatalogData:
    logger.debug(f"Loading catalog YAML from {catalog_file_path}")
    with open(catalog_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "catalog" not in raw:
        raise ValueError(f"catalog.yml file {catalog_file_path} is missing the 'catalog' key at the root")
    logger.debug(f"Catalog YAML parsed successfully from {catalog_file_path}")
    return CatalogData.model_validate(raw["catalog"])


def get_catalog_metric(catalog: Catalog, metric_id: str) -> Metric:
    logger.debug(f"Looking up metric {metric_id!r} in catalog {catalog.id!r}")
    if metric_id not in catalog.metrics:
        raise ValueError(f"Metric {metric_id} not found in catalog {catalog.id}")
    logger.debug(f"Metric {metric_id!r} found in catalog {catalog.id!r}")
    return catalog.metrics[metric_id]
