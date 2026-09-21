# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from gems_views_builder import load_view_config
from gems_views_builder.validation.aggregation_patterns_validator import ViewConfigsAggregationPatternsValidator
from gems_views_builder.validation.view_config import validate_unique_ids

VIEW_CONFIG: dict[str, Any] = {
    "id": "view",
    "taxonomy": "my_taxonomy",
    "scope": {
        "location": {"taxonomy-category": "balance"},
        "calendar": "calendar_file",
    },
    "aggregations-patterns": [
        {"id": "hourly", "time_granularity": "hour", "scenario": False},
    ],
    "catalogs": [{"id": "catalog"}],
    "metrics": [{"id": "catalog.LOAD"}],
}


def make_view_config() -> dict[str, Any]:
    return deepcopy(VIEW_CONFIG)


def write_view_config(tmp_path: Path, view: dict[str, Any]) -> Path:
    path = tmp_path / "view_config.yml"
    path.write_text(yaml.dump({"view": view}))
    return path


def test_raises_on_invalid_metric_id_format(tmp_path: Path) -> None:
    view = make_view_config()
    view["metrics"] = [{"id": "invalid_metric_id"}]
    config = load_view_config(write_view_config(tmp_path, view))

    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        config.populate_with_metrics([])


def test_raises_when_aggregation_key_is_missing(tmp_path: Path) -> None:
    view = make_view_config()
    view.pop("aggregations-patterns")

    with pytest.raises(ValueError, match="aggregations"):
        load_view_config(write_view_config(tmp_path, view))


def test_raises_when_aggregation_time_is_missing(tmp_path: Path) -> None:
    view = make_view_config()
    view["aggregations-patterns"][0].pop("time_granularity")

    with pytest.raises(ValueError, match="time"):
        load_view_config(write_view_config(tmp_path, view))


def test_raises_when_aggregation_scenario_is_missing(tmp_path: Path) -> None:
    view = make_view_config()
    view["aggregations-patterns"][0].pop("scenario")

    with pytest.raises(ValueError, match="scenario"):
        load_view_config(write_view_config(tmp_path, view))


def test_view_config_raises_when_ids_are_not_unique(tmp_path: Path) -> None:
    # Arrange
    view_config = load_view_config(write_view_config(tmp_path, make_view_config()))

    # Act + Assert
    with pytest.raises(ValueError, match="multiple times"):
        validate_unique_ids([view_config, view_config])


def test_view_config_aggregation_patterns_validator(tmp_path: Path) -> None:
    # Arrange
    view_config = load_view_config(write_view_config(tmp_path, make_view_config()))

    # Act + Assert
    ViewConfigsAggregationPatternsValidator([view_config]).validate()


def test_view_config_aggregation_patterns_validator_raises_when_patterns_are_not_unique(tmp_path: Path) -> None:
    # Arrange
    view = make_view_config()
    view["aggregations-patterns"] = view["aggregations-patterns"] * 2
    view_config = load_view_config(write_view_config(tmp_path, view))

    # Act + Assert
    with pytest.raises(ValueError, match="already defined"):
        ViewConfigsAggregationPatternsValidator([view_config]).validate()
