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
    config = load_view_config(test_dataset_dir / "view_config.yml")
    CatalogsTaxonomyValidator(load_catalogs(test_dataset_dir, config.catalog_ids), taxonomy).validate()


@pytest.mark.parametrize(
    ("attribute", "value", "match"),
    [
        ("taxonomy", "wrong_taxonomy", "references taxonomy"),
        ("taxonomy_category", "unknown_category", "uses taxonomy-category"),
        ("location_port", "unknown_port", "uses location-port"),
        ("output_id", "unknown_output", "uses output-id"),
    ],
)
def test_catalogs_taxonomy_validator_rejects_invalid_references(
    test_dataset_dir: Path, attribute: str, value: str, match: str
) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    catalog = load_catalog(next((test_dataset_dir / "catalogs").glob("*.yml")))
    target = catalog if attribute == "taxonomy" else next(iter(catalog.metrics.values())).terms[0]
    setattr(target, attribute, value)
    with pytest.raises(ValueError, match=match):
        CatalogsTaxonomyValidator([catalog], taxonomy).validate()
