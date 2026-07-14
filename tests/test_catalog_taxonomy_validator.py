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

from gems_views_builder.input.catalog import load_catalog, load_catalogs
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.catalogs_taxonomy_validator import CatalogsTaxonomyValidator


def test_catalogs_taxonomy_validator_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    CatalogsTaxonomyValidator([catalog], taxonomy).validate()


def test_catalogs_taxonomy_validator_passes_for_loaded_catalogs(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalogs = load_catalogs(test_dataset_dir, view_config.catalog_ids)
    CatalogsTaxonomyValidator(catalogs, taxonomy).validate()


def test_catalogs_taxonomy_validator_raises_on_taxonomy_id_mismatch(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(test_dataset_dir / "catalogs" / "catalog.yml")
    catalog.taxonomy = "wrong_taxonomy"
    with pytest.raises(ValueError, match="references taxonomy"):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()


def test_catalogs_taxonomy_validator_raises_on_unknown_metric_category(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    next(iter(catalog.metrics.values())).terms[0].taxonomy_category = "unknown_category"
    with pytest.raises(ValueError, match="uses taxonomy-category"):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()


def test_catalogs_taxonomy_validator_raises_on_unknown_location_port(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    next(iter(catalog.metrics.values())).terms[0].location_ports = ("unknown_port",)
    with pytest.raises(ValueError, match="uses location-port"):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()


def test_catalogs_taxonomy_validator_raises_on_unknown_output_id(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    next(iter(catalog.metrics.values())).terms[0].output_id = "unknown_output"
    with pytest.raises(ValueError, match="uses output-id"):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()


def test_catalogs_taxonomy_validator_raises_when_output_id_belongs_to_another_category(
    test_dataset_dir: Path,
) -> None:
    if test_dataset_dir.name != "test_3":
        pytest.skip("requires the test_3 taxonomy fixture, where active_load is only valid on consumption")

    # active_load is valid on consumption, not on production
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    term = catalog.metrics["PROD"].terms[0]
    term.taxonomy_category = "production"
    term.output_id = "active_load"
    with pytest.raises(ValueError, match="uses output-id"):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()
