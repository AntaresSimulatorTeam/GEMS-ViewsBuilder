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

from gems_views_builder.base_model import ViewBuilderBasedModel

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


class PropertyFilter(ViewBuilderBasedModel):
    key: str
    value: str


class BreakdownKey(ViewBuilderBasedModel):
    key: str


class BreakdownProperty(ViewBuilderBasedModel):
    """Legacy single breakdown clause (key,value)."""

    key: str
    value: str


class MetricData(ViewBuilderBasedModel):
    id: str
    terms: list[TermData]
    terms_operator: TermsOperator
    time_operator: TimeOperator
    # New schema: group-by keys
    breakdown: list[BreakdownKey] | None = None
    # Legacy schema: single clause
    breakdown_property: BreakdownProperty | None = None
    # New schema: list of clauses; legacy: a single clause
    filter: list[PropertyFilter] | PropertyFilter | None = None


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
    breakdown: tuple[str, ...] | None = None
    filter: tuple[tuple[str, str], ...] | None = None


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
    filter_clauses: tuple[tuple[str, str], ...] | None
    if metric_data.filter is None:
        filter_clauses = None
    elif isinstance(metric_data.filter, list):
        filter_clauses = tuple((f.key, f.value) for f in metric_data.filter)
    else:
        filter_clauses = ((metric_data.filter.key, metric_data.filter.value),)

    breakdown: tuple[str, ...] | None = None
    if metric_data.breakdown is not None:
        breakdown = tuple(b.key for b in metric_data.breakdown)
    elif metric_data.breakdown_property is not None:
        # Legacy: treat breakdown_property as a filter clause on that key and
        # use the key itself as breakdown dimension.
        breakdown = (metric_data.breakdown_property.key,)
        filter_clauses = tuple(
            list(filter_clauses or ()) + [(metric_data.breakdown_property.key, metric_data.breakdown_property.value)]
        )
    return Metric(
        id=metric_data.id,
        terms=[_to_term(term) for term in metric_data.terms],
        terms_operator=metric_data.terms_operator,
        time_operator=metric_data.time_operator,
        breakdown=breakdown,
        filter=filter_clauses,
    )


def load_catalog(catalog_file_path: Path) -> Catalog:
    parsed = _load_catalog_file(catalog_file_path)
    return Catalog(
        id=parsed.id,
        taxonomy=parsed.taxonomy,
        location_taxonomy_category=parsed.location.taxonomy_category,
        metrics={metric.id: _to_metric(metric) for metric in parsed.metrics_definition},
    )


def _load_catalog_file(catalog_file_path: Path) -> CatalogData:
    with open(catalog_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "catalog" not in raw:
        raise ValueError(f"catalog.yml file {catalog_file_path} is missing the 'catalog' key at the root")
    return CatalogData.model_validate(raw["catalog"])


def get_catalog_metric(catalog: Catalog, metric_id: str) -> Metric:
    if metric_id not in catalog.metrics:
        raise ValueError(f"Metric {metric_id} not found in catalog {catalog.id}")
    return catalog.metrics[metric_id]
