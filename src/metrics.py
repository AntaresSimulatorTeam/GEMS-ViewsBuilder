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

"""Metric operators, BusinessMetricTerm, BusinessMetric, BusinessCatalog, BusinessViewConfiguration."""

from calendar import Calendar
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from location import LocationPorts
from taxonomy import Taxonomy


class TimeAggregation(Enum):
    """
    Time aggregation.
    """

    HOURS = "hours"  # from example it will be used in future


@dataclass
class Aggregation:
    time: Optional[TimeAggregation] = None  # for now it will be used in future


"""Operator for time && terms aggregation. Kept separate from Operator for future flexibility."""


class TermsOperator(Enum):
    """
    Operator for terms.
    """

    SUM = "sum"
    AVG = "avg"


class TimeOperator(Enum):
    """
    Operator for time.
    """

    SUM = "sum"
    AVG = "avg"


@dataclass
class Term:
    taxonomy_category: str
    output_id: str
    location_ports: LocationPorts
    weight_output_id: Optional[str] = None


@dataclass
class Metric:
    id: str
    terms: list[Term]
    terms_operator: TermsOperator
    time_operator: TimeOperator
    breakdown_property: Optional[str] = None
    filter: Optional[tuple[str, str]] = None


@dataclass
class Catalog:
    """
    In memory representation of the catalog.yml file
    id: id of the catalog
    taxonomy: taxonomy id
    location_taxonomy_category: Taxonomy set of taxonomy categories that are used as localization elements, e.g. balance is taxonomy for area,zones ... etc
    metrics_definition: dict[str, Metric] dictionary of metrics definitions
    """

    id: str
    taxonomy: str
    location_taxonomy_category: Taxonomy
    metrics_definition: dict[str, Metric]


@dataclass
class Scope:
    """
    Scope of the view.
    """

    location_taxonomy_category: str
    calendar: Calendar


@dataclass
class BusinessViewConfig:
    """
    In memory representation of the business-view-config.yml file.
    Id: id of the view.
    Scope: scope of the view. -> Which calendar and which taxonomy category are used.
    Catalogs: set of catalogs that are used to build the view.
    Aggregation: aggregation of the view. -> Which time and which terms are used.
    Metrics: list of metrics that are used to build the view. -> Which metrics are used.(id : catalog1.OVERALL_COST, id: catalog2.PRICE...)
    """

    id: str
    scope: Scope
    catalogs: list[Catalog]
    aggregation: Aggregation
    metrics: list[tuple[str, str]]
