# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.validation.view_config_metrics_against_catalogs_validator import (
    ViewConfigMetricsAgainstCatalogsValidator,
)
from tests.common import make_catalog, make_view_config


def test_passes_when_metric_ids_are_unique() -> None:
    view_config = make_view_config(
        full_metric_ids=[
            "catalog_a.LOAD",
            "catalog_a.PROD",
            "catalog_b.BALANCE",
            "catalog_b.FLOW",
            "catalog_b.EXPORT",
        ],
    )
    catalogs = [
        make_catalog("catalog_a", metric_ids=["LOAD", "PROD"]),
        make_catalog("catalog_b", metric_ids=["BALANCE", "FLOW", "EXPORT"]),
    ]

    ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()


def test_raises_when_metric_ids_are_not_unique_across_catalogs() -> None:
    view_config = make_view_config(full_metric_ids=["catalog_a.LOAD", "catalog_b.LOAD"])
    catalogs = [make_catalog("catalog_a", metric_ids=["LOAD"]), make_catalog("catalog_b", metric_ids=["LOAD"])]

    with pytest.raises(ValueError, match="metric ids are not unique"):
        ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()


def test_raises_when_metric_missing_from_catalog() -> None:
    view_config = make_view_config(full_metric_ids=["catalog.MISSING_METRIC"])
    catalogs = [make_catalog("catalog", metric_ids=["LOAD", "PROD"])]

    with pytest.raises(ValueError, match="MISSING_METRIC.*doesn't exist in catalog 'catalog'"):
        ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()


@pytest.mark.parametrize(
    "full_metric_id",
    [
        "catalog.INVALID.METRIC",
        "catalog..INVALID_METRIC",
        "catalog.INVALID_METRIC.",
        ".catalogINVALID_METRIC",
    ],
)
def test_raises_when_metric_ref_format_is_invalid(full_metric_id: str) -> None:
    view_config = make_view_config(full_metric_ids=[full_metric_id])
    catalogs = [make_catalog("catalog", metric_ids=["LOAD", "PROD"])]

    with pytest.raises(ValueError, match=r"Expected format '<catalog_id>\.<metric_id>'"):
        ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()
