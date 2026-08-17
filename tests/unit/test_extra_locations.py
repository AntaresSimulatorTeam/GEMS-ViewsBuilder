# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from types import SimpleNamespace

from gems_views_builder.input.catalog import AggregOperatorType, Metric, Term
from gems_views_builder.input.component import Component
from gems_views_builder.input.view_config import ScenarioAggregation, TimeGranularity, ViewConfig, load_view_config
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def make_component(component_id: str, properties: dict[str, str] | None = None) -> Component:
    return Component(
        SimpleNamespace(
            id=component_id,
            model=SimpleNamespace(id="lib.model"),
            properties=properties or {},
        )
    )


def make_metric() -> Metric:
    return Metric(
        id="LOAD",
        terms_operator=AggregOperatorType.SUM,
        time_operator=AggregOperatorType.SUM,
        terms=[Term(taxonomy_category="production", output_id="p", location_port=None)],
    )


def make_view_config(extra_locations: list[str] | None = None) -> ViewConfig:
    return ViewConfig(
        id="view_area",
        input_data_path=Path("."),
        calendar_id="calendar_file",
        location_taxonomy_category="balance",
        scenario_aggregations=(ScenarioAggregation(id="hourly", time=TimeGranularity.HOUR, scenario=False),),
        extra_locations=extra_locations or [],
    )


def test_view_config_parses_extra_locations(tmp_path: Path) -> None:
    # Arrange
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: view_area
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations:
    scenario-aggregations:
      - id: hourly
        time: hour
        scenario: false
    extra-locations:
      - id: country
      - id: district
      - id: city_part
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
""".strip()
    )

    # Act
    config = load_view_config(config_path)

    # Assert
    assert config.extra_locations == ["country", "district", "city_part"]


def test_view_config_extra_locations_defaults_to_empty_list(tmp_path: Path) -> None:
    # Arrange
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: view_area
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations:
    scenario-aggregations:
      - id: hourly
        time: hour
        scenario: false
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
""".strip()
    )

    # Act
    config = load_view_config(config_path)

    # Assert
    assert config.extra_locations == []


def test_located_component_emits_primary_and_extra_locations() -> None:
    # Arrange
    # Balance node: this component is the location for the other component
    location_properties = {"country": "France", "district": "IleDeFrance", "city_part": "Downtown"}
    balance_node = make_component("balance-node", properties=location_properties)

    # Other component
    production = make_component("some-prod")
    production.locations[(None, "balance")] = balance_node

    components_by_taxon = {"balance": [balance_node], "production": [production]}
    view_config = make_view_config(["country", "district", "city_part"])
    builder = MetricStructureTableBuilder(view_config, components_by_taxon)

    # Act
    table = builder.build(make_metric())
    rows = table.dataframe.collect()

    # Assert
    assert rows["component"].to_list() == ["some-prod", "some-prod", "some-prod", "some-prod"]
    assert rows["metric_location"].to_list() == ["balance-node", "France", "IleDeFrance", "Downtown"]


def test_no_extra_locations_keeps_primary_only() -> None:
    # Arrange
    balance_node = make_component("balance-node", properties={"country": "France"})
    production = make_component("some-prod")
    production.locations[(None, "balance")] = balance_node

    components_by_taxon = {"balance": [balance_node], "production": [production]}
    builder = MetricStructureTableBuilder(make_view_config(), components_by_taxon)

    # Act
    table = builder.build(make_metric())
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["balance-node"]


def test_missing_extra_properties_keeps_primary_only() -> None:
    # Arrange
    balance_node = make_component("balance-node", properties={})
    production = make_component("some-prod")
    production.locations[(None, "balance")] = balance_node

    components_by_taxon = {"balance": [balance_node], "production": [production]}
    view_config = make_view_config(["country", "district", "city_part"])
    builder = MetricStructureTableBuilder(view_config, components_by_taxon)

    # Act
    table = builder.build(make_metric())
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["balance-node"]


def test_partial_extra_locations_emits_only_present_ones() -> None:
    # Arrange
    balance_node = make_component("balance-node", properties={"country": "France", "district": "La Defense"})
    production = make_component("some-prod")
    production.locations[(None, "balance")] = balance_node

    components_by_taxon = {"balance": [balance_node], "production": [production]}
    view_config = make_view_config(["country", "district", "city_part"])
    builder = MetricStructureTableBuilder(view_config, components_by_taxon)

    # Act
    table = builder.build(make_metric())
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["balance-node", "France", "La Defense"]
