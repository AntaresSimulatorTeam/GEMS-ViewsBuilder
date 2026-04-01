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

from gems_views_builder import (
    ModelDefinition,
    ModelLibrary,
    ParameterDef,
    PortDef,
    VariableDef,
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
    library = ModelLibrary(library_path)
    assert isinstance(library.id, str)
    assert len(library.models) > 0


def test_model_library_models_are_typed(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary(library_path)
    for model in library.models.values():
        assert isinstance(model, ModelDefinition)
        assert isinstance(model.id, str)


def test_model_library_taxonomy_categories(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary(library_path)
    assert library.get_taxonomy_category("bus") == "balance"
    assert library.get_taxonomy_category("load") == "consumption"
    assert library.get_taxonomy_category("link") == "link"
    assert library.get_taxonomy_category("storage_unit") == "storage"
    assert library.get_taxonomy_category("store") == "consumption"


def test_model_library_get_taxonomy_category_unknown_model(test_dataset_dir: Path) -> None:
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary(library_path)
    assert library.get_taxonomy_category("unknown_model") is None


def test_model_library_full_model_loaded(test_dataset_dir: Path) -> None:
    """Full model definition with parameters, variables, ports is loaded."""
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary(library_path)
    generator = library.get_model("generator")
    if generator is None:
        pytest.skip("No 'generator' model in this dataset's library")
    assert len(generator.parameters) > 0
    assert all(isinstance(p, ParameterDef) for p in generator.parameters)
    assert len(generator.variables) > 0
    assert all(isinstance(v, VariableDef) for v in generator.variables)
    assert len(generator.ports) > 0
    assert all(isinstance(p, PortDef) for p in generator.ports)
    assert len(generator.port_field_definitions) > 0
    assert len(generator.constraints) > 0
    assert len(generator.objective_contributions) > 0


def test_model_library_port_types_loaded(test_dataset_dir: Path) -> None:
    """Port types at library level are loaded."""
    library_path = _library_path(test_dataset_dir)
    if library_path is None:
        pytest.skip("No model library file found (expected library.yml)")
    library = ModelLibrary(library_path)
    assert len(library.port_types) > 0
    flow_port = next((p for p in library.port_types if p.id == "flow"), None)
    assert flow_port is not None
    assert len(flow_port.fields) > 0
