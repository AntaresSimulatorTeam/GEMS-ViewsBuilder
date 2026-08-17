# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""ViewConfig models and lazy loaders for view_config.yml."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field, field_validator

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
    # Here will be filter in  PR


class Scope(ViewBuilderBasedModel):
    location: Location
    calendar: str


class ScenarioAggregation(ViewBuilderBasedModel):
    time: TimeGranularity
    scenario: bool


class Aggregations(ViewBuilderBasedModel):
    scenario_aggregations: tuple[ScenarioAggregation, ...] = Field(min_length=1)
    extra_locations: list[ExtraLocation] | None = Field(default=None, min_length=0)


class CatalogId(ViewBuilderBasedModel):
    id: str


class MetricId(ViewBuilderBasedModel, frozen=True):
    id: str


class RawViewConfig(ViewBuilderBasedModel):
    id: str
    scope: Scope
    aggregations: Aggregations
    catalogs: list[CatalogId]
    metrics: set[MetricId]

    @field_validator("metrics", mode="before")
    @classmethod
    def parse_metric_ids(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return {item if isinstance(item, MetricId) else MetricId.model_validate(item) for item in value}


@dataclass
class ViewConfig:
    id: str
    input_data_path: Path
    calendar_id: str
    location_taxonomy_category: str
    scenario_aggregations: tuple[ScenarioAggregation, ...]
    catalog_ids: set[str] = field(default_factory=set)
    extra_locations: list[str] = field(default_factory=list)
    metric_ids: set[str] = field(default_factory=set)
    metrics: list[Metric] = field(default_factory=list)

    def fetch_metrics(self, catalogs: dict[str, Catalog]) -> None:
        logging.debug(f"Fetching {len(self.metric_ids)} metric(s) from catalogs")
        unique_metric_ids = set()
        for metric_ref in self.metric_ids:
            if "." not in metric_ref or metric_ref.startswith(".") or metric_ref.endswith("."):
                raise ValueError(
                    f"Invalid metric id '{metric_ref}'. "
                    f"Expected format '<catalog_id>.<metric_id>' for catalog {self.catalog_ids}"
                )
            catalog_id, metric_id = metric_ref.split(".", 1)

            # Temporary solution this needs to be handled while validating
            # With this we can safely remove part counter from TimeAggregator
            # Catalog <-> ViewConfig validation
            # View Config <-> Taxonomy
            # Catalog <-> Taxonomy
            if metric_id in unique_metric_ids:
                raise ValueError(f"Metric id={metric_id!r} is already defined in some catalog")

            unique_metric_ids.add(metric_id)

            if catalog_id not in self.catalog_ids:
                raise ValueError(f"Catalog {catalog_id!r} not found in view config")

            logging.debug(f"Mapped metric {metric_id!r} to catalog {catalog_id!r}")

            self.metrics.append(catalogs[catalog_id].get_metric(metric_id))

    def get_metrics(self) -> list[Metric]:
        return self.metrics


def load_view_config(config_file_path: Path) -> ViewConfig:
    logging.info(f"Loading view config from {config_file_path}")
    raw_view_config = load_raw_view_config_file(config_file_path)
    input_data_path = config_file_path.parent

    view_config = ViewConfig(
        id=raw_view_config.id,
        input_data_path=input_data_path,
        calendar_id=raw_view_config.scope.calendar,
        location_taxonomy_category=raw_view_config.scope.location.taxonomy_category,
        catalog_ids={c.id for c in raw_view_config.catalogs},
        scenario_aggregations=raw_view_config.aggregations.scenario_aggregations,
        metric_ids={metric.id for metric in raw_view_config.metrics},
        extra_locations=[loc.id for loc in (raw_view_config.aggregations.extra_locations or [])],
    )
    logging.info(
        f"View config {view_config.id!r} loaded: calendar={view_config.calendar_id!r}, "
        f"catalogs={len(view_config.catalog_ids)}, metrics={len(view_config.metric_ids)}"
    )
    return view_config


def load_raw_view_config_file(view_file_path: Path) -> RawViewConfig:
    logging.info(f"Parsing view config YAML from {view_file_path}")
    with open(view_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "view" not in raw:
        raise ValueError(f"view_config.yml file {view_file_path} is missing the 'view' key at the root")
    logging.info(f"View config YAML parsed successfully from {view_file_path}")
    return RawViewConfig.model_validate(raw["view"])
