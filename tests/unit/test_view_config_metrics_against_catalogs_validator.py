# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
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


def make_view_config(catalog_ids: set[str], metric_ids: list[str]) -> ViewConfig:
    return ViewConfig(
        id="view",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        taxonomy_id="my_taxonomy",
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
        catalog_ids=catalog_ids,
        metric_ids=metric_ids,
    )


def test_passes_when_metric_ids_are_unique() -> None:
    view_config = make_view_config(
        {"catalog_a", "catalog_b"},
        [
            "catalog_a.LOAD",
            "catalog_a.PROD",
            "catalog_b.BALANCE",
            "catalog_b.FLOW",
            "catalog_b.PROD",
        ],
    )
    catalogs = [
        make_catalog("catalog_a", ["LOAD", "PROD"]),
        make_catalog("catalog_b", ["BALANCE", "FLOW", "PROD"]),
    ]

    ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()


def test_raises_when_metric_missing_from_catalog() -> None:
    view_config = make_view_config({"catalog"}, ["catalog.MISSING_METRIC"])
    catalogs = [make_catalog("catalog", ["LOAD", "PROD"])]

    with pytest.raises(ValueError, match="MISSING_METRIC.*doesn't exist in catalog 'catalog'"):
        ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()
