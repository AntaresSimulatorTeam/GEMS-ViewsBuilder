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

"""BusinessViewConfig: in memory representation of a business_view_config.yml file."""

from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field

from src.base_model import GEMSViewBuilderBaseModel


class TimeAggregation(Enum):
    HOURS = "hours"


class Scope(GEMSViewBuilderBaseModel):
    taxonomy_category: str | None = Field(None, alias="taxonomy-category")
    calendar: str | None = None


class Aggregation(GEMSViewBuilderBaseModel):
    time: TimeAggregation | None = None


class CatalogRef(GEMSViewBuilderBaseModel):
    id: str


class MetricRef(GEMSViewBuilderBaseModel):
    id: str


class BusinessViewData(GEMSViewBuilderBaseModel):
    id: str
    scope: list[Scope]
    aggregation: list[Aggregation]
    catalog: list[CatalogRef]
    metrics: list[MetricRef]


class BusinessViewConfig:
    """
    In memory representation of the business_view_config.yml file.
    """

    def __init__(self, config_file_path: Path) -> None:
        parsed = self._load_business_view_file(config_file_path)
        self.id = parsed.id
        self.location_taxonomy_category: str = next(
            item.taxonomy_category for item in parsed.scope if item.taxonomy_category
        )
        self.calendar_id: str = next(item.calendar for item in parsed.scope if item.calendar)
        self.catalog_ids: list[str] = [c.id for c in parsed.catalog]
        self.time_aggregation: TimeAggregation | None = parsed.aggregation[0].time if parsed.aggregation else None
        self.metrics: set[tuple[str, str]] = {
            (parts[0], parts[1]) for m in parsed.metrics if len(parts := m.id.split(".", 1)) == 2
        }

    def _load_business_view_file(self, business_view_file_path: Path) -> BusinessViewData:
        with open(business_view_file_path) as f:
            raw = yaml.safe_load(f)
        return BusinessViewData.model_validate(raw["view"])
