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

from pathlib import Path

import pytest

from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator


def test_view_config_taxonomy_validator_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    validator = ViewConfigTaxonomyValidator(taxonomy, view_config)

    # Act
    validator.validate()

    # Assert
    assert view_config.taxonomy_id == taxonomy.id


def test_view_config_taxonomy_validator_raises_on_id_mismatch(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.taxonomy_id = "wrong_taxonomy"
    validator = ViewConfigTaxonomyValidator(taxonomy, view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="references taxonomy"):
        validator.validate()


def test_view_config_taxonomy_validator_raises_on_unknown_location_category(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.scope_taxon_category = "unknown_category"
    validator = ViewConfigTaxonomyValidator(taxonomy, view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="is not a category of taxonomy"):
        validator.validate()
