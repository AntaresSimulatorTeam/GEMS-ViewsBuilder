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
    for category in taxonomy.categories:
        assert isinstance(category, TaxonomyCategory)
        assert isinstance(category.id, str)
        assert category.parent_category is None or isinstance(category.parent_category, str)


def test_taxonomy_items_are_typed(test_dataset_dir: Path) -> None:
    taxonomy_path = test_dataset_dir / "taxonomy.yml"
    taxonomy = load_taxonomy(taxonomy_path)
    for category in taxonomy.categories:
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
    category_ids = {c.id for c in taxonomy.categories}
    for expected in ("balance", "production", "consumption", "storage"):
        assert expected in category_ids
    if test_dataset_dir.name == "test_3":
        assert "link" in category_ids
        assert "coupling" in category_ids
