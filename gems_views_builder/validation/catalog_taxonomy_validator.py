# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""Validate consistency between loaded catalogs and the study taxonomy."""

import logging

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.taxonomy import Taxonomy


def validate_catalogs_against_taxonomy(catalogs: dict[str, Catalog], taxonomy: Taxonomy) -> None:
    logging.info(f"Validating {len(catalogs)} catalog(s) against taxonomy {taxonomy.id!r}")
    for catalog in catalogs.values():
        validate_catalog_against_taxonomy(catalog, taxonomy)
    logging.info(f"All catalogs are consistent with taxonomy {taxonomy.id!r}")


def _category_ports_by_id(taxonomy: Taxonomy) -> dict[str, set[str]]:
    return {category.id: {port.id for port in category.ports} for category in taxonomy.categories}


def validate_catalog_against_taxonomy(catalog: Catalog, taxonomy: Taxonomy) -> None:
    logging.info(f"Validating catalog {catalog.id!r} against taxonomy {taxonomy.id!r}")
    if catalog.taxonomy != taxonomy.id:
        raise ValueError(
            f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, but study taxonomy id is {taxonomy.id!r}"
        )

    category_ids = {category.id for category in taxonomy.categories}
    category_ports_by_id = _category_ports_by_id(taxonomy)

    for metric in catalog.metrics.values():
        for term in metric.terms:
            if term.taxonomy_category not in category_ids:
                raise ValueError(
                    f"Catalog {catalog.id!r} metric {metric.id!r} uses taxonomy-category "
                    f"{term.taxonomy_category!r}, which is not defined in taxonomy {taxonomy.id!r}"
                )

            if term.location_ports is not None:
                category_ports = category_ports_by_id[term.taxonomy_category]
                if term.location_ports not in category_ports:
                    raise ValueError(
                        f"Catalog {catalog.id!r} metric {metric.id!r} uses location-port "
                        f"{term.location_ports!r}, which is not defined on taxonomy category "
                        f"{term.taxonomy_category!r} in taxonomy {taxonomy.id!r}"
                    )
