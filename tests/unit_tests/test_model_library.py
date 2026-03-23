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

TEST_FILES_ROOT = Path(__file__).resolve().parent.parent.parent / "resources" / "test_files"

LIBRARY_PATHS = [
    TEST_FILES_ROOT / "test_3" / "pypsa_models.yml",
]


@pytest.mark.parametrize("library_path", LIBRARY_PATHS)
def test_model_library_loads(library_path: Path) -> None:
    library = ModelLibrary(library_path)
    assert isinstance(library.id, str)
    assert len(library.models) > 0


@pytest.mark.parametrize("library_path", LIBRARY_PATHS)
def test_model_library_models_are_typed(library_path: Path) -> None:
    library = ModelLibrary(library_path)
    for model in library.models.values():
        assert isinstance(model, ModelDefinition)
        assert isinstance(model.id, str)


def test_model_library_taxonomy_categories() -> None:
    library = ModelLibrary(TEST_FILES_ROOT / "test_3" / "pypsa_models.yml")
    assert library.get_taxonomy_category("bus") == "balance"
    assert library.get_taxonomy_category("load") == "consumption"
    assert library.get_taxonomy_category("link") == "link"
    assert library.get_taxonomy_category("storage_unit") == "storage"
    assert library.get_taxonomy_category("store") == "consumption"


def test_model_library_get_taxonomy_category_unknown_model() -> None:
    library = ModelLibrary(TEST_FILES_ROOT / "test_3" / "pypsa_models.yml")
    assert library.get_taxonomy_category("unknown_model") is None


def test_model_library_full_model_loaded() -> None:
    """Full model definition with parameters, variables, ports is loaded."""
    library = ModelLibrary(TEST_FILES_ROOT / "test_3" / "pypsa_models.yml")
    generator = library.get_model("generator")
    assert generator is not None
    assert len(generator.parameters) > 0
    assert all(isinstance(p, ParameterDef) for p in generator.parameters)
    assert len(generator.variables) > 0
    assert all(isinstance(v, VariableDef) for v in generator.variables)
    assert len(generator.ports) > 0
    assert all(isinstance(p, PortDef) for p in generator.ports)
    assert len(generator.port_field_definitions) > 0
    assert len(generator.constraints) > 0
    assert len(generator.objective_contributions) > 0


def test_model_library_port_types_loaded() -> None:
    """Port types at library level are loaded."""
    library = ModelLibrary(TEST_FILES_ROOT / "test_3" / "pypsa_models.yml")
    assert len(library.port_types) > 0
    flow_port = next((p for p in library.port_types if p.id == "flow"), None)
    assert flow_port is not None
    assert len(flow_port.fields) > 0
