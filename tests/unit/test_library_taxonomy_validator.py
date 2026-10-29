# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from io import StringIO
from pathlib import Path

import pytest
from gems_craft.model.parsing import parse_yaml_library  # type: ignore

from gems_views_builder import load_taxonomy
from gems_views_builder.input.library import create_lib_from_yml, load_lib_file
from gems_views_builder.validation.validate_library_taxonomy import validate_libraries_against_taxonomy

# Category "balance" requires one port. The library model declares that category and exposes none.
TAXONOMY_MISSING_PORT = """\
taxonomy:
  id: my_taxonomy
  categories:
    - id: balance
      ports:
        - id: p_balance_port
"""

LIBRARY_MISSING_PORT = """\
library:
  id: lib
  models:
    - id: area
      taxonomy-category: balance
"""


def test__load_all_datasets__validating_libraries_taxonomy__no_issue(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    yml_libs = [load_lib_file(path) for path in (test_dataset_dir / "libraries").glob("*.yml")]
    libraries = [create_lib_from_yml(yml_lib) for yml_lib in yml_libs]

    # Act & Assert
    validate_libraries_against_taxonomy(libraries, taxonomy)


def test__library_model_misses_required_port__validating_libraries_taxonomy__raises(tmp_path: Path) -> None:
    # Arrange
    taxonomy_path = tmp_path / "taxonomy.yml"
    taxonomy_path.write_text(TAXONOMY_MISSING_PORT)
    taxonomy = load_taxonomy(taxonomy_path)
    library = parse_yaml_library(StringIO(LIBRARY_MISSING_PORT))

    # Act
    with pytest.raises(ValueError) as error:
        validate_libraries_against_taxonomy([create_lib_from_yml(library)], taxonomy)

    # Assert
    assert str(error.value) == (
        "Model 'area' (taxonomy-category: 'balance') is missing port(s) required by the taxonomy: ['p_balance_port']."
    )
