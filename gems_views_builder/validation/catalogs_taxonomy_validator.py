# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
import logging

from gems_craft.model.taxonomy import Taxonomy, TaxonomyCategory  # type: ignore

from gems_views_builder.input.catalog import Catalog, Metric, Term


class CatalogsTaxonomyValidator:
    def __init__(self, catalogs: list[Catalog], taxonomy: Taxonomy):
        self.catalogs = catalogs
        self.taxon_categories = {category.id: category for category in taxonomy.categories}
        self.taxon_id = taxonomy.id

    def validate(self) -> None:
        logging.info(f"Validating {len(self.catalogs)} catalog(s) against taxonomy {self.taxon_id!r}")
        for catalog in self.catalogs:
            self._validate_catalog_against_taxon(catalog)
        logging.info(f"All catalogs are consistent with taxonomy {self.taxon_id!r}")

    def _validate_catalog_against_taxon(self, catalog: Catalog) -> None:
        logging.info(f"Validating catalog {catalog.id!r} against taxonomy {self.taxon_id!r}")
        self._match_catalog_taxonomy(catalog)
        self._validate_catalog_metrics_taxon(catalog)

    def _validate_catalog_metrics_taxon(self, catalog: Catalog) -> None:
        for metric in catalog.metrics.values():
            try:
                self._validate_metric_terms(metric)
            except ValueError as error:
                raise ValueError(f"Catalog {catalog.id!r} metric {metric.id!r}: {error}") from error

    def _match_catalog_taxonomy(self, catalog: Catalog) -> None:
        if catalog.taxonomy != self.taxon_id:
            raise ValueError(
                f"Catalog {catalog.id!r} references taxonomy {catalog.taxonomy!r}, but study taxonomy id is {self.taxon_id!r}"
            )

    def _validate_metric_terms(self, metric: Metric) -> None:
        for term in metric.terms:
            if term.taxonomy_category not in self.taxon_categories:
                raise ValueError(
                    f"uses taxonomy-category {term.taxonomy_category!r}, which is not defined "
                    f"in taxonomy {self.taxon_id!r}"
                )
            self._validate_term_output(term, self.taxon_categories[term.taxonomy_category])
            self._validate_term_location_port(term, self.taxon_categories[term.taxonomy_category])

    def _validate_term_output(self, term: Term, category: TaxonomyCategory) -> None:
        if term.output_id not in allowed_output(category):
            raise ValueError(
                f"uses output-id {term.output_id!r}, which is not declared as a variable, "
                f"extra-output, or port-field-definition on taxonomy category {term.taxonomy_category!r} "
                f"in taxonomy {self.taxon_id!r}"
            )

    def _validate_term_location_port(self, term: Term, category: TaxonomyCategory) -> None:
        category_ports = {port.id for port in category.ports}
        if term.location_port is not None and term.location_port not in category_ports:
            raise ValueError(
                f"uses location-port {term.location_port!r}, which is not defined on "
                f"taxonomy category {term.taxonomy_category!r} in taxonomy {self.taxon_id!r}"
            )


def allowed_output(category: TaxonomyCategory) -> set[str]:
    return (
        {variable.id for variable in category.variables}
        | {extra_output.id for extra_output in category.extra_outputs}
        | {item.id for item in category.port_field_definitions}
    )
