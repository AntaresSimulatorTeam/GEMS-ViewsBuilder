# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaxonomyTreeNode:
    id: str
    # children_ids represents everything under this node (whole subtree), not only first-level children
    children_ids: set[str] = field(default_factory=set)
    # First level children
    childrens: dict[str, TaxonomyTreeNode] = field(default_factory=dict)


@dataclass
class TaxonomyTree:
    root: TaxonomyTreeNode
