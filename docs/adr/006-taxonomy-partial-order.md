# ADR-006 — Taxonomy partial order (subcategory walk)

**Status**: Designed in spec, not yet implemented

## Context

The taxonomy supports a `parent-category` field on each category, defining a hierarchy
(partial order). Example:

```yaml
categories:
  - id: production
  - id: fatal_production
    parent-category: production
```

The intended behaviour of `LIST_OF_COMPONENTS_IN_TAXONOMY_CATEGORY(category)` is to return
components whose model belongs to `category` **or any of its subcategories** (i.e. categories
that have `category` as an ancestor in the hierarchy).

In the example: a term with `taxonomy-category: production` should match components of
both `production` models and `fatal_production` models.

## Current state

`ModelLibrary.get_components_in_taxonomy_category(taxonomy_category)` in `library.py`
does an **exact match** only:

```python
return self.models_by_taxonomy_category.get(taxonomy_category, [])
```

The `parent_category` field exists in `TaxonomyCategory` (`taxonomy.py`) but is not
used for component resolution.

## Work needed

1. Build a `children_by_category` index when loading the taxonomy (or library): for each
   category, collect all categories that transitively have it as an ancestor.
2. Modify `get_components_in_taxonomy_category` to also return models from all subcategories.
3. Alternatively, pass the taxonomy into `ModelLibrary` at index-build time and build the
   full descendant closure then.

## Impact

Without this, a catalog term targeting a parent category misses all components of child
categories, producing incomplete (silently low) metric values.

---

## Impact on LOCATING_FUNCTION

The partial order affects `LOCATING_FUNCTION` in two distinct ways.

### 1. Component selection (direct — this ADR)

`MetricStructureBuilder` calls
`ModelLibrary.get_components_in_taxonomy_category(term.taxonomy_category)` to find
contributing components. Without the downward walk, a term with
`taxonomy-category: production` misses all `fatal_production` components. This is the
primary concern of this ADR.

### 2. Peer validity check (indirect — ADR-001)

Once the peer location category check from [ADR-001](001-location-taxonomy-hierarchy.md)
is implemented, it will need to accept a peer whose taxonomy category is `catalog.location.taxonomy-category`
**or any of its descendants**. A peer of `fatal_production` (subcategory of `production`)
should be a valid location when `catalog.location.taxonomy-category = production`.

This check therefore also depends on the **downward walk** built by this ADR (from a
given category, enumerate all subcategories transitively).

---

## Impact on consistency checks

### Rule 3 — Term location port (upward walk needed)

`catalog_taxonomy_validator.py` currently checks:

```
term.location-ports ∈ taxonomy.category[term.taxonomy-category].ports[*].id
```

using an exact category match. If a child category does not redeclare a port that its
parent declares, this check will raise a false `ValueError` for a term that targets the
child category with a parent's port.

Example: if `fatal_production` (child of `production`) does not redeclare `p_balance_port`,
a term `{taxonomy-category: fatal_production, location-ports: p_balance_port}` is rejected
today even if the port is physically present via the parent.

To fix this, the port lookup must walk **up** the hierarchy (ancestor walk), collecting
ports from all ancestor categories in addition to the declared category's own ports.

> Note: the direction is opposite to component resolution — ports require an **ancestor
> walk** (upward), while component resolution requires a **descendant walk** (downward).

### Rules 2, 7b, 7d — not affected

- **Rule 2** (`term.taxonomy-category ∈ taxonomy.categories[*].id`): pure membership
  check — no hierarchy traversal needed.
- **Rule 7b** (`scope.taxonomy-category ∈ taxonomy.categories[*].id`): same.
- **Rule 7d** (`scope.taxonomy-category == catalog.location.taxonomy-category`): exact
  equality is correct — the scope declares the top-level location category explicitly.

---

## Impact on ADR-007 (consistency check strategy)

[ADR-007](007-consistency-check-strategy.md) proposes a fail-fast ordered sequence of
checks. ADR-006 has three consequences for that sequence.

### 1. New prerequisite: hierarchy index build

Both modified checks (Rule 3 port lookup and Rule 6 peer category check) require
pre-computed indexes that do not exist today:

- **Descendant closure**: for each category, the set of all transitively-descendant
  category ids. Used by component resolution and the peer category check (downward walk).
- **Ancestor closure**: for each category, the ordered list of ancestor category ids.
  Used by the port lookup (upward walk).

These indexes are O(categories²) to build and only need to be computed once from the
loaded `Taxonomy`. They should be built as part of `Loader.load()` (or lazily on first
use) before any check that depends on them runs. ADR-007's recommended sequence should
therefore become:

```
1. Layout check                 (file existence, O(1))
2. Calendar format              (keep at load time)
3. SimulationTable columns      (keep at load time)
4. Taxonomy hierarchy indexes   ← NEW: build descendant + ancestor closures, O(categories²)
5. Catalog ↔ taxonomy           (port check now uses ancestor walk)
6. view_config ↔ catalog        (unchanged)
7. Peer category check          (now uses descendant walk)
```

### 2. Two existing checks change in complexity

Steps 5 and 7 in ADR-007's sequence change from O(1) set-membership lookups to
O(depth) hierarchy walks per term or component. For shallow taxonomies (typical depth
≤ 5) this remains negligible, and the checks stay in the same position in the ordered
sequence. No reordering of ADR-007's sequence is required beyond inserting step 4.

### 3. The "execution-time checks become assertions" argument weakens slightly

ADR-007's recommendation closes with: *"Execution-time checks (uniqueness) become
assertions — if inputs are valid, uniqueness is guaranteed by construction."* This holds
for Rule 5 (uniqueness). However, the peer category check (Rule 6) cannot be fully
pre-computed at startup for large systems: it depends on which peers are actually resolved
per metric, which requires iterating the system graph. This check therefore remains
O(components × terms) at startup, as ADR-007 already notes — ADR-006 does not change
its phase, only its predicate (exact match → descendant walk).
