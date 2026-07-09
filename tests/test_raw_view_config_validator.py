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

import pytest

from gems_views_builder.input.view_config import load_raw_view_config_file
from gems_views_builder.validation.raw_view_config_validator import RawViewConfigValidator


def _write_view_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(body.strip())
    return config_path


def test_raw_view_config_validator_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    # Arrange
    raw_view_config = load_raw_view_config_file(test_dataset_dir / "view_config.yml")
    validator = RawViewConfigValidator(raw_view_config)

    # Act
    validator.validate()

    # Assert
    locations = [item.location for item in raw_view_config.scope if item.location is not None]
    calendars = [item.calendar for item in raw_view_config.scope if item.calendar is not None]
    assert len(locations) == 1
    assert len(calendars) == 1
    assert locations[0].taxonomy_category == "balance"
    assert calendars[0].id == "calendar_file"


def test_raw_view_config_validator_raises_when_location_missing(tmp_path: Path) -> None:
    # Arrange
    config_path = _write_view_config(
        tmp_path,
        """
view:
  id: missing_location
  scope:
    - calendar:
        id: calendar_file
    - calendar:
        id: other_calendar
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy:
    - id: my_taxonomy
  metrics:
    - id: catalog.LOAD
""",
    )
    raw_view_config = load_raw_view_config_file(config_path)
    validator = RawViewConfigValidator(raw_view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="exactly one location"):
        validator.validate()


def test_raw_view_config_validator_raises_when_calendar_missing(tmp_path: Path) -> None:
    # Arrange
    config_path = _write_view_config(
        tmp_path,
        """
view:
  id: missing_calendar
  scope:
    - location:
        taxonomy-category: balance
    - {}
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy:
    - id: my_taxonomy
  metrics:
    - id: catalog.LOAD
""",
    )
    raw_view_config = load_raw_view_config_file(config_path)
    validator = RawViewConfigValidator(raw_view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="exactly one calendar"):
        validator.validate()


def test_raw_view_config_validator_raises_when_multiple_locations(tmp_path: Path) -> None:
    # Arrange
    config_path = _write_view_config(
        tmp_path,
        """
view:
  id: multiple_locations
  scope:
    - location:
        taxonomy-category: balance
    - location:
        taxonomy-category: production
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy:
    - id: my_taxonomy
  metrics:
    - id: catalog.LOAD
""",
    )
    raw_view_config = load_raw_view_config_file(config_path)
    validator = RawViewConfigValidator(raw_view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="exactly one location"):
        validator.validate()


def test_raw_view_config_validator_raises_when_multiple_calendars(tmp_path: Path) -> None:
    # Arrange
    config_path = _write_view_config(
        tmp_path,
        """
view:
  id: multiple_calendars
  scope:
    - location:
        taxonomy-category: balance
      calendar:
        id: calendar_file
    - calendar:
        id: other_calendar
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy:
    - id: my_taxonomy
  metrics:
    - id: catalog.LOAD
""",
    )
    raw_view_config = load_raw_view_config_file(config_path)
    validator = RawViewConfigValidator(raw_view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="exactly one calendar"):
        validator.validate()
