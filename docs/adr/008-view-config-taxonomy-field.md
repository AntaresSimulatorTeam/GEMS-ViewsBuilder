# ADR-008 — Taxonomy field in view-config

**Status**: Planned — tracked in [issue #57](https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/issues/57)

## Context

`catalog.yml` already declares two taxonomy-related fields at the top level:

```yaml
catalog:
  taxonomy: my_taxonomy                    # which taxonomy this catalog is written against
  location:
    taxonomy-category: balance             # category whose instances serve as location units
```

`view_config.yml` currently has **neither** of these fields:

- There is no `taxonomy` field — the view-config does not declare which taxonomy it is
  written against.
- There is no explicit `location` section — the location taxonomy category is declared
  implicitly through `scope.taxonomy-category`, which plays the same role but uses a
  different key.

This creates three gaps (flagged as "not yet implemented" in ADR-007 and
`05-consistency-rules.md`):

1. No check that `view_config.scope.taxonomy-category` is a valid category id in the
   taxonomy (without a `taxonomy` field in view_config, this cross-check cannot be
   performed).
2. No check that the view-config and the catalogs it references all target the **same
   taxonomy**.
3. No check that `view_config.scope.taxonomy-category` matches
   `catalog.location.taxonomy-category` for every referenced catalog.

When these values diverge, the pipeline runs without error but produces outputs where
scope filtering and location resolution are driven by inconsistent taxonomy assumptions.

## Decision

### 1. Add a `taxonomy` field to `view_config.yml`

A top-level `taxonomy: <id>` field is added, mirroring the field already present in
`catalog.yml`. It identifies the taxonomy the view-config is written against.

Updated structure:

```yaml
view:
  id: <str>
  taxonomy: <str>            # ← NEW: must match taxonomy.id and all catalog.taxonomy values

  scope:
    - location:
      taxonomy-category: <str>   # location taxonomy category (see note below)
    - calendar: <str>
  ...
```

### 2. Keep `scope.taxonomy-category` as the location category declaration

`scope.taxonomy-category` already holds the same information as
`catalog.location.taxonomy-category`. Rather than introducing a separate
`location.taxonomy-category` key in view_config (which would require restructuring
`scope`), the existing field is used as-is for cross-validation.

### 3. Add four new consistency checks

Once the `taxonomy` field exists in view-config, the following checks should be enforced
at startup (parsing-time, alongside the existing `catalog_taxonomy_validator`):

| Check | Error raised |
|---|---|
| `view_config.taxonomy == taxonomy.id` | `ValueError` |
| `view_config.scope.taxonomy-category ∈ taxonomy.categories[*].id` | `ValueError` |
| `view_config.taxonomy == catalog.taxonomy` for every referenced catalog | `ValueError` |
| `view_config.scope.taxonomy-category == catalog.location.taxonomy-category` for every referenced catalog | `ValueError` |

These checks ensure the view-config, all its catalogs, and the loaded taxonomy form a
fully consistent set before any computation begins.

## Alternatives considered

**Rename `scope.taxonomy-category` to `location.taxonomy-category`** (mirroring catalog
structure exactly). This would make the schemas of view-config and catalog uniform on this
point, but requires a breaking change to the `view.scope` list format. Deferred — the
`scope` structure may itself evolve (e.g. to support multiple location categories), so the
renaming is left for a future redesign of the `scope` field.

## Consequences

- Any existing `view_config.yml` without a `taxonomy` field will fail to load once this
  is implemented (breaking change to the input format).
- Eliminates silent inconsistencies where view-config and catalog reference different
  taxonomies or use different location categories.
- Adds four new startup `ValueError` paths (fast-fail — no computation wasted).
