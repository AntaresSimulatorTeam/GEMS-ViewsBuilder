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
from dataclasses import dataclass

from gems_views_builder.input.catalog import Catalog, Term
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem


@dataclass
class CatalogsTaxonomyValidator:
    catalogs: list[Catalog]
    taxonomy: Taxonomy

    def validate(self) -> None:
        logging.info(f"Validating {len(self.catalogs)} catalog(s) against taxonomy {self.taxonomy.id!r}")
        for catalog in self.catalogs:
            self._validate_catalog_against_taxonomy(catalog)
        logging.info(f"All catalogs are consistent with taxonomy {self.taxonomy.id!r}")

    def _match_catalog_taxonomy_id(self, catalog: Catalog) -> None:
        if catalog.taxonomy != self.taxonomy.id:
            raise ValueError(
                f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, but study taxonomy id is {self.taxonomy.id!r}"
            )

    @staticmethod
    def _item_ids(items: list[TaxonomyItem]) -> set[str]:
        return {item.id for item in items}

    def _allowed_output_ids(self, category: TaxonomyCategory) -> set[str]:
        # | logical or(union) so resulting set is unique.
        return self._item_ids(category.variables) | self._item_ids(category.extra_outputs)

    def _validate_term_output_id(
        self, catalog: Catalog, metric_id: str, term: Term, category: TaxonomyCategory
    ) -> None:
        allowed = self._allowed_output_ids(category)
        if term.output_id in allowed:
            return
        raise ValueError(
            f"Catalog {catalog.id!r} metric {metric_id!r} uses output-id {term.output_id!r}, "
            f"which is not declared as a variable or extra-output on taxonomy category "
            f"{term.taxonomy_category!r} in taxonomy {self.taxonomy.id!r}"
        )

    def _validate_catalog_against_taxonomy(self, catalog: Catalog) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against taxonomy {self.taxonomy.id!r}")
        self._match_catalog_taxonomy_id(catalog)

        categories = self.taxonomy.get_taxonomy_categories()

        category_ports_by_id = {
            category.id: {port.id for port in category.ports} for category in self.taxonomy.categories
        }

        for metric in catalog.metrics.values():
            for term in metric.terms:
                category = categories.get(term.taxonomy_category)
                if category is None:
                    raise ValueError(
                        f"Catalog {catalog.id!r} metric {metric.id!r} uses taxonomy-category "
                        f"{term.taxonomy_category!r}, which is not defined in taxonomy {self.taxonomy.id!r}"
                    )

                self._validate_term_output_id(catalog, metric.id, term, category)

                if term.location_port is not None:
                    category_ports = category_ports_by_id[term.taxonomy_category]
                    if term.location_port not in category_ports:
                        raise ValueError(
                            f"Catalog {catalog.id!r} metric {metric.id!r} uses location-port "
                            f"{term.location_port!r}, which is not defined on taxonomy category "
                            f"{term.taxonomy_category!r} in taxonomy {self.taxonomy.id!r}"
                        )
