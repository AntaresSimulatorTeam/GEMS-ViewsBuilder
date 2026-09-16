# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest
from gems_craft.model.parsing import FieldSchema, write_yaml_library  # type: ignore

from gems_views_builder import (
    ConstraintSchema,
    LibrarySchema,
    ModelPortSchema,
    ModelSchema,
    ObjectiveContributionSchema,
    ParameterSchema,
    PortFieldDefinitionSchema,
    PortTypeSchema,
    VariableSchema,
)
from gems_views_builder.input.library import collect_lib_files, create_lib_from_yml, load_lib_file


def make_generator_model() -> ModelSchema:
    return ModelSchema(
        id="generator",
        taxonomy_category="production",
        parameters=[ParameterSchema(id="p_max"), ParameterSchema(id="cost")],
        variables=[VariableSchema(id="generation", lower_bound="0", upper_bound="p_max")],
        ports=[ModelPortSchema(id="balance_port", type="flow")],
        port_field_definitions=[PortFieldDefinitionSchema(port="balance_port", field="flow", definition="generation")],
        constraints=[ConstraintSchema(id="generation_bound", expression="generation <= p_max")],
        objective_contributions=[
            ObjectiveContributionSchema(id="operational_objective", expression="expec(sum(cost * generation))")
        ],
    )


def make_flow_port_type_schema() -> PortTypeSchema:
    return PortTypeSchema(id="flow", description="A port which transfers power flow", fields=[FieldSchema(id="flow")])


def make_library_schema() -> LibrarySchema:
    return LibrarySchema(
        id="test",
        dependencies=[],
        port_types=[make_flow_port_type_schema()],
        models=[make_generator_model()],
    )


def test_collect_lib_files_raises_when_no_yml_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No model libraries found"):
        collect_lib_files(tmp_path)


def test_collect_and_load_multiple_libs(tmp_path: Path) -> None:
    # Arrange
    lib_schema = make_library_schema()
    write_yaml_library(lib_schema, tmp_path / "library_one.yml")
    lib_schema2 = make_library_schema()
    write_yaml_library(lib_schema2, tmp_path / "library_two.yml")

    # Act
    collected = collect_lib_files(tmp_path)
    gvb_libraries = [create_lib_from_yml(load_lib_file(lib_file)) for lib_file in collected]

    # Assert
    assert len(gvb_libraries) == 2


def test_gvb_library_fully_loaded(tmp_path: Path) -> None:
    """
    Note:
    GVB Library and Gemspy Library are not the same.
    GVB Library is created from LibrarySchema
    """
    # Arrange
    lib_schema = make_library_schema()
    write_yaml_library(lib_schema, tmp_path / "test.yml")

    # Act
    collected = collect_lib_files(tmp_path)
    gvb_library = create_lib_from_yml(load_lib_file(collected[0]))

    # Assert
    assert gvb_library.id == lib_schema.id
    assert gvb_library.port_types == lib_schema.port_types
    assert gvb_library.models["generator"] == lib_schema.models[0]
    assert gvb_library.models_by_taxonomy_category == {"production": ["generator"]}
    assert gvb_library.taxon_by_model == {"generator": "production"}
