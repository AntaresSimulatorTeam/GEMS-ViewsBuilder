# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from gems_views_builder.input.taxonomy.taxonomy import Taxonomy, TaxonomyCategory


@dataclass(kw_only=True)
class TaxonomyTreeNode:
    id: str
    children: dict[str, TaxonomyTreeNode] = field(default_factory=dict)
    category: TaxonomyCategory | None = None
    descendants: set[str] = field(default_factory=set)


@dataclass
class TaxonomyTree:
    root: TaxonomyTreeNode = field(default_factory=lambda: TaxonomyTreeNode(id="root"))


def make_taxonomy_tree(taxonomy: Taxonomy) -> TaxonomyTree:
    taxon_tree = TaxonomyTree()
    # Step 1: insert nodes into the tree
    insert_nodes(taxonomy, taxon_tree)
    # Step 2: detect cycles
    detect_cycles(taxon_tree.root, set())
    # Step 3: enrich tree
    enrich_tree(taxon_tree.root)  # O(n)
    return taxon_tree


def insert_nodes(taxonomy: Taxonomy, taxon_tree: TaxonomyTree) -> None:
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


def detect_cycles(root: TaxonomyTreeNode, current_path: set[str]) -> None:
    """
    Time complexity: O(n) where n is number of categories
    Space complexity: O(log n) avg case, worst case O(n) if we skewed tree
    """
    # Base case: if the node is already in the current path, we have a cycle
    if root.id in current_path:
        raise ValueError(f"Cycle detected: {current_path}")

    current_path.add(root.id)
    for child in root.children.values():
        detect_cycles(child, current_path)
    current_path.remove(root.id)


def enrich_tree(node: TaxonomyTreeNode) -> set[str]:
    descendants: set[str] = set()
    for child in node.children.values():
        descendants.update(enrich_tree(child))
    node.descendants = descendants
    return {node.id} | descendants
