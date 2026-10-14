# Copyright 2007-2026, RTE (https://www.rte-france.com)
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
    catalog = make_catalog(metrics={"PROD": make_metric("PROD", "production", "p_port")})
    target = catalog if attribute == "taxonomy" else next(iter(catalog.metrics.values())).terms[0]
    setattr(target, attribute, value)

    with pytest.raises(ValueError, match=match):
        taxonomy = make_taxonomy(categories={"production": PRODUCTION_CATEGORY})
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()
