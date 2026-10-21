# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from gems_views_builder.input.catalog import Catalog


def validate_catalog_ids(catalogs: list[Catalog]) -> None:
    catalog_ids = set()
    for catalog in catalogs:
        if catalog.id in catalog_ids:
            raise ValueError(f"Catalog {catalog.id!r} is defined multiple times")
        catalog_ids.add(catalog.id)
