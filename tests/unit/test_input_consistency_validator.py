# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace
from typing import cast

import pytest

from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.validation.input_consistency_validator import (
    InputConsistencyValidator,
    group_catalogs_by_view_configs,
)


def make_catalog(catalog_id: str, location_category: str, metric_ids: list[str]) -> Catalog:
    return Catalog(
        id=catalog_id,
        taxonomy="my_taxonomy",
        location_taxonomy_category=location_category,
        metrics={
            metric_id: Metric(
                id=metric_id,
                terms=[],
                terms_operator=AggregOperatorType.SUM,
                time_operator=AggregOperatorType.SUM,
            )
            for metric_id in metric_ids
        },
    )


def make_view_config(view_config_id: str, location_category: str, full_metric_ids: list[str]) -> ViewConfig:
    return ViewConfig(
        id=view_config_id,
        calendar_id="calendar_file",
        location_taxonomy_category=location_category,
        taxonomy_id="my_taxonomy",
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
        full_metric_ids=full_metric_ids,
    )


def make_raw_input_data(view_configs: list[ViewConfig], catalogs: list[Catalog]) -> RawInputData:
    return cast(
        RawInputData,
        SimpleNamespace(
            taxonomy=Taxonomy(
                id="my_taxonomy",
                categories={
                    "balance": TaxonomyCategory(id="balance"),
                    "consumption": TaxonomyCategory(id="consumption"),
                },
            ),
            view_configs=view_configs,
            catalogs=catalogs,
        ),
    )


def test_groups_each_catalog_once_under_the_view_config_that_references_it() -> None:
    # Arrange
    view_config_one = make_view_config("view_config_one", "balance", ["catalog.LOAD", "catalog.PROD"])
    view_config_two = make_view_config(
        "view_config_two", "consumption", ["catalog2.CONSUMPTION", "catalog3.AVG_CONSUMPTION"]
    )
    catalog = make_catalog("catalog", "balance", ["LOAD", "PROD"])
    catalog2 = make_catalog("catalog2", "consumption", ["CONSUMPTION"])
    catalog3 = make_catalog("catalog3", "avg_consumption", ["AVG_CONSUMPTION"])
    raw_input_data = make_raw_input_data([view_config_one, view_config_two], [catalog, catalog2, catalog3])

    # Act
    grouped = group_catalogs_by_view_configs(
        raw_input_data, {catalog.id: catalog, catalog2.id: catalog2, catalog3.id: catalog3}
    )


    # Assert
    assert [item.id for item in grouped["view_config_one"]] == ["catalog"]
    assert [item.id for item in grouped["view_config_two"]] == ["catalog2", "catalog3"]


def test_validates_view_configs_with_different_location_categories() -> None:
    # Arrange
    view_config_one = make_view_config("view_config_one", "balance", ["catalog.LOAD"])
    view_config_two = make_view_config("view_config_two", "consumption", ["catalog2.CONSUMPTION"])
    catalogs = [
        make_catalog("catalog", "balance", ["LOAD"]),
        make_catalog("catalog2", "consumption", ["CONSUMPTION"]),
    ]
    validator = InputConsistencyValidator(make_raw_input_data([view_config_one, view_config_two], catalogs))

    # Act
    validator.validate()

    # Assert
    assert len(validator.raw_input_data.view_configs) == 2
    assert validator.raw_input_data.view_configs[0].id == "view_config_one"
    assert validator.raw_input_data.view_configs[1].id == "view_config_two"


def test_raises_when_a_view_config_references_an_unknown_catalog() -> None:
    # Arrange
    view_config_one = make_view_config("view_config_one", "balance", ["missing.LOAD"])
    raw_input_data = make_raw_input_data([view_config_one], [])

    # Act
    with pytest.raises(ValueError) as error:
        group_catalogs_by_view_configs(raw_input_data, {})

    # Assert
    assert str(error.value) == "Catalog 'missing' not found in input data but used in view config 'view_config_one'"


def test_raises_when_a_view_config_references_a_catalog_that_is_not_defined() -> None:
    # Arrange
    view_config_one = make_view_config("view_config_one", "balance", ["catalog.LOAD"])
    view_config_two = make_view_config("view_config_two", "consumption", ["catalog2.CONSUMPTION"])
    raw_input_data = make_raw_input_data(
        [view_config_one, view_config_two], [make_catalog("catalog", "balance", ["LOAD"])]
    )

    # Act
    with pytest.raises(ValueError) as error:
        InputConsistencyValidator(raw_input_data).validate()

    # Assert
    assert str(error.value) == "Catalog 'catalog2' not found in input data but used in view config 'view_config_two'"
