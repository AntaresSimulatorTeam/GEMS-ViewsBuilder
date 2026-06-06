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
from gems.model.parsing import ModelPortSchema, ParameterSchema, VariableSchema  # type: ignore[import-untyped]

from gems_views_builder import (
    ModelLibrary,
)


def _library_path(test_dataset_dir: Path) -> Path | None:
    generic = Path(test_dataset_dir) / "library.yml"
    if generic.is_file():
        return generic
    pytest.skip("No model library file found (expected library.yml)")


def test_model_library_loads(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary.load(library_path)
    assert isinstance(library.id, str)
    assert len(library.models) > 0


def test_model_library_models_are_typed(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary.load(library_path)
    for model in library.models.values():
        # GemsPy parsing schema
        assert hasattr(model, "id")
        assert isinstance(model.id, str)


def _production_model_id(library: ModelLibrary) -> str:
    for model_id in ("generator", "generator_basic"):
        if model_id in library.models:
            return model_id
    raise AssertionError("Expected a production model ('generator' or 'generator_basic') in the library")


def test_model_library_taxonomy_categories(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary.load(library_path)
    assert library.get_taxonomy_category("load") == "consumption"
    if "store" in library.models:
        assert library.get_taxonomy_category("store") == "consumption"
    else:
        production_model = _production_model_id(library)
        assert library.get_taxonomy_category(production_model) == "production"


def test_model_library_get_taxonomy_category_unknown_model(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary.load(library_path)
    assert library.get_taxonomy_category("unknown_model") is None


def test_model_library_full_model_loaded(test_dataset_dir: Path) -> None:
    """Full model definition with parameters, variables, ports is loaded."""
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary.load(library_path)
    production_model = _production_model_id(library)
    generator = library.get_model(production_model)
    assert generator is not None
    assert len(generator.parameters) > 0
    assert all(isinstance(p, ParameterSchema) for p in generator.parameters)
    assert len(generator.variables) > 0
    assert all(isinstance(v, VariableSchema) for v in generator.variables)
    assert len(generator.ports) > 0
    assert all(isinstance(p, ModelPortSchema) for p in generator.ports)
    assert len(generator.port_field_definitions) > 0
    assert len(generator.objective_contributions) > 0
    if production_model == "generator":
        assert len(generator.constraints) > 0


def test_model_library_port_types_loaded(test_dataset_dir: Path) -> None:
    """Port types at library level are loaded."""
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary.load(library_path)
    assert len(library.port_types) > 0
    flow_port = next((p for p in library.port_types if p.id == "flow"), None)
    assert flow_port is not None
    assert len(flow_port.fields) > 0
