# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace
from typing import cast

from gems_views_builder import Taxonomy, TaxonomyCategory
from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.validation.input_consistency_validator import (
    InputConsistencyValidator,
    associated_catalogs,
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
                categories=[
                    TaxonomyCategory(id="balance"),
                    TaxonomyCategory(id="consumption"),
                ],
            ),
            view_configs=view_configs,
            libraries=[],
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
    catalogs_by_ids = {catalog.id: catalog, catalog2.id: catalog2, catalog3.id: catalog3}

    # Act
    catalogs_for_one = associated_catalogs(view_config_one, catalogs_by_ids)
    catalogs_for_two = associated_catalogs(view_config_two, catalogs_by_ids)

    # Assert
    assert [item.id for item in catalogs_for_one] == ["catalog"]
    assert [item.id for item in catalogs_for_two] == ["catalog2", "catalog3"]


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
