# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from gems_views_builder import TaxonomyCategory, TaxonomyItem, load_taxonomy


def test_taxonomy_loads(test_dataset_dir: Path) -> None:
    taxonomy_path = test_dataset_dir / "taxonomy.yml"
    taxonomy = load_taxonomy(taxonomy_path)
    assert taxonomy.id == "my_taxonomy"
    assert taxonomy.description != ""
    assert len(taxonomy.categories) > 0


def test_taxonomy_categories_are_typed(test_dataset_dir: Path) -> None:
    taxonomy_path = test_dataset_dir / "taxonomy.yml"
    taxonomy = load_taxonomy(taxonomy_path)
    for category_id, category in taxonomy.categories.items():
        assert isinstance(category_id, str)
        assert isinstance(category, TaxonomyCategory)
        assert category.id == category_id
        assert category.parent_category is None or isinstance(category.parent_category, str)


def test_taxonomy_items_are_typed(test_dataset_dir: Path) -> None:
    taxonomy_path = test_dataset_dir / "taxonomy.yml"
    taxonomy = load_taxonomy(taxonomy_path)
    for category in taxonomy.categories.values():
        for field in (
            category.variables,
            category.parameters,
            category.ports,
            category.constraints,
            category.extra_outputs,
            category.properties,
        ):
            for item in field:
                assert isinstance(item, TaxonomyItem)
                assert isinstance(item.id, str)


def test_taxonomy_known_categories(test_dataset_dir: Path) -> None:
    taxonomy = load_taxonomy(test_dataset_dir / "taxonomy.yml")
    for expected in ("balance", "production", "consumption", "storage"):
        assert expected in taxonomy.categories
    if test_dataset_dir.name == "test_3":
        assert "link" in taxonomy.categories
        assert "coupling" in taxonomy.categories
