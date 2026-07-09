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
from pydantic import ValidationError

from gems_views_builder import TimeAggregation, ViewConfig, load_view_config


def test_loads(test_dataset_dir: Path) -> None:
    config_path = test_dataset_dir / "view_config.yml"
    config = load_view_config(config_path)
    assert isinstance(config, ViewConfig)
    assert isinstance(config.id, str)
    assert isinstance(config.location_taxonomy_category, str)
    assert isinstance(config.calendar_id, str)
    assert isinstance(config.taxonomy_id, str)
    assert len(config.catalog_ids) > 0
    assert config.input_data_path == test_dataset_dir


def test_catalog_ids_are_strings(test_dataset_dir: Path) -> None:
    config_path = test_dataset_dir / "view_config.yml"
    config = load_view_config(config_path)
    for catalog_id in config.catalog_ids:
        assert isinstance(catalog_id, str)


def test_metric_ids_are_strings(test_dataset_dir: Path) -> None:
    config_path = test_dataset_dir / "view_config.yml"
    config = load_view_config(config_path)
    for metric_id in config.metric_ids:
        assert isinstance(metric_id, str)
        assert "." in metric_id
        catalog_id, metric_name = metric_id.split(".", 1)
        assert catalog_id in config.catalog_ids
        assert metric_name


def test_known_values(test_dataset_dir: Path) -> None:
    config = load_view_config(test_dataset_dir / "view_config.yml")
    assert config.id == "view_area"
    assert config.location_taxonomy_category == "balance"
    assert config.taxonomy_id == "my_taxonomy"
    assert config.catalog_ids == {"catalog"}
    metric_names = {metric_id.split(".", 1)[1] for metric_id in config.metric_ids}
    assert "LOAD" in metric_names
    if test_dataset_dir.name == "test_3":
        assert "PROD" in metric_names
        assert "BALANCE" in metric_names
    else:
        assert "PRODUCTION" in metric_names
        assert "NUCLEAR_PRODUCTION" in metric_names


def test_time_aggregation(test_dataset_dir: Path) -> None:
    config = load_view_config(test_dataset_dir / "view_config.yml")
    assert config.time_aggregation == TimeAggregation.HOUR


def test_raises_on_invalid_metric_id_format(tmp_path: Path) -> None:
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
  taxonomy:
    - id: my_taxonomy
  metrics:
    - id: invalid_metric_id
""".strip()
    )

    config = load_view_config(invalid_config)

    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        config.fetch_metrics({})


def test_raises_on_missing_taxonomy_section(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: missing_taxonomy
  scope:
    - taxonomy-category: balance
    - calendar: calendar_file
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  metrics:
    - id: catalog.LOAD
""".strip()
    )

    with pytest.raises(ValidationError):
        load_view_config(config_path)


def test_raises_on_empty_taxonomy_list(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: empty_taxonomy
  scope:
    - taxonomy-category: balance
    - calendar: calendar_file
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy: []
  metrics:
    - id: catalog.LOAD
""".strip()
    )

    with pytest.raises(ValueError, match="no taxonomy id configured"):
        load_view_config(config_path)


def test_raises_on_multiple_taxonomy_ids(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """
view:
  id: multiple_taxonomies
  scope:
    - taxonomy-category: balance
    - calendar: calendar_file
  aggregation:
    - time: hour
  catalog:
    - id: catalog
  taxonomy:
    - id: my_taxonomy
    - id: other_taxonomy
  metrics:
    - id: catalog.LOAD
""".strip()
    )

    with pytest.raises(ValueError, match="multiple taxonomy ids"):
        load_view_config(config_path)
