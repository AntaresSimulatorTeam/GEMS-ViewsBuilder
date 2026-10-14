# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace

import polars as pl

from gems_views_builder import AggregOperatorType, Metric, PropertySchema, Term
from gems_views_builder.input.component import Component
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def make_component(properties: dict[str, str] | None = None, component_id: str = "fake") -> Component:
    component = Component(
        SimpleNamespace(id=component_id, model=SimpleNamespace(id="lib.model"), properties=properties or {})
    )
    component.taxonomy_category = "production"
    component.locations[(None, "balance")] = component
    return component


def make_view_config() -> ViewConfig:
    return ViewConfig(
        id="view",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        taxonomy_id="taxonomy",
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
    )


def test_match_keeps_components_with_the_filter_value() -> None:
    component = make_component({"technology": "gas"}, "gen_1")
    assert component.match(None) is True
    assert component.match(PropertySchema(key="technology", value="gas")) is True
    assert component.match(PropertySchema(key="technology", value="nuclear")) is False


def test_format_breakdown_properties_missing_keys_use_none_literal() -> None:
    breakdown = [
        PropertySchema(key="country"),
        PropertySchema(key="company"),
        PropertySchema(key="technology"),
    ]
    component = make_component({"company": "rhonepower"})
    assert component.format_breakdown_properties(breakdown) == "{(country,None),(company,rhonepower),(technology,None)}"


def test_format_breakdown_properties_all_keys_present() -> None:
    breakdown = [PropertySchema(key="technology"), PropertySchema(key="company")]
    component = make_component({"technology": "gas", "company": "rhonepower"})
    assert component.format_breakdown_properties(breakdown) == "{(technology,gas),(company,rhonepower)}"


def test_breakdown_follows_schema_order_not_property_insertion_order() -> None:
    """Two components with the same properties, inserted in opposite order, share one breakdown key."""
    breakdown = [PropertySchema(key="technology"), PropertySchema(key="company")]
    technology_first: dict[str, str] = {}
    technology_first["technology"] = "gas"
    technology_first["company"] = "rhonepower"
    company_first: dict[str, str] = {}
    company_first["company"] = "rhonepower"
    company_first["technology"] = "gas"
    expected = "{(technology,gas),(company,rhonepower)}"

    assert make_component(technology_first).format_breakdown_properties(breakdown) == expected
    assert make_component(company_first).format_breakdown_properties(breakdown) == expected


def test_format_breakdown_properties_empty_breakdown() -> None:
    component = make_component({"company": "x"})
    assert component.format_breakdown_properties(None) == "{}"


def test_structure_table_applies_filter_and_breakdown() -> None:
    gas = make_component({"technology": "gas", "company": "rhonepower"}, "gas")
    nuclear = make_component({"technology": "nuclear", "company": "rhonepower"}, "nuclear")
    metric = Metric(
        id="PRODUCTION",
        terms=[Term(taxonomy_category="production", output_id="generation", location_port=None)],
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.SUM,
        breakdown=[PropertySchema(key="technology"), PropertySchema(key="company")],
        filter=PropertySchema(key="technology", value="gas"),
    )

    table = MetricStructureTableBuilder(make_view_config(), {"production": [gas, nuclear]}).build(metric)
    df = table.dataframe.collect()

    assert df["component"].to_list() == ["gas"]
    assert df["breakdown_properties"][0] == "{(technology,gas),(company,rhonepower)}"
    assert df.filter(pl.col("component") == "nuclear").height == 0
