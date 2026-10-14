# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import pytest

from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator
from tests.common import make_taxonomy, make_view_config


def test_passes_when_view_config_matches_taxonomy() -> None:
    ViewConfigTaxonomyValidator(make_taxonomy(), make_view_config()).validate()


def test_raises_on_id_mismatch() -> None:
    view_config = make_view_config()
    view_config.taxonomy_id = "wrong_taxonomy"

    with pytest.raises(ValueError, match="references taxonomy"):
        ViewConfigTaxonomyValidator(make_taxonomy(), view_config).validate()


def test_raises_on_unknown_location_category() -> None:
    view_config = make_view_config()
    view_config.location_taxonomy_category = "unknown_category"

    with pytest.raises(ValueError, match="is not a category of taxonomy"):
        ViewConfigTaxonomyValidator(make_taxonomy(), view_config).validate()
