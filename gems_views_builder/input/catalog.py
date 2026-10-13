# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Catalog .yml parsing models and typed representation."""

import logging
from dataclasses import dataclass, field
from enum import Enum

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
