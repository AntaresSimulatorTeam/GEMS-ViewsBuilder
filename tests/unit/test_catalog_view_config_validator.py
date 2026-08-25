# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.catalog import (
    AggregOperatorType,
    Catalog,
    Metric,
    Term,
    load_catalog,
    load_catalogs,
)
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.catalogs_view_config_validator import CatalogsViewConfigValidator


def make_catalog(catalog_id: str, metric_ids: list[str]) -> Catalog:
    metrics = {
        metric_id: Metric(
            id=metric_id,
            terms=[Term(taxonomy_category="production", output_id="p", location_port=None)],
            terms_operator=AggregOperatorType.SUM,
            time_operator=AggregOperatorType.SUM,
        )
        for metric_id in metric_ids
    }
    return Catalog(
        id=catalog_id,
        taxonomy="my_taxonomy",
        location_taxonomy_category="balance",
        metrics=metrics,
    )


def test_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    validator = CatalogsViewConfigValidator([catalog], view_config)

    validator.validate()

    assert catalog.taxonomy == view_config.taxonomy_id
    assert catalog.location_taxonomy_category == view_config.location_taxonomy_category


def test_passes_for_loaded_catalogs(test_dataset_dir: Path) -> None:
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalogs = load_catalogs(test_dataset_dir / "catalogs", view_config.catalog_ids)

    CatalogsViewConfigValidator(list(catalogs.values()), view_config).validate()


def test_raises_on_taxonomy_id_mismatch(test_dataset_dir: Path) -> None:
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalog.taxonomy = "wrong_taxonomy"
    validator = CatalogsViewConfigValidator([catalog], view_config)

    with pytest.raises(ValueError, match="references taxonomy"):
        validator.validate()


def test_raises_on_location_category_mismatch(test_dataset_dir: Path) -> None:
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalog.location_taxonomy_category = "wrong_category"
    validator = CatalogsViewConfigValidator([catalog], view_config)

    with pytest.raises(ValueError, match="location taxonomy category"):
        validator.validate()


def test_passes_when_metric_ids_are_unique(test_dataset_dir: Path) -> None:
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.catalog_ids = {"catalog_a", "catalog_b"}
    view_config.metric_ids = ["catalog_a.LOAD", "catalog_a.PROD", "catalog_b.BALANCE", "catalog_b.FLOW"]
    catalogs = [
        make_catalog("catalog_a", ["LOAD", "PROD"]),
        make_catalog("catalog_b", ["BALANCE", "FLOW"]),
    ]
    validator = CatalogsViewConfigValidator(catalogs, view_config)

    validator.validate()

    assert {metric_id for catalog in catalogs for metric_id in catalog.metrics} == {
        "LOAD",
        "PROD",
        "BALANCE",
        "FLOW",
    }


def test_raises_when_metric_missing_from_catalog(test_dataset_dir: Path) -> None:
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.catalog_ids = {"catalog"}
    view_config.metric_ids = ["catalog.MISSING_METRIC"]
    catalogs = [make_catalog("catalog", ["LOAD", "PROD"])]
    validator = CatalogsViewConfigValidator(catalogs, view_config)

    with pytest.raises(ValueError, match=r"metric 'catalog.MISSING_METRIC' is not defined in catalog 'catalog'"):
        validator.validate()
