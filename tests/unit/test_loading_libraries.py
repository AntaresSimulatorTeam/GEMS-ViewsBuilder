# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.library import collect_lib_files, create_lib_from_yml, load_yml_libs

LIBRARY_YAML = """\
library:
  id: library_one
  port-types:
    - id: flow
      description: A port which transfers power flow
      fields:
        - id: flow
  models:
    - id: generator
      taxonomy-category: production
      parameters:
        - id: p_max
        - id: cost
      variables:
        - id: generation
          lower-bound: 0
          upper-bound: p_max
      ports:
        - id: balance_port
          type: flow
      port-field-definitions:
        - port: balance_port
          field: flow
          definition: generation
      constraints:
        - id: generation_bound
          expression: generation <= p_max
      objective-contributions:
        - id: operational_objective
          expression: expec(sum(cost * generation))
"""


def test_collect_lib_files_raises_when_no_yml_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No model libraries found"):
        collect_lib_files(tmp_path)


def test_collect_libraries(tmp_path: Path) -> None:
    (tmp_path / "library_one.yml").write_text(LIBRARY_YAML)
    (tmp_path / "library_two.yml").write_text(LIBRARY_YAML.replace("id: library_one", "id: library_two"))
    lib_files = collect_lib_files(tmp_path)
    assert len(lib_files) == 2
    assert {path.name for path in lib_files} == {"library_one.yml", "library_two.yml"}


def test_load_multiple_libs(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "library_one.yml").write_text(LIBRARY_YAML)
    (tmp_path / "library_two.yml").write_text(LIBRARY_YAML.replace("id: library_one", "id: library_two"))

    # Act
    yml_libs = load_yml_libs(tmp_path)
    libs = [create_lib_from_yml(yml_lib) for yml_lib in yml_libs]

    # Assert
    assert len(libs) == 2
    assert {lib.id for lib in libs} == {"library_one", "library_two"}


def test_library_fully_loaded(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "test.yml").write_text(LIBRARY_YAML)

    # Act
    yml_lib = load_yml_libs(tmp_path)[0]
    lib = create_lib_from_yml(yml_lib)

    # Assert
    assert lib.id == yml_lib.id
    assert lib.port_types == yml_lib.port_types
    assert lib.models["generator"] == yml_lib.models[0]
    assert lib.models_by_taxonomy_category == {"production": ["generator"]}
    assert lib.taxon_by_model == {"generator": "production"}
