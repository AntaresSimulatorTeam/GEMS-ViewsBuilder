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

from gems_views_builder.input.catalog import load_catalog, load_catalogs
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.catalog_view_config_validator import (
    CatalogsViewConfigValidator,
)


def test_catalog_view_config_validator_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    # Arrange
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    validator = CatalogsViewConfigValidator([catalog], view_config)

    # Act
    validator.validate()

    # Assert
    assert catalog.taxonomy == view_config.taxonomy_id
    assert catalog.location_taxonomy_category == view_config.scope_taxon_category


def test_validate_catalogs_against_view_config_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    # Arrange
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalogs = load_catalogs(test_dataset_dir, view_config.catalog_ids)

    # Act / Assert
    CatalogsViewConfigValidator(catalogs, view_config).validate()


def test_catalog_view_config_validator_raises_on_taxonomy_id_mismatch(test_dataset_dir: Path) -> None:
    # Arrange
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalog.taxonomy = "wrong_taxonomy"
    validator = CatalogsViewConfigValidator([catalog], view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="references taxonomy"):
        validator.validate()


def test_catalog_view_config_validator_raises_on_location_category_mismatch(
    test_dataset_dir: Path,
) -> None:
    # Arrange
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalog.location_taxonomy_category = "wrong_category"
    validator = CatalogsViewConfigValidator([catalog], view_config)

    # Act / Assert
    with pytest.raises(ValueError, match="location taxonomy category"):
        validator.validate()
