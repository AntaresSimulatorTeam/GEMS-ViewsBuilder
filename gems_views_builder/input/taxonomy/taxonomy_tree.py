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