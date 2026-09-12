# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""ViewConfig models for view_config.yml."""

import logging
from dataclasses import dataclass, field
from enum import Enum

from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.input.catalog import Catalog, Metric


class ExtraLocation(ViewBuilderBasedModel):
    id: str


class TimeGranularity(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Location(ViewBuilderBasedModel):
    taxonomy_category: str


class Scope(ViewBuilderBasedModel):
    location: Location
    calendar: str
    extra_locations: list[ExtraLocation] | None = Field(default=None, min_length=0)


class AggregationPattern(ViewBuilderBasedModel):
    id: str
    time_granularity: TimeGranularity
    scenario: bool
    spatial_filter: list[str] | None = Field(default=None)


class CatalogId(ViewBuilderBasedModel):
    id: str


class MetricId(ViewBuilderBasedModel, frozen=True):
    id: str


class RawViewConfig(ViewBuilderBasedModel):
    id: str
    scope: Scope
    aggregations_patterns: tuple[AggregationPattern, ...] = Field(min_length=1)
    catalogs: list[CatalogId]
    metrics: list[MetricId]


@dataclass
class ViewConfig:
    id: str
    calendar_id: str
    location_taxonomy_category: str
    aggregation_patterns: tuple[AggregationPattern, ...]
    catalog_ids: set[str] = field(default_factory=set)
    extra_locations: list[str] = field(default_factory=list)
    metric_ids: list[str] = field(default_factory=list)
    metrics: list[Metric] = field(default_factory=list)

    def fetch_metrics(self, catalogs: dict[str, Catalog]) -> None:
        logging.debug(f"Fetching {len(self.metric_ids)} metric(s) from catalogs")
        for metric_ref in self.metric_ids:
            if "." not in metric_ref or metric_ref.startswith(".") or metric_ref.endswith("."):
                raise ValueError(
                    f"Invalid metric id '{metric_ref}'. "
                    f"Expected format '<catalog_id>.<metric_id>' for catalog {self.catalog_ids}"
                )
            catalog_id, metric_id = metric_ref.split(".", 1)

            if catalog_id not in self.catalog_ids:
                raise ValueError(f"Catalog {catalog_id!r} not found in view config")

            logging.debug(f"Mapped metric {metric_id!r} to catalog {catalog_id!r}")

            self.metrics.append(catalogs[catalog_id].get_metric(metric_id))

    def get_metrics(self) -> list[Metric]:
        return self.metrics
