# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder
from tests.common import make_component, make_metric, make_view_config


def test_view_config_parses_extra_locations(tmp_path: Path) -> None:
    # Arrange
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: view_area
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
    extra-locations:
      - id: country
      - id: district
      - id: city_part
  aggregations-patterns:
    - id: hourly
      time_granularity: hour
      scenario: false
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""
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
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations-patterns:
    - id: hourly
      time_granularity: hour
      scenario: false
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""
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
    view_config = make_view_config(extra_locations=["country", "district", "city_part"])
    builder = MetricStructureTableBuilder(view_config, components_by_taxon)

    # Act
    table = builder.build(make_metric("LOAD"))
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
    table = builder.build(make_metric("LOAD"))
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["balance-node"]


def test_missing_extra_properties_keeps_primary_only() -> None:
    # Arrange
    balance_node = make_component("balance-node", properties={})
    production = make_component("some-prod")
    production.locations[(None, "balance")] = balance_node

    components_by_taxon = {"balance": [balance_node], "production": [production]}
    view_config = make_view_config(extra_locations=["country", "district", "city_part"])
    builder = MetricStructureTableBuilder(view_config, components_by_taxon)

    # Act
    table = builder.build(make_metric("LOAD"))
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["balance-node"]


def test_partial_extra_locations_emits_only_present_ones() -> None:
    # Arrange
    balance_node = make_component("balance-node", properties={"country": "France", "district": "La Defense"})
    production = make_component("some-prod")
    production.locations[(None, "balance")] = balance_node

    components_by_taxon = {"balance": [balance_node], "production": [production]}
    view_config = make_view_config(extra_locations=["country", "district", "city_part"])
    builder = MetricStructureTableBuilder(view_config, components_by_taxon)

    # Act
    table = builder.build(make_metric("LOAD"))
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["balance-node", "France", "La Defense"]
