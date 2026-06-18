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

from gems_views_builder.input.catalog import Catalog, Term
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem


def validate_catalogs_against_taxonomy(catalogs: dict[str, Catalog], taxonomy: Taxonomy) -> None:
    logging.info(f"Validating {len(catalogs)} catalog(s) against taxonomy {taxonomy.id!r}")
    for catalog in catalogs.values():
        validate_catalog_against_taxonomy(catalog, taxonomy)
    logging.info(f"All catalogs are consistent with taxonomy {taxonomy.id!r}")


def _category_by_id(taxonomy: Taxonomy) -> dict[str, TaxonomyCategory]:
    return {category.id: category for category in taxonomy.categories}


def _item_ids(items: list[TaxonomyItem]) -> set[str]:
    return {item.id for item in items}


def _allowed_output_ids(category: TaxonomyCategory) -> set[str]:
    # | logical or(union) so resulting set is unique.
    return _item_ids(category.variables) | _item_ids(category.extra_outputs) | _item_ids(category.port_fields)


def _location_port_names(location_ports: str | tuple[str, ...] | None) -> list[str]:
    if location_ports is None:
        return []
    if isinstance(location_ports, str):
        return [location_ports]
    return list(location_ports)


def _validate_term_output_id(catalog_id: str, metric_id: str, term: Term, category: TaxonomyCategory) -> None:
    allowed = _allowed_output_ids(category)
    if term.output_id in allowed:
        return
    raise ValueError(
        f"Catalog {catalog_id!r} metric {metric_id!r} uses output-id {term.output_id!r}, "
        f"which is not declared as a variable, extra-output, or port-field on taxonomy category "
        f"{term.taxonomy_category!r}"
    )


def _validate_term_location_ports(catalog_id: str, metric_id: str, term: Term, category: TaxonomyCategory) -> None:
    category_ports = _item_ids(category.ports)
    for port in _location_port_names(term.location_ports):
        if port not in category_ports:
            raise ValueError(
                f"Catalog {catalog_id!r} metric {metric_id!r} uses location-port "
                f"{port!r}, which is not defined on taxonomy category "
                f"{term.taxonomy_category!r}"
            )


def validate_catalog_against_taxonomy(catalog: Catalog, taxonomy: Taxonomy) -> None:
    logging.info(f"Validating catalog {catalog.id!r} against taxonomy {taxonomy.id!r}")
    if catalog.taxonomy != taxonomy.id:
        raise ValueError(
            f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, but study taxonomy id is {taxonomy.id!r}"
        )

    categories_by_id = _category_by_id(taxonomy)

    for metric in catalog.metrics.values():
        for term in metric.terms:
            category = categories_by_id.get(term.taxonomy_category)
            if category is None:
                raise ValueError(
                    f"Catalog {catalog.id!r} metric {metric.id!r} uses taxonomy-category "
                    f"{term.taxonomy_category!r}, which is not defined in taxonomy {taxonomy.id!r}"
                )

            _validate_term_output_id(catalog.id, metric.id, term, category)

            if term.location_ports is not None:
                _validate_term_location_ports(catalog.id, metric.id, term, category)
