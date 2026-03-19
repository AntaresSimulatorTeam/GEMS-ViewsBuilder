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

from src.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyItem

TEST_FILES_ROOT = Path(__file__).resolve().parent.parent.parent / "resources" / "test_files"

TAXONOMY_PATH = [
    TEST_FILES_ROOT / "test_1" / "taxonomy.yml",
    TEST_FILES_ROOT / "test_3" / "taxonomy.yml",
]


@pytest.mark.parametrize("taxonomy_path", TAXONOMY_PATH)
def test_taxonomy_loads(taxonomy_path: Path) -> None:
    taxonomy = Taxonomy(taxonomy_path)
    assert taxonomy.id == "my_taxonomy"
    assert taxonomy.description != ""
    assert len(taxonomy.categories) > 0


@pytest.mark.parametrize("taxonomy_path", TAXONOMY_PATH)
def test_taxonomy_categories_are_typed(taxonomy_path: Path) -> None:
    taxonomy = Taxonomy(taxonomy_path)
    for category in taxonomy.categories:
        assert isinstance(category, TaxonomyCategory)
        assert isinstance(category.id, str)
        assert category.parent_category is None or isinstance(category.parent_category, str)


@pytest.mark.parametrize("taxonomy_path", TAXONOMY_PATH)
def test_taxonomy_items_are_typed(taxonomy_path: Path) -> None:
    taxonomy = Taxonomy(taxonomy_path)
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


def test_taxonomy_known_categories() -> None:
    taxonomy = Taxonomy(TEST_FILES_ROOT / "test_2" / "taxonomy.yml")
    category_ids = set([c.id for c in taxonomy.categories])
    assert "balance" in category_ids
    assert "production" in category_ids
    assert "dispatchable_production" in category_ids
    assert "consumption" in category_ids
    assert "storage" in category_ids
    assert "link" in category_ids
    assert "fatal_production" in category_ids
    assert "fatal_consumption" in category_ids
    assert "flexible_consumption" in category_ids
    assert "converter" in category_ids
    assert "coupling_models" in category_ids
    assert "capacity_investment_decisions" in category_ids
