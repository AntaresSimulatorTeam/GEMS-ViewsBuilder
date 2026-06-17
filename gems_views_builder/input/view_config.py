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

"""ViewConfig models and lazy loaders for view_config.yml."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field

from gems_views_builder.base_model import ViewBuilderBasedModel
from gems_views_builder.input.catalog import Catalog, load_catalog


class TimeAggregation(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Scope(ViewBuilderBasedModel):
    taxonomy_category: str | None = Field(None, alias="taxonomy-category")
    calendar: str | None = None


class Aggregation(ViewBuilderBasedModel):
    time: TimeAggregation | None = None


class CatalogRef(ViewBuilderBasedModel):
    id: str


class MetricRef(ViewBuilderBasedModel):
    id: str


class ViewData(ViewBuilderBasedModel):
    id: str
    scope: list[Scope]
    aggregation: list[Aggregation]
    catalog: list[CatalogRef]
    metrics: list[MetricRef]


@dataclass
class ViewConfig:
    id: str
    input_data_path: Path
    location_taxonomy_category: str | None = None
    calendar_id: str | None = None
    catalog_ids: list[str] = field(default_factory=list)
    time_aggregation: TimeAggregation | None = None
    catalog_to_metrics: dict[str, list[str]] = field(default_factory=dict)

    # # This method needs to be inside catalog.py
    def load_catalog(self, catalog_id: str) -> Catalog:
        """
        Load only the requested catalog when needed instead of preloading all catalogs.
        """
        catalog_file = self.input_data_path / "catalogs" / f"{catalog_id}.yml"
        if not catalog_file.exists():
            raise FileNotFoundError(f"Catalog file {catalog_file} not found")
        logging.info(f"Loading catalog {catalog_id!r} from view config")
        return load_catalog(catalog_file)


def load_view_config(config_file_path: Path) -> ViewConfig:
    logging.info(f"Loading view config from {config_file_path}")
    parsed = load_view_file(config_file_path)
    input_data_path = config_file_path.parent
    location_taxonomy_category = next(
        (item.taxonomy_category for item in parsed.scope if item.taxonomy_category),
        None,
    )
    if location_taxonomy_category is None:
        raise ValueError(
            f"view_config.yml '{parsed.id}': no 'taxonomy-category' found in scope. "
            f"At least one scope entry must define a taxonomy-category"
        )

    view_config = ViewConfig(
        id=parsed.id,
        input_data_path=input_data_path,
        location_taxonomy_category=location_taxonomy_category,
        calendar_id=next((item.calendar for item in parsed.scope if item.calendar), None),
        catalog_ids=[c.id for c in parsed.catalog],
        time_aggregation=parsed.aggregation[0].time if parsed.aggregation else None,
        catalog_to_metrics=group_metrics_by_catalog(parsed.id, parsed.metrics),
    )
    logging.info(
        f"View config {view_config.id!r} loaded: calendar={view_config.calendar_id!r}, "
        f"catalogs={len(view_config.catalog_ids)}, metric groups={len(view_config.catalog_to_metrics)}"
    )
    return view_config


def load_view_file(view_file_path: Path) -> ViewData:
    logging.info(f"Parsing view config YAML from {view_file_path}")
    with open(view_file_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if "view" not in raw:
        raise ValueError(f"view_config.yml file {view_file_path} is missing the 'view' key at the root")
    logging.info(f"View config YAML parsed successfully from {view_file_path}")
    return ViewData.model_validate(raw["view"])


def group_metrics_by_catalog(view_config_id: str, metrics: list[MetricRef]) -> dict[str, list[str]]:
    logging.debug(f"Grouping {len(metrics)} metric reference(s) by catalog")
    catalog_to_metrics: dict[str, list[str]] = defaultdict(list)
    for metric in metrics:
        if "." not in metric.id or metric.id.startswith(".") or metric.id.endswith("."):
            raise ValueError(
                f"view_config.yml '{view_config_id}': invalid metric id '{metric.id}'. "
                "Expected format '<catalog_id>.<metric_id>'"
            )
        catalog_id, metric_id = metric.id.split(".", 1)
        catalog_to_metrics[catalog_id].append(metric_id)
        logging.debug(f"Mapped metric reference {metric.id!r} to catalog {catalog_id!r}")
    return catalog_to_metrics
