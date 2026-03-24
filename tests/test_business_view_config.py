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

from gems_views_builder import TimeAggregation, ViewConfig
from tests.conftest import TEST_FILES_ROOT

CONFIG_PATHS = [
    TEST_FILES_ROOT / "test_3" / "view_config.yml",
]


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_view_config_loads(config_path: Path) -> None:
    config = ViewConfig(config_path)
    assert isinstance(config.id, str)
    assert isinstance(config.location_taxonomy_category, str)
    assert isinstance(config.calendar_id, str)
    assert len(config.catalog_ids) > 0


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_view_config_catalog_ids_are_strings(config_path: Path) -> None:
    config = ViewConfig(config_path)
    for catalog_id in config.catalog_ids:
        assert isinstance(catalog_id, str)


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_view_config_metrics_are_pairs(config_path: Path) -> None:
    config = ViewConfig(config_path)
    for catalog_id, metrics in config.catalog_to_metrics.items():
        assert isinstance(catalog_id, str)
        assert isinstance(metrics, list)
        assert all(isinstance(metric, str) for metric in metrics)


def test_view_config_known_values() -> None:
    config = ViewConfig(TEST_FILES_ROOT / "test_3" / "view_config.yml")
    assert config.id == "view_area"
    assert config.location_taxonomy_category == "balance"
    assert config.catalog_ids == ["catalog"]
    assert "PROD" in config.catalog_to_metrics["catalog"]
    assert "LOAD" in config.catalog_to_metrics["catalog"]
    assert "BALANCE" in config.catalog_to_metrics["catalog"]


def test_view_config_time_aggregation() -> None:
    config = ViewConfig(TEST_FILES_ROOT / "test_3" / "view_config.yml")
    assert config.time_aggregation == TimeAggregation.HOURS


def test_view_config_raises_on_invalid_metric_id_format(tmp_path: Path) -> None:
    invalid_config = tmp_path / "view_config.yml"
    invalid_config.write_text(
        """
view:
  id: invalid_metric_format
  scope:
    - taxonomy-category: balance
    - calendar: calendar_file
  aggregation:
    - time: hours
  catalog:
    - id: catalog_1
  metrics:
    - id: invalid_metric_id
""".strip()
    )

    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        ViewConfig(invalid_config)
