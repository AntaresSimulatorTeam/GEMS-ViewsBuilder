# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.input.catalog import AggregOperatorType, Catalog, Metric, Term
from gems_views_builder.input.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem
from gems_views_builder.validation.catalogs_taxonomy_validator import CatalogsTaxonomyValidator


def make_taxonomy() -> Taxonomy:
    category = TaxonomyCategory(
        id="production",
        ports=[TaxonomyItem(id="p_port")],
        variables=[TaxonomyItem(id="p")],
    )
    return Taxonomy(id="taxonomy", categories={"production": category})


def make_catalog() -> Catalog:
    return Catalog(
        id="catalog",
        taxonomy="taxonomy",
        location_taxonomy_category="balance",
        metrics={
            "PROD": Metric(
                id="PROD",
                terms=[Term(taxonomy_category="production", output_id="p", location_port="p_port")],
                terms_operator=AggregOperatorType.SUM,
                time_operator=AggregOperatorType.SUM,
            )
        },
    )


def test_passes_for_matching_catalog() -> None:
    CatalogsTaxonomyValidator([make_catalog()], make_taxonomy()).validate()


@pytest.mark.parametrize(
    ("attribute", "value", "match"),
    [
        ("taxonomy", "wrong_taxonomy", "references taxonomy"),
        ("taxonomy_category", "unknown_category", "uses taxonomy-category"),
        ("location_port", "unknown_port", "uses location-port"),
        ("output_id", "unknown_output", "uses output-id"),
    ],
)
def test_rejects_invalid_references(attribute: str, value: str, match: str) -> None:
    catalog = make_catalog()
    target = catalog if attribute == "taxonomy" else next(iter(catalog.metrics.values())).terms[0]
    setattr(target, attribute, value)

    with pytest.raises(ValueError, match=match):
        CatalogsTaxonomyValidator([catalog], make_taxonomy()).validate()
