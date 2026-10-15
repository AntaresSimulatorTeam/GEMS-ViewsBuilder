# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder import load_view_config


def test_raises_on_invalid_metric_id_format(tmp_path: Path) -> None:
    invalid_config = tmp_path / "view_config.yml"
    invalid_config.write_text(
        """
view:
  id: invalid_metric_format
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
    - id: catalog_1
  metrics:
    - id: invalid_metric_id
"""
    )

    config = load_view_config(invalid_config)

    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        config.fetch_metrics([])


def test_raises_when_aggregation_key_is_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: missing_aggregation
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""
    )

    with pytest.raises(ValueError, match="aggregations"):
        load_view_config(config_path)


def test_raises_when_aggregation_time_is_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: missing_time
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations-patterns:
    - id: hourly
      scenario: false
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""
    )

    with pytest.raises(ValueError, match="time"):
        load_view_config(config_path)


def test_raises_when_aggregation_scenario_is_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: missing_scenario
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations-patterns:
    - id: hourly
      time_granularity: hour
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""
    )

    with pytest.raises(ValueError, match="scenario"):
        load_view_config(config_path)


def test_raises_when_time_and_scenario_pair_is_duplicated(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: duplicate_pattern
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations-patterns:
    - id: hourly
      time_granularity: hour
      scenario: false
    - id: hourly_again
      time_granularity: hour
      scenario: false
  catalogs:
    - id: catalog
  metrics:
    - id: catalog.LOAD
"""
    )

    with pytest.raises(ValueError, match="already defined"):
        load_view_config(config_path)
