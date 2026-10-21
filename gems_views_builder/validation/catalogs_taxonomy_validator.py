# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging
from dataclasses import dataclass

from gems_craft.model.taxonomy import Taxonomy, TaxonomyCategory  # type: ignore

from gems_views_builder.input.catalog import Catalog, Metric, Term


def _allowed_output(category: TaxonomyCategory) -> set[str]:
    return (
        {variable.id for variable in category.variables}
        | {extra_output.id for extra_output in category.extra_outputs}
        | {item.id for item in category.port_field_definitions}
    )


def match_taxonomy_category(taxonomy: Taxonomy, category_id: str) -> TaxonomyCategory | None:
    for category in taxonomy.categories:
        if category.id == category_id:
            return category
    return None


@dataclass
class CatalogsTaxonomyValidator:
    catalogs: list[Catalog]
    taxonomy: Taxonomy

    def validate(self) -> None:
        logging.info(f"Validating {len(self.catalogs)} catalog(s) against taxonomy {self.taxonomy.id!r}")
        for catalog in self.catalogs:
            self._validate_catalog_against_taxon(catalog)
        logging.info(f"All catalogs are consistent with taxonomy {self.taxonomy.id!r}")

    def _validate_catalog_against_taxon(self, catalog: Catalog) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against taxonomy {self.taxonomy.id!r}")
        self._match_catalog_taxonomy(catalog)
        self._validate_catalog_metrics_taxon(catalog)

    def _validate_catalog_metrics_taxon(self, catalog: Catalog) -> None:
        for metric in catalog.metrics.values():
            try:
                self._validate_metric_terms(metric)
            except ValueError as error:
                raise ValueError(f"Catalog {catalog.id!r} metric {metric.id!r}: {error}") from error

    def _match_catalog_taxonomy(self, catalog: Catalog) -> None:
        if catalog.taxonomy != self.taxonomy.id:
            raise ValueError(
                f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, but study taxonomy id is {self.taxonomy.id!r}"
            )

    def _validate_metric_terms(self, metric: Metric) -> None:
        for term in metric.terms:
            category = match_taxonomy_category(self.taxonomy, term.taxonomy_category)
            if category is None:
                raise ValueError(
                    f"uses taxonomy-category {term.taxonomy_category!r}, which is not defined "
                    f"in taxonomy {self.taxonomy.id!r}"
                )
            self._validate_term_output(term, category)
            self._validate_term_location_port(term, category)

    def _validate_term_output(self, term: Term, category: TaxonomyCategory) -> None:
        if term.output_id in _allowed_output(category):
            return
        raise ValueError(
            f"uses output-id {term.output_id!r}, which is not declared as a variable, "
            f"extra-output, or port-field-definition on taxonomy category {term.taxonomy_category!r} "
            f"in taxonomy {self.taxonomy.id!r}"
        )

    def _validate_term_location_port(self, term: Term, category: TaxonomyCategory) -> None:
        if term.location_port is not None:
            if term.location_port not in {port.id for port in category.ports}:
                raise ValueError(
                    f"uses location-port {term.location_port!r}, which is not defined on "
                    f"taxonomy category {term.taxonomy_category!r} in taxonomy {self.taxonomy.id!r}"
                )
