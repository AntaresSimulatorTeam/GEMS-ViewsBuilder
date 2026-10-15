# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace

from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, PropertySchema, Term
from gems_views_builder.input.component import Component
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig

SIMULATION_TABLE_ROW: dict[str, object] = {
    "block": "b1",
    "component": "comp",
    "output": "out",
    "absolute_time_index": 1,
    "block_time_index": 1,
    "scenario_index": 1,
    "value": 1.0,
    "basis_status": "ok",
}


def make_simulation_table_row(**overrides: object) -> dict[str, object]:
    return {**SIMULATION_TABLE_ROW, **overrides}


def make_aggregation_pattern(
    pattern_id: str,
    time_granularity: TimeGranularity,
    scenario: bool = False,
    spatial_filter: list[str] | None = None,
) -> AggregationPattern:
    return AggregationPattern(
        id=pattern_id,
        time_granularity=time_granularity,
        scenario=scenario,
        spatial_filter=spatial_filter,
    )


def make_view_config(
    view_id: str = "view",
    calendar_id: str = "calendar",
    location_taxonomy_category: str = "balance",
    taxonomy_id: str = "taxonomy",
    aggregation_patterns: tuple[AggregationPattern, ...] | None = None,
    extra_locations: list[str] | None = None,
    full_metric_ids: list[str] | None = None,
) -> ViewConfig:
    return ViewConfig(
        id=view_id,
        calendar_id=calendar_id,
        location_taxonomy_category=location_taxonomy_category,
        taxonomy_id=taxonomy_id,
        aggregation_patterns=aggregation_patterns
        if aggregation_patterns is not None
        else (make_aggregation_pattern(pattern_id="hourly", time_granularity=TimeGranularity.HOUR),),
        extra_locations=extra_locations or [],
        full_metric_ids=full_metric_ids or [],
    )


def make_term(
    taxonomy_category: str = "production",
    output_id: str = "p",
    location_port: str | None = None,
) -> Term:
    return Term(taxonomy_category=taxonomy_category, output_id=output_id, location_port=location_port)


def make_metric(
    metric_id: str = "M",
    taxonomy_category: str = "production",
    location_port: str | None = None,
    output_id: str = "p",
    terms: list[Term] | None = None,
    terms_operator: AggregOperatorType = AggregOperatorType.SUM,
    time_operator: AggregOperatorType = AggregOperatorType.SUM,
    breakdown: list[PropertySchema] | None = None,
    filter: PropertySchema | None = None,
) -> Metric:
    resolved_terms = terms if terms is not None else [make_term(taxonomy_category, output_id, location_port)]
    return Metric(
        id=metric_id,
        terms=resolved_terms,
        terms_operator=terms_operator,
        time_operator=time_operator,
        breakdown=breakdown,
        filter=filter,
    )


def make_catalog(
    catalog_id: str = "catalog",
    taxonomy: str = "taxonomy",
    location_taxonomy_category: str = "balance",
    metrics: dict[str, Metric] | None = None,
    metric_ids: list[str] | None = None,
) -> Catalog:
    if metrics is None:
        metrics = {metric_id: make_metric(metric_id) for metric_id in (metric_ids or [])}
    return Catalog(
        id=catalog_id,
        taxonomy=taxonomy,
        location_taxonomy_category=location_taxonomy_category,
        metrics=metrics,
    )


def make_taxonomy(
    taxonomy_id: str = "taxonomy",
    categories: dict[str, TaxonomyCategory] | None = None,
) -> Taxonomy:
    if categories is None:
        categories = {"balance": TaxonomyCategory(id="balance")}
    return Taxonomy(id=taxonomy_id, categories=categories)


def make_raw_component(
    component_id: str,
    model_id: str = "lib.model",
    properties: dict[str, str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(id=component_id, model=SimpleNamespace(id=model_id), properties=properties or {})


def make_component(
    component_id: str = "fake",
    properties: dict[str, str] | None = None,
    taxonomy_category: str | None = None,
    model_id: str = "lib.model",
    self_located_at: str | None = None,
) -> Component:
    component = Component(
        make_raw_component(component_id, model_id, properties),
        taxonomy_category=taxonomy_category,
    )
    if self_located_at is not None:
        component.locations[(None, self_located_at)] = component
    return component
