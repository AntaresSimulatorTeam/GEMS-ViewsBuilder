# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.library import collect_lib_files, create_lib_from_yml, load_yml_libs
from gems_craft.model.parsing import ModelSchema

LIBRARY_YAML_1 = """\
library:
  id: library_1
  models:
    - id: generator
      taxonomy-category: production
"""

LIBRARY_YAML_2 = """\
library:
  id: library_2
  models:
    - id: generator
      taxonomy-category: production
"""

def test_collect_lib_files_raises_when_no_yml_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No model libraries found"):
        collect_lib_files(tmp_path)


def test_collect_libraries(tmp_path: Path) -> None:
    (tmp_path / "library_1.yml").write_text(LIBRARY_YAML_1)
    (tmp_path / "library_2.yml").write_text(LIBRARY_YAML_2)
    lib_files = collect_lib_files(tmp_path)
    assert len(lib_files) == 2
    assert {path.name for path in lib_files} == {"library_1.yml", "library_2.yml"}


def test_load_multiple_libs(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "library_1.yml").write_text(LIBRARY_YAML_1)
    (tmp_path / "library_2.yml").write_text(LIBRARY_YAML_2)

    # Act
    yml_libs = load_yml_libs(tmp_path)
    libs = [create_lib_from_yml(yml_lib) for yml_lib in yml_libs]

    # Assert
    assert len(libs) == 2
    assert {lib.id for lib in libs} == {"library_1", "library_2"}


def test_library_fully_loaded(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "test.yml").write_text(LIBRARY_YAML_1)

    # Act
    yml_lib = load_yml_libs(tmp_path)[0]
    lib = create_lib_from_yml(yml_lib)

    # Assert
    assert lib.id == "library_1"
    assert lib.port_types == []
    assert lib.models["generator"] == ModelSchema(id="generator", taxonomy_category="production")
    assert lib.models_by_taxonomy_category == {"production": ["generator"]}
    assert lib.taxon_by_model == {"generator": "production"}
