# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder import (
    Library,
    ModelPortSchema,
    ModelSchema,
    ParameterSchema,
    VariableSchema,
)
from gems_views_builder.input.library import collect_lib_files, create_lib_from_yml, load_lib_file


def test_collect_lib_files_returns_yml_files_from_directory(test_dataset_dir: Path) -> None:
    collected = collect_lib_files(test_dataset_dir / "libraries")
    assert collected
    assert all(path.is_file() and path.suffix.lower() == ".yml" for path in collected)


def test_collect_lib_files_raises_when_no_yml_files(tmp_path: Path) -> None:
    libraries_dir = tmp_path / "libraries"
    libraries_dir.mkdir()
    with pytest.raises(ValueError, match="No model libraries found"):
        collect_lib_files(libraries_dir)


def test_model_library_loads(test_dataset_dir: Path) -> None:
    collected = collect_lib_files(test_dataset_dir / "libraries")
    assert collected
    for path in collected:
        library = create_lib_from_yml(load_lib_file(path))
        assert isinstance(library, Library)
        assert isinstance(library.id, str)
        assert len(library.models) > 0


def test_model_library_models_are_typed(test_dataset_dir: Path) -> None:
    for path in collect_lib_files(test_dataset_dir / "libraries"):
        library = create_lib_from_yml(load_lib_file(path))
        for model in library.models.values():
            assert isinstance(model, ModelSchema)
            assert isinstance(model.id, str)


# Known model id -> taxonomy category for datasets that include that model.
_KNOWN_TAXONOMY_CATEGORIES: dict[str, str] = {
    "area": "balance",
    "bus": "balance",
    "generator": "production",
    "generator_basic": "production",
    "load": "consumption",
    "store": "storage",
    "link": "link",
    "storage_unit": "storage",
}


def test_model_library_taxonomy_categories(test_dataset_dir: Path) -> None:
    for path in collect_lib_files(test_dataset_dir / "libraries"):
        library = create_lib_from_yml(load_lib_file(path))
        for model_id, expected_category in _KNOWN_TAXONOMY_CATEGORIES.items():
            if model_id not in library.models:
                continue
            assert library.get_model_taxon(model_id) == expected_category


def test_model_library_get_taxonomy_category_unknown_model(test_dataset_dir: Path) -> None:
    library = create_lib_from_yml(load_lib_file(collect_lib_files(test_dataset_dir / "libraries")[0]))
    with pytest.raises(ValueError, match="Model unknown_model not found in library"):
        library.get_model_taxon("unknown_model")


def test_model_library_full_model_loaded(test_dataset_dir: Path) -> None:
    """Full model definition with parameters, variables, ports is loaded."""
    for path in collect_lib_files(test_dataset_dir / "libraries"):
        library = create_lib_from_yml(load_lib_file(path))
        try:
            generator = library.get_model("generator")
        except ValueError:
            pytest.skip("No 'generator' model in this dataset's libraries")
    assert len(generator.parameters) > 0
    assert all(isinstance(p, ParameterSchema) for p in generator.parameters)
    assert len(generator.variables) > 0
    assert all(isinstance(v, VariableSchema) for v in generator.variables)
    assert len(generator.ports) > 0
    assert all(isinstance(p, ModelPortSchema) for p in generator.ports)
    assert len(generator.port_field_definitions) > 0
    assert len(generator.objective_contributions) > 0
    assert len(generator.constraints) > 0


def test_model_library_port_types_loaded(test_dataset_dir: Path) -> None:
    """Port types at library level are loaded."""
    for path in collect_lib_files(test_dataset_dir / "libraries"):
        library = create_lib_from_yml(load_lib_file(path))
        flow_port = next((p for p in library.port_types if p.id == "flow"), None)
        assert flow_port is not None
        assert len(flow_port.fields) > 0
