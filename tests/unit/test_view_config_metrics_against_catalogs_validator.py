# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.view_config_metrics_against_catalogs_validator import (
    ViewConfigMetricsAgainstCatalogsValidator,
)


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


def test_passes_when_metric_ids_are_unique(test_dataset_dir: Path) -> None:
    # Arrange
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.catalog_ids = {"catalog_a", "catalog_b"}
    view_config.metric_ids = [
        "catalog_a.LOAD",
        "catalog_a.PROD",
        "catalog_b.BALANCE",
        "catalog_b.FLOW",
        "catalog_b.PROD",
    ]
    catalogs = [
        make_catalog("catalog_a", ["LOAD", "PROD"]),
        make_catalog("catalog_b", ["BALANCE", "FLOW", "PROD"]),
    ]

    # Act & Assert
    ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()


def test_raises_when_metric_missing_from_catalog(test_dataset_dir: Path) -> None:
    # Arrange
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.catalog_ids = {"catalog"}
    view_config.metric_ids = ["catalog.MISSING_METRIC"]
    catalogs = [make_catalog("catalog", ["LOAD", "PROD"])]

    # Act & Assert
    with pytest.raises(ValueError, match="MISSING_METRIC.*doesn't exist in catalog 'catalog'"):
        ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()
