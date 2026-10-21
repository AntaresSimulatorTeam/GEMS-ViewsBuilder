# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from gems_views_builder import load_view_config
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.validation.view_config import (
    validate_unique_ids,
    validate_view_configs_aggregation_patterns,
    validate_view_configs_full_metric_ids,
)

VIEW_CONFIG_YAML = """
id: view
taxonomy: my_taxonomy
scope:
  location:
    taxonomy-category: balance
  calendar: calendar_file
aggregations-patterns:
  - id: hourly
    time_granularity: hour
    scenario: false
metrics:
  - id: catalog.LOAD
"""


def make_view_config() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(VIEW_CONFIG_YAML))


def write_view_config(tmp_path: Path, view: dict[str, Any]) -> Path:
    path = tmp_path / "view_config.yml"
    path.write_text(yaml.dump({"view": view}))
    return path


@pytest.mark.parametrize(
    "full_metric_id",
    [
        "invalid_metric_id",
        "catalog.INVALID.METRIC",
        "catalog..INVALID_METRIC",
        "catalog.INVALID_METRIC.",
        ".catalogINVALID_METRIC",
    ],
)
def test_raises_on_invalid_metric_id_format(tmp_path: Path, full_metric_id: str) -> None:
    # Arrange
    view = make_view_config()
    view["metrics"] = [{"id": full_metric_id}]
    config = load_view_config(write_view_config(tmp_path, view))

    # Act
    with pytest.raises(ValueError) as error:
        validate_view_configs_full_metric_ids([config])

    # Assert
    assert (
        str(error.value)
        == f"Invalid metric id reference '{full_metric_id}'. Expected format '<catalog_id>.<metric_id>'"
    )


def test_raises_when_aggregation_key_is_missing(tmp_path: Path) -> None:
    # Arrange
    view = make_view_config()
    view.pop("aggregations-patterns")

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(write_view_config(tmp_path, view))

    # Assert
    assert "aggregations-patterns" in str(error.value)
    assert "Field required" in str(error.value)


def test_raises_when_aggregation_time_is_missing(tmp_path: Path) -> None:
    # Arrange
    view = make_view_config()
    view["aggregations-patterns"][0].pop("time_granularity")

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(write_view_config(tmp_path, view))

    # Assert
    assert "time-granularity" in str(error.value)
    assert "Field required" in str(error.value)


def test_raises_when_aggregation_scenario_is_missing(tmp_path: Path) -> None:
    # Arrange
    view = make_view_config()
    view["aggregations-patterns"][0].pop("scenario")

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(write_view_config(tmp_path, view))

    # Assert
    assert "scenario" in str(error.value)
    assert "Field required" in str(error.value)


def test_view_config_raises_when_ids_are_not_unique(tmp_path: Path) -> None:
    # Arrange
    view_config = load_view_config(write_view_config(tmp_path, make_view_config()))

    # Act
    with pytest.raises(ValueError) as error:
        validate_unique_ids([view_config, view_config])

    # Assert
    assert str(error.value) == "View config 'view' is defined multiple times"


def test_view_config_aggregation_patterns_validator(tmp_path: Path) -> None:
    # Arrange
    view_config = load_view_config(write_view_config(tmp_path, make_view_config()))

    # Act + Assert
    validate_view_configs_aggregation_patterns([view_config])


def make_catalog(catalog_id: str, metric_ids: list[str]) -> Catalog:
    return Catalog(
        id=catalog_id,
        taxonomy="my_taxonomy",
        location_taxonomy_category="balance",
        metrics={
            metric_id: Metric(
                id=metric_id,
                terms=[Term(taxonomy_category="production", output_id="p", location_port=None)],
                terms_operator=AggregOperatorType.SUM,
                time_operator=AggregOperatorType.SUM,
            )
            for metric_id in metric_ids
        },
    )


def test_populate_with_metrics_raises_when_catalog_is_missing(tmp_path: Path) -> None:
    # Arrange
    view_config = load_view_config(write_view_config(tmp_path, make_view_config()))

    # Act
    with pytest.raises(ValueError) as error:
        view_config.populate_with_metrics([make_catalog("catalogX", ["LOAD"])])

    # Assert
    assert str(error.value) == "Catalog 'catalog' used in view config 'view' doesn't exist!"


def test_populate_with_metrics_raises_when_metric_is_missing(tmp_path: Path) -> None:
    # Arrange
    view_config = load_view_config(write_view_config(tmp_path, make_view_config()))

    # Act
    with pytest.raises(ValueError) as error:
        view_config.populate_with_metrics([make_catalog("catalog", ["PROD"])])

    # Assert
    assert str(error.value) == "Metric 'LOAD' used in view config 'view' doesn't exist in catalog 'catalog'"


def test_view_config_aggregation_patterns_validator_raises_when_patterns_are_not_unique(tmp_path: Path) -> None:
    # Arrange
    view = make_view_config()
    view["aggregations-patterns"] = view["aggregations-patterns"] * 2
    view_config = load_view_config(write_view_config(tmp_path, view))

    # Act
    with pytest.raises(ValueError) as error:
        validate_view_configs_aggregation_patterns([view_config])

    # Assert
    assert str(error.value) == "Pattern (TimeGranularity.HOUR, False) is already defined"
