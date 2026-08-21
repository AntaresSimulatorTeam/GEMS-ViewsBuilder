# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest

from gems_views_builder.input.catalog import load_catalog, load_catalogs
from gems_views_builder.input.taxonomy import load_taxonomy
from gems_views_builder.input.view_config import load_view_config
from gems_views_builder.validation.catalog_taxonomy_validator import (
    validate_catalog_against_taxonomy,
    validate_catalogs_against_taxonomy,
)


def test_validate_catalog_against_taxonomy_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    validate_catalog_against_taxonomy(catalog, taxonomy)


def test_validate_catalogs_against_taxonomy_passes_for_test_dataset(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    view_config = load_view_config(test_dataset_dir / "view_config.yml")
    catalogs = load_catalogs(test_dataset_dir / "catalogs", view_config.catalog_ids)
    validate_catalogs_against_taxonomy(catalogs, taxonomy)


def test_validate_catalog_against_taxonomy_raises_on_taxonomy_id_mismatch(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(test_dataset_dir / "catalogs" / "catalog.yml")
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
    next(iter(catalog.metrics.values())).terms[0].location_port = "unknown_port"
    with pytest.raises(ValueError, match="uses location-port"):
        validate_catalog_against_taxonomy(catalog, taxonomy)
