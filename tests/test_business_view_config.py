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


def test_view_config_loads(test_dataset_dir: Path) -> None:
    config_path = test_dataset_dir / "view_config.yml"
    config = ViewConfig.load(config_path)
    assert isinstance(config.id, str)
    assert isinstance(config.location_taxonomy_category, str)
    assert isinstance(config.calendar_id, str)
    assert len(config.catalog_ids) > 0


def test_view_config_catalog_ids_are_strings(test_dataset_dir: Path) -> None:
    config_path = test_dataset_dir / "view_config.yml"
    config = ViewConfig.load(config_path)
    for catalog_id in config.catalog_ids:
        assert isinstance(catalog_id, str)


def test_view_config_metrics_are_pairs(test_dataset_dir: Path) -> None:
    config_path = test_dataset_dir / "view_config.yml"
    config = ViewConfig.load(config_path)
    for catalog_id, metrics in config.catalog_to_metrics.items():
        assert isinstance(catalog_id, str)
        assert isinstance(metrics, list)
        assert all(isinstance(metric, str) for metric in metrics)


def test_view_config_known_values(test_dataset_dir: Path) -> None:
    config = ViewConfig.load(test_dataset_dir / "view_config.yml")
    assert config.id == "view_area"
    assert config.location_taxonomy_category == "balance"
    assert config.catalog_ids == ["catalog"]
    metrics = config.catalog_to_metrics["catalog"]
    assert "LOAD" in metrics
    if test_dataset_dir.name == "test_3":
        assert "PROD" in metrics
        assert "BALANCE" in metrics
    else:
        assert "PRODUCTION" in metrics
        assert "NUCLEAR_PRODUCTION" in metrics


def test_view_config_time_aggregation(test_dataset_dir: Path) -> None:
    config = ViewConfig.load(test_dataset_dir / "view_config.yml")
    assert config.time_aggregation == TimeAggregation.HOUR


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
    - time: hour
  catalog:
    - id: catalog_1
  metrics:
    - id: invalid_metric_id
""".strip()
    )

    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        ViewConfig.load(invalid_config)
