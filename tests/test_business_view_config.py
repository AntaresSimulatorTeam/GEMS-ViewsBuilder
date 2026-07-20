# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest
from pydantic import ValidationError

from gems_views_builder import TimeAggregation, ViewConfig, load_view_config


def test_loads(test_dataset_dir: Path) -> None:
    config = load_view_config(test_dataset_dir / "view_config.yml")
    assert isinstance(config, ViewConfig)
    assert isinstance(config.id, str)
    assert isinstance(config.location_taxonomy_category, str)
    assert isinstance(config.calendar_id, str)
    assert isinstance(config.taxonomy_id, str)
    assert config.catalog_ids
    assert config.input_data_path == test_dataset_dir


def test_catalog_and_metric_ids_are_strings(test_dataset_dir: Path) -> None:
    config = load_view_config(test_dataset_dir / "view_config.yml")
    assert all(isinstance(catalog_id, str) for catalog_id in config.catalog_ids)
    for metric_id in config.metric_ids:
        assert isinstance(metric_id, str)
        catalog_id, metric_name = metric_id.split(".", 1)
        assert catalog_id in config.catalog_ids
        assert metric_name


def test_known_values(test_dataset_dir: Path) -> None:
    config = load_view_config(test_dataset_dir / "view_config.yml")
    assert config.id == "view_area"
    assert config.location_taxonomy_category == "balance"
    assert config.taxonomy_id == "my_taxonomy"
    assert config.catalog_ids == {"catalog"}


def test_time_aggregation(test_dataset_dir: Path) -> None:
    assert load_view_config(test_dataset_dir / "view_config.yml").time_aggregation == TimeAggregation.HOUR


def test_raises_on_invalid_metric_id_format(tmp_path: Path) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        """view:
  id: invalid_metric_format
  scope:
    - location:
        taxonomy-category: balance
    - calendar:
        id: calendar_file
  aggregation:
    - time: hour
  catalog:
    - id: catalog_1
  taxonomy:
    - id: my_taxonomy
  metrics:
    - id: invalid_metric_id"""
    )
    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        load_view_config(config_path).fetch_metrics([])


@pytest.mark.parametrize(
    "taxonomy_section",
    ["", "  taxonomy: []", "  taxonomy:\n    - id: my_taxonomy\n    - id: other_taxonomy"],
)
def test_raises_on_invalid_taxonomy_section(tmp_path: Path, taxonomy_section: str) -> None:
    config_path = tmp_path / "view_config.yml"
    config_path.write_text(
        f"""view:
  id: invalid_taxonomy
  scope:
    - location:
        taxonomy-category: balance
    - calendar:
        id: calendar_file
  aggregation:
    - time: hour
  catalog:
    - id: catalog
{taxonomy_section}
  metrics:
    - id: catalog.LOAD"""
    )
    with pytest.raises(ValidationError):
        load_view_config(config_path)
