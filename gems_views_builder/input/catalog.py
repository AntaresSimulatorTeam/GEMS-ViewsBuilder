# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Catalog .yml parsing models and typed representation."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from pydantic import field_validator

from gems_views_builder.base_model import ViewBuilderBasedModel

"""
They are the same for now but we could keep them separated for future use.
In fact they represent the different operators
"""


class AggregOperatorType(Enum):
    SUM = "sum"
    AVG = "avg"


class TermData(ViewBuilderBasedModel):
    taxonomy_category: str
    output_id: str
    location_port: str | None
    weight_output_id: str | None = None

    @field_validator("location_port")
    @classmethod
    def validate_location_port(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("location-port must not be an empty or blank string")
        return value


class PropertySchema(ViewBuilderBasedModel):
    """Reference to a system/taxonomy property by key; value is required only for metric filters."""

    key: str
    value: str | None = None


class MetricData(ViewBuilderBasedModel):
    id: str
    terms: list[TermData]
    terms_operator: AggregOperatorType
    time_operator: AggregOperatorType
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
    location_port: str | None
    weight_output_id: str | None = None


@dataclass
class Metric:
    id: str
    terms: list[Term]
    terms_operator: AggregOperatorType
    time_operator: AggregOperatorType
    breakdown: list[PropertySchema] | None = None
    filter: PropertySchema | None = None


@dataclass
class Catalog:
    id: str
    taxonomy: str
    location_taxonomy_category: str
    metrics: dict[str, Metric] = field(default_factory=dict)

    def get_metric(self, metric_id: str) -> Metric:
        logging.debug(f"Looking up metric {metric_id!r} in catalog {self.id!r}")
        if metric_id not in self.metrics:
            logging.info(f"[{metric_id}] Metric not found in catalog '{self.id}' — skipping")
            raise ValueError(f"Metric {metric_id} not found in catalog {self.id}")
        logging.debug(f"Metric {metric_id!r} found in catalog {self.id!r}")
        return self.metrics[metric_id]


def to_term(term_data: TermData) -> Term:
    return Term(
        taxonomy_category=term_data.taxonomy_category,
        output_id=term_data.output_id,
        location_port=term_data.location_port,
        weight_output_id=term_data.weight_output_id,
    )


def to_metric(metric_data: MetricData) -> Metric:
    return Metric(
        id=metric_data.id,
        terms=[to_term(term) for term in metric_data.terms],
        terms_operator=metric_data.terms_operator,
        time_operator=metric_data.time_operator,
        breakdown=list(metric_data.breakdown) if metric_data.breakdown else None,
        filter=metric_data.filter,
    )


def load_catalogs(catalogs_dir: Path, catalog_ids: set[str]) -> list[Catalog]:
    return [load_catalog(catalogs_dir / f"{catalog_id}.yml") for catalog_id in catalog_ids]


def load_catalog(catalog_file_path: Path) -> Catalog:
    logging.info(f"Loading catalog from {catalog_file_path}")
    parsed_catalog = load_catalog_file(catalog_file_path)
    catalog = Catalog(
        id=parsed_catalog.id,
        taxonomy=parsed_catalog.taxonomy,
        location_taxonomy_category=parsed_catalog.location.taxonomy_category,
        metrics={metric.id: to_metric(metric) for metric in parsed_catalog.metrics_definition},
    )
    logging.info(
        f"Catalog {catalog.id!r} loaded with taxonomy {catalog.taxonomy!r} and {len(catalog.metrics)} metric(s)"
    )
    return catalog


def load_catalog_file(catalog_file_path: Path) -> CatalogData:
    logging.debug(f"Loading catalog YAML from {catalog_file_path}")
    if not catalog_file_path.exists():
        raise FileNotFoundError(f"Catalog file {catalog_file_path} not found")
    with open(catalog_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "catalog" not in raw:
        raise ValueError(f"catalog.yml file {catalog_file_path} is missing the 'catalog' key at the root")
    return CatalogData.model_validate(raw["catalog"])
