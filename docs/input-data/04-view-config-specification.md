# View Config Specification

`view_config.yml` is the top-level configuration file that selects which metrics to
compute and how to aggregate them.

---

## Structure

```yaml
view:
  id: <str>

  scope:
    - location:
      taxonomy-category: <str>    # category of location components (e.g. balance)
    - calendar: <str>             # filename stem of the calendar CSV

  aggregation:
    - time: hour | day | week | month | year

  catalog:
    - id: <str>                   # filename stem of a catalog YAML (e.g. "my_catalog" → catalogs/my_catalog.yml)
    - ...

  metrics:
    - id: <catalog_key>.<metric_id>
    - ...
```

Python type: `ViewConfig` (`metrics.py`).

---

## Fields

### `view.id`

Identifier for this view configuration. Not used in output filenames; mainly for logging.

### `view.scope`

A list with two entries (both required):

| Entry | Field | Type | Description |
|---|---|---|---|
| `- location:` | `taxonomy-category` | str | Taxonomy category whose components are location units. Must match `catalog.location.taxonomy-category` for all referenced catalogs (not yet validated — see [ADR-007](../adr/007-consistency-check-strategy.md)). |
| `- calendar:` | `calendar` | str | Filename stem of the calendar CSV (e.g. `calendar_file` for `calendar_file.csv`). |

> **YAML note**: the `location:` key is syntactically present but ignored by the parser.
> The `taxonomy-category` field is read directly from the same list item.

### `view.aggregation`

```yaml
aggregation:
  - time: hour    # or day | week | month | year
```

Declares the intended temporal granularity. Loaded into `ViewConfig.time_aggregation`
but **not yet applied** in the current aggregation code — the output `view_date` equals
the raw `granular_date` from the calendar. See [ADR-007](../adr/007-consistency-check-strategy.md).

### `view.catalog`

List of catalog references. Each `id` is the **filename stem** (not the internal `catalog.id`
field inside the YAML):

```yaml
catalog:
  - id: my_catalog    # loads catalogs/my_catalog.yml
```

### `view.metrics`

List of metric references in `<catalog_key>.<metric_id>` format:

```yaml
metrics:
  - id: my_catalog.PRODUCTION
  - id: my_catalog.LOAD
  - id: other_catalog.BALANCE
```

The part before the first `.` is the catalog key (must match an entry in `view.catalog`).
The remainder is the metric id within that catalog.

Metrics are processed in declaration order.

---

## Full example

From `resources/tests/test_inputs/test_3/view_config.yml`:

```yaml
view:
  id: view_area

  scope:
    - location:
      taxonomy-category: balance

    - calendar: calendar_file

  aggregation:
    - time: hour

  catalog:
    - id: catalog             # loads catalogs/catalog.yml

  metrics:
    - id: catalog.PROD
    - id: catalog.LOAD
    - id: catalog.BALANCE
```

---

## Relationships

```
view_config.yml
  └─ scope.taxonomy-category ─────────────► taxonomy category id
                                             (should equal catalog.location.taxonomy-category)
  └─ scope.calendar ───────────────────────► calendar*.csv (filename stem)
  └─ catalog[*].id ────────────────────────► catalogs/<id>.yml (filename)
  └─ metrics[*].id = <catalog_key>.<metric_id>
       ├─ <catalog_key> ──────────────────► catalog[*].id (must be listed above)
       └─ <metric_id> ────────────────────► metric.id inside that catalog
```
