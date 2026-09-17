# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0


from pathlib import Path

import pytest

from gems_views_builder.input.taxonomy.taxonomy import load_taxonomy
from gems_views_builder.input.taxonomy.taxonomy_tree import (
    TaxonomyTree,
    TaxonomyTreeNode,
    make_neighbors,
    make_taxonomy_tree,
)

TAXONOMY = """
taxonomy:
  id: test_tax
  description: "A simple taxonomy with id and parent_category for 5 categories"

  categories:
    - id: energy
      parent_category: null

    - id: production
      parent_category: energy

    - id: consumption
      parent_category: energy

    - id: balance
"""
TAXONOMY_WITH_SELF_LOOP = """
taxonomy:
  id: test_tax
  description: "A simple taxonomy with a self loop"

  categories:
    - id: energy
      parent_category: energy
"""

EXPECTED_NEIGHBORS = {
    "energy": {"production", "consumption"},
    "balance": set(),
    "production": set(),
    "consumption": set(),
    None: {"energy", "balance"},
}


def test_make_neighbors(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "taxonomy.yml").write_text(TAXONOMY)
    taxonomy = load_taxonomy(tmp_path / "taxonomy.yml")

    # Act
    neighbors = make_neighbors(taxonomy)

    # Assert
    assert neighbors == EXPECTED_NEIGHBORS


def test_make_neighbors_fails_on_self_loop(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "taxonomy.yml").write_text(TAXONOMY_WITH_SELF_LOOP)
    taxonomy = load_taxonomy(tmp_path / "taxonomy.yml")

    # Act + Assert
    with pytest.raises(ValueError):
        make_neighbors(taxonomy)


def test_make_taxonomy_tree(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "taxonomy.yml").write_text(TAXONOMY)
    taxonomy = load_taxonomy(tmp_path / "taxonomy.yml")
    taxonomy_tree = TaxonomyTree()
    # Act
    make_taxonomy_tree(taxonomy, taxonomy_tree)

    # Assert
    assert taxonomy_tree.root.id == "root"
    assert taxonomy_tree.root.children == {
        "energy": TaxonomyTreeNode(
            id="energy",
            category=taxonomy.categories["energy"],
            children={
                "production": TaxonomyTreeNode(id="production", category=taxonomy.categories["production"]),
                "consumption": TaxonomyTreeNode(id="consumption", category=taxonomy.categories["consumption"]),
            },
        ),
        "balance": TaxonomyTreeNode(id="balance", category=taxonomy.categories["balance"]),
    }
    assert taxonomy_tree.root.children["energy"].children["production"].children == {}
    assert taxonomy_tree.root.children["energy"].children["consumption"].children == {}
    assert taxonomy_tree.root.children["balance"].children == {}
