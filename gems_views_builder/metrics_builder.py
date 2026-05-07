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

from dataclasses import dataclass

import polars as pl
from gems.study.system import Component
from gems_views_builder.catalog import Catalog, Metric
from gems_views_builder.library import ModelLibrary
from gems_views_builder.system import InputSystem
from gems_views_builder.taxonomy import Taxonomy

from typing import Any, Dict

_METRIC_STRUCTURE_SCHEMA = pl.Schema(
    {
        "metric_id": pl.Utf8,
        "component": pl.Utf8,
        "metric_location": pl.Utf8,
        "breakdown_properties": pl.Utf8,
        "output": pl.Utf8,
        "weight_output_id": pl.Int64,  # # What will be value range here, probably we could use Int8 to save memory?
    }
)


@dataclass(frozen=True)
class MetricStructureTable:
    """Metric structure table produced from catalog metric terms (spec 2.1)."""

    dataframe: pl.DataFrame


def _component_properties(component: Component) -> dict[str, str]:
    """
    Normalize `component.properties` to a dict[str,str].

    Depending on Gems parser versions, properties may be:
    - dict-like {key: value}
    - list-like of items with (id|key, value) fields
    """
    raw: Any = getattr(component, "properties", None) or {}
    if isinstance(raw, dict):
        return {k: str(v) for k, v in raw.items()}
    out: dict[str, str] = {}
    for item in raw:
        if isinstance(item, dict):
            k = item.get("id") or item.get("key")
            v = item.get("value")
        else:
            k = getattr(item, "id", None) or getattr(item, "key", None)
            v = getattr(item, "value", None)
        if isinstance(k, str) and v is not None:
            out[k] = str(v)
    return out


def _component_property_value(component: Component, key: str) -> str | None:
    return _component_properties(component).get(key)


def _component_matches_property_filter(component: Component, clauses: tuple[tuple[str, str], ...] | None) -> bool:
    """If the metric defines filters, the component must match all (key,value) clauses."""
    if clauses is None:
        return True
    props = _component_properties(component)
    return all(props.get(k) == v for k, v in clauses)


def _format_breakdown_properties(props: dict[str, str], keys: tuple[str, ...] | None) -> str:
    if not keys:
        return "{}"
    pairs: list[str] = []
    for k in keys:
        if k not in props:
            return "{}"
        pairs.append(f"({k},{props[k]})")
    return "{" + ",".join(pairs) + "}"


class MetricStructureBuilder:
    def __init__(
        self,
        system: InputSystem,
        catalog: Catalog,
        metric: Metric,
        taxonomy: Taxonomy,
        model_library: ModelLibrary,
    ) -> None:
        self.system = system
        self.catalog = catalog
        self.metric = metric
        self.taxonomy = taxonomy
        self.model_library = model_library

    def build(self) -> MetricStructureTable:
        rows: list[dict[str, object]] = []
        for term in self.metric.terms:
            model_ids = self.model_library.get_components_in_taxonomy_category(term.taxonomy_category)
            for model_id in model_ids:
                qualified_ref = f"{self.model_library.id}.{model_id}"
                for component_id in self.system.get_instances_by_model(qualified_ref):
                    component = self.system.get_component(component_id)
                    
                    # # Decide does the component matches the filter, if yes they will contribute to the metric
                    if _component_matches_property_filter(component, self.metric.filter):
                        metric_location = self.system.get_location(component_id, term.location_ports)
                        loc_str = metric_location if isinstance(metric_location, str) else "|".join(metric_location)

                        props = _component_properties(component)
                        breakdown_properties = _format_breakdown_properties(props, self.metric.breakdown)
                        rows.append(
                            {
                                "metric_id": self.metric.id,
                                "component": component_id,
                                "metric_location": loc_str,
                                "breakdown_properties": breakdown_properties,
                                "output": term.output_id,
                                "weight_output_id": 1,
                            }
                        )
                        
        if not rows:
            return MetricStructureTable(pl.DataFrame(schema=_METRIC_STRUCTURE_SCHEMA))
        return MetricStructureTable(pl.DataFrame(rows, schema=_METRIC_STRUCTURE_SCHEMA))
