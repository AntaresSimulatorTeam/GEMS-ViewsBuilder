# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from gems_views_builder import load_view_config
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.validation.aggregation_patterns_validator import AggregationPatternsValidator


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
  metrics:
    - id: catalog.LOAD
"""
    )

    config = load_view_config(config_path)
    raw_input_data = cast(RawInputData, SimpleNamespace(view_config=config))

    with pytest.raises(ValueError, match="already defined"):
        AggregationPatternsValidator(raw_input_data).validate()
