# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from gems_views_builder.input.taxonomy.taxonomy import Taxonomy, TaxonomyCategory


@dataclass(kw_only=True)
class DummyNode:
    id: str
    children: dict[str, DummyNode] = field(default_factory=dict)


@dataclass(kw_only=True)
class TaxonomyTreeNode(DummyNode):
    category: TaxonomyCategory
    has_parent: bool = False
    ancestors: set[str] = field(default_factory=set)


@dataclass
class TaxonomyTree:
    root: DummyNode = field(default_factory=lambda: DummyNode(id="root"))


def make_taxonomy_tree(taxonomy: Taxonomy, taxon_tree: TaxonomyTree) -> None:
    neighbors = make_neighbors(taxonomy)  # O(n)
    for cat in get_root_categories(neighbors):  # O(1)
        node = TaxonomyTreeNode(id=cat, category=taxonomy.categories[cat])
        taxon_tree.root.children[cat] = node
        insert_children(neighbors, node, taxonomy)


def insert_children(
    neighbors: dict[str | None, set[str]],
    taxon_tree_node: TaxonomyTreeNode,
    taxonomy: Taxonomy,
) -> None:
    # Base case: if the node has no children, return
    if not neighbors[taxon_tree_node.id]:
        return

    # Recursive case: insert children
    for child in neighbors[taxon_tree_node.id]:
        child_node = TaxonomyTreeNode(id=child, category=taxonomy.categories[child])
        taxon_tree_node.children[child] = child_node
        insert_children(neighbors, child_node, taxonomy)


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
    """
    Everything labeled as None is considered as a root category.
    Suppose we have cat1,cat2,cat3 as root categories.
    None : {cat1, cat2, cat3} -> cat1, cat2, cat3 are root categories.
    """
    return neighbors[None]
