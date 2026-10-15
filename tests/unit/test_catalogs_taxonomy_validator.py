# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.input.taxonomy import TaxonomyCategory, TaxonomyItem
from gems_views_builder.validation.catalogs_taxonomy_validator import CatalogsTaxonomyValidator
from tests.common import make_catalog, make_metric, make_taxonomy

PRODUCTION_CATEGORY = TaxonomyCategory(
    id="production",
    ports=[TaxonomyItem(id="p_port")],
    variables=[TaxonomyItem(id="p")],
)


def test_passes_for_matching_catalog() -> None:
    taxonomy = make_taxonomy(categories={"production": PRODUCTION_CATEGORY})
    catalog = make_catalog(metrics={"PROD": make_metric("PROD", "production", "p_port")})
    CatalogsTaxonomyValidator([catalog], taxonomy).validate()


def test_raises_on_taxonomy_id_mismatch() -> None:
    catalog = make_catalog(taxonomy="wrong_taxonomy", metrics={"PROD": make_metric("PROD", "production", "p_port")})
    taxonomy = make_taxonomy(categories={"production": PRODUCTION_CATEGORY})

    with pytest.raises(ValueError, match="references taxonomy"):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()


@pytest.mark.parametrize(
    ("taxonomy_category", "location_port", "output_id", "match"),
    [
        ("unknown_category", "p_port", "p", "uses taxonomy-category"),
        ("production", "unknown_port", "p", "uses location-port"),
        ("production", "p_port", "unknown_output", "uses output-id"),
    ],
)
def test_rejects_invalid_term_references(
    taxonomy_category: str, location_port: str, output_id: str, match: str
) -> None:
    catalog = make_catalog(metrics={"PROD": make_metric("PROD", taxonomy_category, location_port, output_id)})
    taxonomy = make_taxonomy(categories={"production": PRODUCTION_CATEGORY})

    with pytest.raises(ValueError, match=match):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()
