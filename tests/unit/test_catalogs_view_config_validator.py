# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.catalog import load_catalog, load_catalogs
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.catalogs_view_config_validator import ViewConfigCatalogsValidator


def test_passes_for_loaded_catalogs(test_dataset_dir: Path) -> None:
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalogs = load_catalogs(test_dataset_dir / "catalogs", view_config.catalog_ids)

    # Act & Assert
    ViewConfigCatalogsValidator(catalogs, view_config).validate()


def test_raises_on_taxonomy_id_mismatch(test_dataset_dir: Path) -> None:
    # Arrange
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalog.taxonomy = "wrong_taxonomy"

    # Act & Assert
    with pytest.raises(ValueError, match="references taxonomy"):
        ViewConfigCatalogsValidator([catalog], view_config).validate()


def test_raises_on_location_category_mismatch(test_dataset_dir: Path) -> None:
    # Arrange
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalog.location_taxonomy_category = "wrong_category"

    # Act & Assert
    with pytest.raises(ValueError, match="location taxonomy category"):
        ViewConfigCatalogsValidator([catalog], view_config).validate()
