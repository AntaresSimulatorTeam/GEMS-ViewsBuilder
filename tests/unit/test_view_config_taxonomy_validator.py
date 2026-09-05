# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.view_config_taxonomy import ViewConfigTaxonomyValidator


def test_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")

    # Act & Assert
    ViewConfigTaxonomyValidator(taxonomy, view_config).validate()


def test_raises_on_id_mismatch(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.taxonomy_id = "wrong_taxonomy"

    # Act & Assert
    with pytest.raises(ValueError, match="references taxonomy"):
        ViewConfigTaxonomyValidator(taxonomy, view_config).validate()


def test_raises_on_unknown_location_category(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    view_config.location_taxonomy_category = "unknown_category"

    # Act & Assert
    with pytest.raises(ValueError, match="is not a category of taxonomy"):
        ViewConfigTaxonomyValidator(taxonomy, view_config).validate()
