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

from pathlib import Path
from types import SimpleNamespace

from gems_views_builder.input.catalog import Metric, Term, TermsOperator, TimeOperator
from gems_views_builder.input.component import Component
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.metrics_structure_builder import MetricStructureTableBuilder


def component(component_id: str, properties: dict[str, str] | None = None) -> Component:
    return Component(
        SimpleNamespace(
            id=component_id,
            model=SimpleNamespace(id="lib.model"),
            properties=properties or {},
        )
    )


def metric() -> Metric:
    return Metric(
        id="LOAD",
        terms_operator=TermsOperator.SUM,
        time_operator=TimeOperator.SUM,
        terms=[Term(taxonomy_category="production", output_id="p", location_port=None)],
    )


def located_at(component: Component, location: Component, location_category: str = "balance") -> Component:
    component.locations[(None, location_category)] = location
    return component


def test_view_config_parses_extra_locations(tmp_path: Path) -> None:
    # Arrange
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: view_area
  scope:
    - taxonomy-category: balance
    - calendar: calendar_file
  aggregation:
    time: hour
    extra-locations:
      - id: country
      - id: district
      - id: city_part
  catalog:
    - id: catalog
  metrics:
    - id: catalog.LOAD
""".strip()
    )

    # Act
    config = load_view_config(config_path)

    # Assert
    assert config.extra_locations == ["country", "district", "city_part"]


def test_spatial_aggregation_emits_country_district_and_city_part() -> None:
    # Arrange
    paris = component(
        "paris",
        properties={
            "country": "France",
            "district": "IleDeFrance",
            "city_part": "Downtown",
        },
    )
    gen_paris = located_at(component("gen_paris"), paris)
    components_by_taxon = {"balance": [paris], "production": [gen_paris]}
    builder = MetricStructureTableBuilder(
        "balance",
        components_by_taxon,
        extra_locations=["country", "district", "city_part"],
    )

    # Act
    table = builder.build(metric())
    rows = table.dataframe.collect()

    # Assert
    assert rows["component"].to_list() == ["gen_paris", "gen_paris", "gen_paris"]
    assert rows["metric_location"].to_list() == ["France", "IleDeFrance", "Downtown"]


def test_spatial_aggregation_keeps_primary_when_extra_locations_absent() -> None:
    # Arrange
    paris = component("paris", properties={"country": "France"})
    gen_paris = located_at(component("gen_paris"), paris)
    components_by_taxon = {"balance": [paris], "production": [gen_paris]}
    builder = MetricStructureTableBuilder("balance", components_by_taxon)

    # Act
    table = builder.build(metric())
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["paris"]


def test_spatial_aggregation_keeps_primary_when_properties_missing() -> None:
    # Arrange
    paris = component("paris", properties={})
    gen_paris = located_at(component("gen_paris"), paris)
    components_by_taxon = {"balance": [paris], "production": [gen_paris]}
    builder = MetricStructureTableBuilder(
        "balance",
        components_by_taxon,
        extra_locations=["country", "district", "city_part"],
    )

    # Act
    table = builder.build(metric())
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["paris"]


def test_spatial_aggregation_uses_only_present_properties() -> None:
    # Arrange
    paris = component("paris", properties={"country": "France", "district": "La Defense"})
    gen_paris = located_at(component("gen_paris"), paris)
    components_by_taxon = {"balance": [paris], "production": [gen_paris]}
    builder = MetricStructureTableBuilder(
        "balance",
        components_by_taxon,
        extra_locations=["country", "district", "city_part"],
    )

    # Act
    table = builder.build(metric())
    locations = table.dataframe.collect()["metric_location"].to_list()

    # Assert
    assert locations == ["France", "La Defense"]
