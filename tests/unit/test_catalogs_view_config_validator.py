# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.validation.catalogs_view_config_validator import ViewConfigCatalogsValidator
from tests.common import make_catalog, make_view_config


def test_passes_when_catalog_matches_view_config() -> None:
    ViewConfigCatalogsValidator([make_catalog()], make_view_config(catalog_ids={"catalog"})).validate()


def test_raises_on_taxonomy_id_mismatch() -> None:
    catalog = make_catalog()
    catalog.taxonomy = "wrong_taxonomy"

    with pytest.raises(ValueError, match="references taxonomy"):
        ViewConfigCatalogsValidator([catalog], make_view_config(catalog_ids={"catalog"})).validate()


def test_raises_on_location_category_mismatch() -> None:
    catalog = make_catalog()
    catalog.location_taxonomy_category = "wrong_category"

    with pytest.raises(ValueError, match="location taxonomy category"):
        ViewConfigCatalogsValidator([catalog], make_view_config(catalog_ids={"catalog"})).validate()
