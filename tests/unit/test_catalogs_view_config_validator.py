# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.input.catalog import Catalog
from gems_views_builder.input.view_config import AggregationPattern, TimeGranularity, ViewConfig
from gems_views_builder.validation.catalogs_view_config_validator import ViewConfigCatalogsValidator


def make_catalog() -> Catalog:
    return Catalog(
        id="catalog",
        taxonomy="taxonomy",
        location_taxonomy_category="balance",
    )


def make_view_config() -> ViewConfig:
    return ViewConfig(
        id="view",
        calendar_id="calendar",
        location_taxonomy_category="balance",
        taxonomy_id="taxonomy",
        aggregation_patterns=(AggregationPattern(id="hourly", time_granularity=TimeGranularity.HOUR, scenario=False),),
        catalog_ids={"catalog"},
    )


def test_passes_when_catalog_matches_view_config() -> None:
    ViewConfigCatalogsValidator([make_catalog()], make_view_config()).validate()


def test_raises_on_taxonomy_id_mismatch() -> None:
    catalog = make_catalog()
    catalog.taxonomy = "wrong_taxonomy"

    with pytest.raises(ValueError, match="references taxonomy"):
        ViewConfigCatalogsValidator([catalog], make_view_config()).validate()


def test_raises_on_location_category_mismatch() -> None:
    catalog = make_catalog()
    catalog.location_taxonomy_category = "wrong_category"

    with pytest.raises(ValueError, match="location taxonomy category"):
        ViewConfigCatalogsValidator([catalog], make_view_config()).validate()
