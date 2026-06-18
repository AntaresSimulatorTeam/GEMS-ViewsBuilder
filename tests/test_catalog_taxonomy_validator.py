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

from gems_views_builder.input.catalog import Catalog, load_catalog, load_catalogs
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.loader import Loader
from gems_views_builder.validation.catalog_taxonomy_validator import (
    validate_catalog_against_taxonomy,
    validate_catalogs_against_taxonomy,
)


def test_validate_catalog_against_taxonomy_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalogs_against_taxonomy_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    from gems_views_builder.input.view_config import load_view_config

    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalogs = load_catalogs(test_dataset_dir, view_config.catalog_ids)
    validate_catalogs_against_taxonomy(catalogs, taxonomy)


def test_validate_catalog_against_taxonomy_raises_on_taxonomy_id_mismatch(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    catalog.taxonomy = "wrong_taxonomy"
    with pytest.raises(ValueError, match="references taxonomy"):
        validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalog_against_taxonomy_raises_on_unknown_metric_category(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    next(iter(catalog.metrics.values())).terms[0].taxonomy_category = "unknown_category"
    with pytest.raises(ValueError, match="uses taxonomy-category"):
        validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalog_against_taxonomy_raises_on_unknown_location_port(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    next(iter(catalog.metrics.values())).terms[0].location_ports = "unknown_port"
    with pytest.raises(ValueError, match="uses location-port"):
        validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalog_against_taxonomy_raises_on_unknown_output_id(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    next(iter(catalog.metrics.values())).terms[0].output_id = "unknown_output"

    # Act & Assert
    with pytest.raises(ValueError, match="uses output-id"):
        validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalog_term_passes_when_output_id_matches_taxonomy_category(test_dataset_dir: Path) -> None:
    # Arrange
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    prod_term = catalog.metrics["PROD"].terms[0]
    link_term = catalog.metrics["BALANCE"].terms[0]
    assert prod_term.taxonomy_category == "production"
    assert prod_term.output_id == "p"
    assert link_term.taxonomy_category == "link"
    assert link_term.output_id == "p0_port.flow"

    # Act & Assert
    validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalog_term_raises_when_output_id_belongs_to_another_category(test_dataset_dir: Path) -> None:
    # Arrange: active_load is valid on consumption, not on production
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    term = catalog.metrics["PROD"].terms[0]
    term.taxonomy_category = "production"
    term.output_id = "active_load"

    # Act & Assert
    with pytest.raises(ValueError, match="uses output-id"):
        validate_catalog_against_taxonomy(catalog, taxonomy)


def test_view_builder_raises_when_catalog_taxonomy_mismatch(
    test_dataset_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def catalogs_with_wrong_taxonomy(input_data_path: Path, catalog_ids: list[str]) -> dict[str, Catalog]:
        catalogs = load_catalogs(input_data_path, catalog_ids)
        next(iter(catalogs.values())).taxonomy = "wrong_taxonomy"
        return catalogs

    monkeypatch.setattr(
        "gems_views_builder.loader.load_catalogs",
        catalogs_with_wrong_taxonomy,
    )
    with pytest.raises(ValueError, match="references taxonomy"):
        Loader(test_dataset_dir).load()
