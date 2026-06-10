# Cross-File Consistency Rules

These are the **logical rules** that must hold across input files for a study to be valid.
For the code that enforces them (and which are not yet enforced), see
[`pipeline/02-validation-and-checks.md`](../pipeline/02-validation-and-checks.md).

---

## 1. Taxonomy identity

`catalog.taxonomy` must equal `taxonomy.id`.

```
catalog.yml  →  catalog.taxonomy == taxonomy.yml  →  taxonomy.id
```

**Enforced**: yes (`catalog_taxonomy_validator.py`).

---

## 2. Term taxonomy category

Every `term.taxonomy-category` in every metric must be a valid category id in the taxonomy.

```
catalog  →  term.taxonomy-category  ∈  taxonomy.categories[*].id
```

**Enforced**: yes (`catalog_taxonomy_validator.py`).

---

## 3. Term location port

When `term.location-ports` is not null, it must be a port id declared on
`term.taxonomy-category` in the taxonomy.

```
catalog  →  term.location-ports  ∈  taxonomy.category[term.taxonomy-category].ports[*].id
```

**Enforced**: yes, for string values (`catalog_taxonomy_validator.py`).

> Current limitation: only single-string `location-ports` values are checked. Tuple values
> (multi-port) are not iterated.

---

## 4. Term output-id

`term.output-id` must be a valid output identifier for models in `term.taxonomy-category`:
a variable id, port-field-definition id (`<port>.<field>`), or extra-output id from those models.

```
catalog  →  term.output-id  ∈  { variable.id | port-field-def.id | extra-output.id }
            for models where model.taxonomy-category == term.taxonomy-category
```

**Enforced**: **no** — not yet implemented. See [ADR-007](../adr/007-consistency-check-strategy.md).

---

## 5. Location resolution uniqueness

For each `(component, location-port)` pair processed at metric build time,
exactly **one** peer component must be connected through that port.
Zero peers or two or more peers raises a `ValueError`.

**Enforced**: yes, at execution time (`system.py:_get_peer_components` + `get_location`).

---

## 6. Peer location category

The peer component resolved via a location port must belong to
`catalog.location.taxonomy-category` (i.e. it must be a location component).

**Enforced**: **no** — not yet implemented. See [ADR-001](../adr/001-location-taxonomy-hierarchy.md)
and [ADR-003](../adr/003-get-location-ownership.md).

---

## 7. view_config ↔ catalog location consistency

`view_config.scope.taxonomy-category` should equal `catalog.location.taxonomy-category`
for all catalogs referenced by the view config.

**Enforced**: **no** — not yet validated. See [ADR-007](../adr/007-consistency-check-strategy.md).

---

## 8. Calendar ↔ SimulationTable join completeness

The calendar must contain a row for every `absolute_time_index` value present in the
simulation table (for time-dependent rows). Mismatches are not detected explicitly; the
inner join in Step 1 silently drops unmatched rows.

**Enforced**: **no** — detected implicitly at join time with no error raised.

---

## Summary table

| Rule | Enforced | Where |
|---|---|---|
| `catalog.taxonomy == taxonomy.id` | ✅ | `catalog_taxonomy_validator.py` |
| `term.taxonomy-category ∈ taxonomy.categories` | ✅ | `catalog_taxonomy_validator.py` |
| `term.location-ports ∈ category.ports` (string only) | ✅ | `catalog_taxonomy_validator.py` |
| `term.output-id` valid for taxonomy-category | ❌ | not implemented |
| Location port resolves to exactly 1 peer | ✅ | `system.py`, execution time |
| Peer belongs to `catalog.location.taxonomy-category` | ❌ | not implemented |
| `view_config.taxonomy-category == catalog.location.taxonomy-category` | ❌ | not implemented |
| Calendar covers all sim table timesteps | ❌ | silent at join time |
