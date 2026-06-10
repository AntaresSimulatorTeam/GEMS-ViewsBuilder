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
