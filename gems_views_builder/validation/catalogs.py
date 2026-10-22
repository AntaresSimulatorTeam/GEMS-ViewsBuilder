# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.catalog import Catalog


def validate_catalogs(catalogs: list[Catalog]) -> None:
    validate_catalogs_are_unique(catalogs)
    for catalog in catalogs:
        validate_catalogs_metrics(catalog)

def validate_catalogs_are_unique(catalogs: list[Catalog]) -> None:
    catalog_ids = set()
    for catalog in catalogs:
        if catalog.id in catalog_ids:
            raise ValueError(f"Catalog {catalog.id!r} is defined multiple times")
        catalog_ids.add(catalog.id)

def validate_catalogs_metrics(catalog: Catalog) -> None:
    unique_metric_ids = set()
    for metric_id in catalog.metrics.keys():
        if metric_id in unique_metric_ids:
            raise ValueError(f"Metric {metric_id!r} is defined multiple times in catalog {catalog.id!r}")
        unique_metric_ids.add(metric_id)
