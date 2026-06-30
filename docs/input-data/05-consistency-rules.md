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

> Current bug: tuple `location-ports` values (multi-port) trigger a false `ValueError` — the
> tuple is compared against the set of string port ids and never matches, so any multi-port
> term would incorrectly fail validation. This is latent because no existing test uses a
> tuple `location-ports` in YAML.

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

## 5. Location resolution — zero peers

For each `(component, location-port)` pair processed at metric build time, if no connection
exists for that port (i.e. the pair is absent from the connection index), a `ValueError` is
raised.

**Enforced**: yes, at execution time (`system.py:InputSystem._get_peer_components`).

> **Multiple peers**: if a port connects to several peers, they are all returned and merged
> into `metric_location` as `{peer1,peer2,...}`. No error is raised. Enforcing uniqueness
> (exactly one peer per port) is the intended future behaviour — see
> [ADR-003](../adr/003-get-location-ownership.md).

---

## 6. Peer location category

The peer component resolved via a location port must belong to
`catalog.location.taxonomy-category` (i.e. it must be a location component).

**Enforced**: **no** — not yet implemented. See [ADR-001](../adr/001-location-taxonomy-hierarchy.md)
and [ADR-003](../adr/003-get-location-ownership.md).

---

## 7. view_config ↔ taxonomy and catalog consistency

> **TODO(#57)**: all four sub-rules below require a `taxonomy` field on `view_config.yml`
> (not yet added). See [ADR-008](../adr/008-view-config-taxonomy-field.md).

### 7a. view_config references a known taxonomy

```
view_config.taxonomy == taxonomy.id
```

**Enforced**: **no** — field `view_config.taxonomy` does not exist yet.

### 7b. scope location category exists in the taxonomy

```
view_config.scope.taxonomy-category ∈ taxonomy.categories[*].id
```

**Enforced**: **no** — requires `view_config.taxonomy` field to identify which taxonomy to
check against.

### 7c. view_config and its catalogs target the same taxonomy

```
view_config.taxonomy == catalog.taxonomy   (for every referenced catalog)
```

**Enforced**: **no** — field `view_config.taxonomy` does not exist yet.

### 7d. scope location category matches catalog location category

```
view_config.scope.taxonomy-category == catalog.location.taxonomy-category
                                       (for every referenced catalog)
```

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
| Location port has at least 1 connection (0-peer case) | ✅ | `system.py`, execution time |
| Location port resolves to exactly 1 peer (uniqueness) | ❌ | not implemented (multiple peers merged silently) |
| Peer belongs to `catalog.location.taxonomy-category` | ❌ | not implemented |
| **TODO(#57)** `view_config.taxonomy == taxonomy.id` | ❌ | field not yet added |
| **TODO(#57)** `view_config.scope.taxonomy-category ∈ taxonomy.categories` | ❌ | field not yet added |
| **TODO(#57)** `view_config.taxonomy == catalog.taxonomy` (per catalog) | ❌ | field not yet added |
| **TODO(#57)** `view_config.scope.taxonomy-category == catalog.location.taxonomy-category` | ❌ | not implemented |
| Calendar covers all sim table timesteps | ❌ | silent at join time |
