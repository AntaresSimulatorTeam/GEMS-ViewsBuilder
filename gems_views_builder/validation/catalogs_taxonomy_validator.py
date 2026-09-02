# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging
from dataclasses import dataclass

from gems_views_builder.input.catalog import Catalog, Metric, Term
from gems_views_builder.input.taxonomy import (
    Taxonomy,
    TaxonomyCategory,
    allowed_output_ids,
    group_categories_ports_by_id,
)


@dataclass
class CatalogsTaxonomyValidator:
    catalogs: list[Catalog]
    taxonomy: Taxonomy

    def validate(self) -> None:
        logging.info(f"Validating {len(self.catalogs)} catalog(s) against taxonomy {self.taxonomy.id!r}")
        for catalog in self.catalogs:
            self._validate_catalog_against_taxonomy(catalog)
        logging.info(f"All catalogs are consistent with taxonomy {self.taxonomy.id!r}")

    def _validate_catalog_against_taxonomy(self, catalog: Catalog) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against taxonomy {self.taxonomy.id!r}")

        self._match_catalog_taxonomy_id(catalog)
        category_ports_by_id = group_categories_ports_by_id(self.taxonomy)

        for metric in catalog.metrics.values():
            validate_metric_terms(metric, category_ports_by_id, self.taxonomy, catalog.id)

    def _match_catalog_taxonomy_id(self, catalog: Catalog) -> None:
        if catalog.taxonomy != self.taxonomy.id:
            raise ValueError(
                f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, but study taxonomy id is {self.taxonomy.id!r}"
            )


def validate_metric_terms(
    metric: Metric,
    category_ports_by_id: dict[str, set[str]],
    taxonomy: Taxonomy,
    catalog_id: str,
) -> None:
    for term in metric.terms:
        category = taxonomy.categories.get(term.taxonomy_category)
        if category is None:
            raise ValueError(
                f"Catalog {catalog_id!r} metric {metric.id!r} uses taxonomy-category "
                f"{term.taxonomy_category!r}, which is not defined in taxonomy {taxonomy.id!r}"
            )
        validate_term_output_id(catalog_id, metric.id, term, category, taxonomy.id)
        validate_term_location_port(catalog_id, metric.id, term, category_ports_by_id, taxonomy.id)


def validate_term_output_id(
    catalog_id: str, metric_id: str, term: Term, category: TaxonomyCategory, taxonomy_id: str
) -> None:
    if term.output_id in allowed_output_ids(category):
        return
    raise ValueError(
        f"Catalog {catalog_id!r} metric {metric_id!r} uses output-id {term.output_id!r}, "
        f"which is not declared as a variable or extra-output on taxonomy category "
        f"{term.taxonomy_category!r} in taxonomy {taxonomy_id!r}"
    )


def validate_term_location_port(
    catalog_id: str, metric_id: str, term: Term, category_ports_by_id: dict[str, set[str]], taxonomy_id: str
) -> None:
    if term.location_port is not None:
        if term.location_port not in category_ports_by_id[term.taxonomy_category]:
            raise ValueError(
                f"Catalog {catalog_id!r} metric {metric_id!r} uses location-port "
                f"{term.location_port!r}, which is not defined on taxonomy category "
                f"{term.taxonomy_category!r} in taxonomy {taxonomy_id!r}"
            )
