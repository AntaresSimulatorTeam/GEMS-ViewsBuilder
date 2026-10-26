# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from gems_views_builder import load_view_config
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.validation.view_config import (
    validate_aggregation_pattern_content_uniqueness,
    validate_unique_aggregation_pattern_ids,
    validate_unique_ids,
    validate_view_configs_aggregation_patterns,
)
from gems_views_builder.validation.view_config_metrics_against_catalogs_validator import (
    ViewConfigMetricsAgainstCatalogsValidator,
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


def write_view_config(tmp_path: Path, view: dict[str, Any]) -> Path:
    path = tmp_path / "view_config.yml"
    path.write_text(yaml.dump({"view": view}))
    return path


@pytest.fixture
def view_config_yaml() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(VIEW_CONFIG_YAML))


@pytest.fixture
def view_config(tmp_path: Path, view_config_yaml: dict[str, Any]) -> ViewConfig:
    path_to_yml = write_view_config(tmp_path, view_config_yaml)
    return load_view_config(path_to_yml)


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
def test_raises_on_invalid_metric_id_format(
    full_metric_id: str, view_config_yaml: dict[str, Any], tmp_path: Path
) -> None:
    view_config_yaml["metrics"] = [{"id": full_metric_id}]

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(write_view_config(tmp_path, view_config_yaml))

    # Assert
    assert full_metric_id in str(error.value)
    assert "String should match pattern" in str(error.value)


def test_raises_when_aggregation_key_is_missing(tmp_path: Path, view_config_yaml: dict[str, Any]) -> None:
    # Arrange
    view_config_yaml.pop("aggregations-patterns")
    path_to_yml = write_view_config(tmp_path, view_config_yaml)

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(path_to_yml)

    # Assert
    assert "aggregations-patterns" in str(error.value)
    assert "Field required" in str(error.value)


def test_raises_when_aggregation_time_is_missing(tmp_path: Path, view_config_yaml: dict[str, Any]) -> None:
    # Arrange
    view_config_yaml["aggregations-patterns"][0].pop("time_granularity")
    path_to_yml = write_view_config(tmp_path, view_config_yaml)

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(path_to_yml)

    # Assert
    assert "time-granularity" in str(error.value)
    assert "Field required" in str(error.value)


def test_raises_when_aggregation_scenario_is_missing(tmp_path: Path, view_config_yaml: dict[str, Any]) -> None:
    # Arrange
    view_config_yaml["aggregations-patterns"][0].pop("scenario")
    path_to_yml = write_view_config(tmp_path, view_config_yaml)

    # Act
    with pytest.raises(ValueError) as error:
        load_view_config(path_to_yml)

    # Assert
    assert "scenario" in str(error.value)
    assert "Field required" in str(error.value)


def test_view_config_raises_when_ids_are_not_unique(view_config: ViewConfig) -> None:
    # Act
    with pytest.raises(ValueError) as error:
        validate_unique_ids([view_config, view_config])

    # Assert
    assert str(error.value) == "View config 'view' is defined multiple times"


def test_view_config_aggregation_patterns_validator(view_config: ViewConfig) -> None:
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


def test_metrics_validator_raises_when_catalog_is_missing(view_config: ViewConfig) -> None:
    # Act
    with pytest.raises(ValueError) as error:
        ViewConfigMetricsAgainstCatalogsValidator([make_catalog("catalogX", ["LOAD"])], view_config).validate()

    # Assert
    assert str(error.value) == "Catalog 'catalog' used in view config 'view' doesn't exist!"


def test_metrics_validator_raises_when_metric_is_missing(view_config: ViewConfig) -> None:
    # Act
    with pytest.raises(ValueError) as error:
        ViewConfigMetricsAgainstCatalogsValidator([make_catalog("catalog", ["PROD"])], view_config).validate()

    # Assert
    assert str(error.value) == "Metric 'LOAD' used in view config 'view' doesn't exist in catalog 'catalog'"


def test_view_config_aggregation_patterns_validator_raises_when_pattern_ids_are_not_unique(
    view_config: ViewConfig,
) -> None:
    view_config.aggregation_patterns = view_config.aggregation_patterns * 2

    # Act
    with pytest.raises(ValueError) as error:
        validate_unique_aggregation_pattern_ids(view_config.aggregation_patterns)

    # Assert
    assert str(error.value) == "Aggregation pattern 'hourly' is defined multiple times"


def test_view_config_aggregation_patterns_validator_raises_when_time_and_scenario_match(
    tmp_path: Path, view_config_yaml: dict[str, Any]
) -> None:
    # Arrange
    duplicate = dict(view_config_yaml["aggregations-patterns"][0])
    duplicate["id"] = "hourly_again"
    view_config_yaml["aggregations-patterns"].append(duplicate)
    view_config = load_view_config(write_view_config(tmp_path, view_config_yaml))

    # Act
    with pytest.raises(ValueError) as error:
        validate_aggregation_pattern_content_uniqueness(view_config.aggregation_patterns)

    # Assert
    assert str(error.value) == "Pattern (TimeGranularity.HOUR, False) is already defined"
