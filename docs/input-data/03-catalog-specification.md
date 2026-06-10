# Catalog Specification

A catalog file (`catalogs/<id>.yml`) defines a collection of business metrics for a study.
Multiple catalog files can be referenced by a single `view_config.yml`.

> **File naming**: the filename stem (without `.yml`) is used as the catalog key in
> `view_config.yml` and in the metric reference format `<catalog_key>.<metric_id>`.
> The internal `catalog.id` field is separate and is only used in error messages and validation.

---

## Top-level structure

```yaml
catalog:
  id: <str>                            # internal identifier (used in error messages)
  taxonomy: <str>                      # must equal taxonomy.id of the study
  location:
    taxonomy-category: <str>           # category whose components serve as location units
  metrics-definition:
    - <metric>
    - ...
```

Python type: `Catalog` (`catalog.py`).

---

## Metric fields

```yaml
- id: <str>
  terms:
    - <term>
    - ...                              # 1..N terms
  terms-operator: sum | avg
  time-operator: sum | avg
  breakdown:                           # optional; 0..N keys
    - key: <str>
    - ...
  filter:                              # optional; 0..1
    key: <str>
    value: <str>
```

| Field | Required | Description |
|---|---|---|
| `id` | yes | Metric identifier, unique within the catalog |
| `terms` | yes | 1..N output contributions |
| `terms-operator` | yes | How to combine values from multiple terms: `sum` or `avg` |
| `time-operator` | yes | How to aggregate over time within a `view_date` bucket: `sum` or `avg` |
| `breakdown` | no | Split output by these component property keys |
| `filter` | no | Restrict contributing components to those where `properties[key] == value` |

Python type: `Metric` (`catalog.py`).

---

## Term fields

```yaml
- taxonomy-category: <str>            # category of contributing components
  output-id: <str>                    # which output to read from the simulation table
  location-ports: null | <str>        # how to resolve the location of each component
  weight-output-id: <str>             # optional; for weighted operators (not yet used)
```

| Field | Type | Description |
|---|---|---|
| `taxonomy-category` | str | All components with models in this category contribute |
| `output-id` | str | Must be a variable id, port-field-def id, or extra-output id valid for this category |
| `location-ports` | null / str | `null` = self-location; `"port_name"` = locate via that port |
| `weight-output-id` | str / null | Future use (see [ADR-005](../adr/005-terms-operator-weighted.md)) |

Python type: `Term` (`catalog.py`).

> **Note on subcategories**: currently `taxonomy-category` is an exact match only.
> The intended behaviour (walk subcategories via `parent-category`) is not yet implemented.
> See [ADR-006](../adr/006-taxonomy-partial-order.md).

---

## `filter` — restricting contributing components

```yaml
filter:
  key: technology
  value: nuclear
```

- **Cardinality**: 0 or 1 per metric (see [ADR-002](../adr/002-filter-cardinality.md)).
- A component contributes only if `properties[key] == value`.
- `value` is required; omitting it raises a validation error at load time.

---

## `breakdown` — splitting output by property

```yaml
breakdown:
  - key: technology
  - key: company
```

- **Cardinality**: 0..N keys per metric.
- All distinct `value`s found on contributing components are emitted (no pre-declared values).
- A component missing a key emits `(key, None)` for that key.
- Output format: `{(key1,val1),(key2,val2)}` — pairs in catalog declaration order.

**Why declaration order matters**: two components may declare the same properties in different
order in `system.yml`. The breakdown string is built from the catalog's key list order, ensuring
identical strings for equivalent components regardless of property declaration order.

---

## Full example

From `resources/tests/test_inputs/filtering_and_breakdown/catalogs/catalog.yml`:

```yaml
catalog:
  id: catalog
  taxonomy: my_taxonomy
  location:
    taxonomy-category: balance

  metrics-definition:

    # Simple metric: total production per location
    - id: PRODUCTION
      terms:
        - taxonomy-category: production
          output-id: generation
          location-ports: balance_port
      terms-operator: sum
      time-operator: sum

    # Breakdown: production split by technology
    - id: PRODUCTION_BY_TECH
      terms:
        - taxonomy-category: production
          output-id: generation
          location-ports: balance_port
      terms-operator: sum
      time-operator: sum
      breakdown:
        - key: technology

    # Filter: only nuclear generators
    - id: NUCLEAR_PRODUCTION
      terms:
        - taxonomy-category: production
          output-id: generation
          location-ports: balance_port
      terms-operator: sum
      time-operator: sum
      filter:
        key: technology
        value: nuclear

    # Multi-key breakdown: production by technology AND company
    - id: PRODUCTION_BY_TECH_AND_COMPANY
      terms:
        - taxonomy-category: production
          output-id: generation
          location-ports: balance_port
      terms-operator: sum
      time-operator: sum
      breakdown:
        - key: technology
        - key: company

    # Multi-term metric: balance (link flows at both ends)
    - id: BALANCE
      terms:
        - taxonomy-category: link
          output-id: p0_port.flow
          location-ports: p0_port
        - taxonomy-category: link
          output-id: p1_port.flow
          location-ports: p1_port
      terms-operator: sum
      time-operator: sum
```

---

## Relationship summary

```
catalog.yml
  └─ catalog.taxonomy ──────────────────────► taxonomy.id
  └─ catalog.location.taxonomy-category ───► taxonomy category id
  └─ metric.filter / breakdown.key ────────► component property key (in system.yml)
  └─ term.taxonomy-category ───────────────► taxonomy category id
  └─ term.location-ports ──────────────────► port id on that taxonomy category
  └─ term.output-id ───────────────────────► variable / port-field-def / extra-output id
                                             in models of that taxonomy-category (NOT YET validated)
```
