# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from io import StringIO
from pathlib import Path

import pytest
from gems_craft.model.parsing import parse_yaml_library  # type: ignore

from gems_views_builder import load_taxonomy
from gems_views_builder.input.library import load_lib_file
from gems_views_builder.validation.library_taxonomy_validator import validate_libraries_against_taxonomy


def test_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    libraries = [load_lib_file(path) for path in (test_dataset_dir / "libraries").glob("*.yml")]

    # Act & Assert
    validate_libraries_against_taxonomy(libraries, taxonomy)


def test_raises_gemspy_message_when_model_misses_a_required_item(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    library = parse_yaml_library(
        StringIO(
            """
library:
  id: lib
  description: incomplete
  models:
    - id: area
      taxonomy-category: balance
"""
        )
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Model 'area'"):
        validate_libraries_against_taxonomy([library], taxonomy)
