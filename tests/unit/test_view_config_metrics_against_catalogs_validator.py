# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.validation.view_config_metrics_against_catalogs_validator import (
    ViewConfigMetricsAgainstCatalogsValidator,
)
from tests.common import make_catalog, make_view_config


def test_passes_when_metric_ids_are_unique() -> None:
    view_config = make_view_config(
        catalog_ids={"catalog_a", "catalog_b"},
        metric_ids=[
            "catalog_a.LOAD",
            "catalog_a.PROD",
            "catalog_b.BALANCE",
            "catalog_b.FLOW",
            "catalog_b.PROD",
        ],
    )
    catalogs = [
        make_catalog("catalog_a", metric_ids=["LOAD", "PROD"]),
        make_catalog("catalog_b", metric_ids=["BALANCE", "FLOW", "PROD"]),
    ]

    ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()


def test_raises_when_metric_missing_from_catalog() -> None:
    view_config = make_view_config(catalog_ids={"catalog"}, metric_ids=["catalog.MISSING_METRIC"])
    catalogs = [make_catalog("catalog", metric_ids=["LOAD", "PROD"])]

    with pytest.raises(ValueError, match="MISSING_METRIC.*doesn't exist in catalog 'catalog'"):
        ViewConfigMetricsAgainstCatalogsValidator(catalogs, view_config).validate()
