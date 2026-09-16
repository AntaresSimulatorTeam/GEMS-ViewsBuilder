# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from gems_views_builder.input.taxonomy.taxonomy import Taxonomy, TaxonomyCategory


@dataclass
class TaxonomyTreeNode:
    id: str
    category: TaxonomyCategory | None = None
    has_parent: bool = False
    ancestors: set[str] = field(default_factory=set)
    children: dict[str, TaxonomyTreeNode] = field(default_factory=dict)


@dataclass
class TaxonomyTree:
    root: TaxonomyTreeNode = field(default_factory=lambda: TaxonomyTreeNode(id="root"))


def make_taxonomy_tree(taxonomy: Taxonomy, taxon_tree: TaxonomyTree) -> None:
    neighbors = make_neighbors(taxonomy)  # O(n)
    root_cat = get_root_categories(neighbors)  # O(1)
    for cat in root_cat:
        taxon_tree.root.children[cat] = TaxonomyTreeNode(id=cat, category=taxonomy.categories[cat])
        # TODO: implement recursive function to build the tree

    # Bottom up BFS to fill ancestors


def make_neighbors(taxonomy: Taxonomy) -> dict[str | None, set[str]]:
    neighbors: dict[str | None, set[str]] = defaultdict(set)
    for cat in taxonomy.categories.values():
        check_self_loop(cat.id, cat.parent_category)
        neighbors[cat.parent_category].add(cat.id)
        neighbors.setdefault(cat.id, set())
    return neighbors


def check_self_loop(cat_id: str, parent_cat_id: str | None) -> None:
    if parent_cat_id is not None and cat_id == parent_cat_id:
        raise ValueError(f"Category ID={cat_id} is its own parent")


def get_root_categories(neighbors: dict[str | None, set[str]]) -> set[str]:
    return neighbors[None]
