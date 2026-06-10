# Processing Pipeline

Entry point: `ViewBuilder(input_data_path).build()` in `views.py`.

---

## Workflow

```
[taxonomy.yml]                  ┌─ INIT: validate + load all inputs ─────────────────────────┐
[library.yml]                   │ StudyLayoutValidator.validate()                             │
[system.yml]          ─────────►│ validate_catalogs_against_taxonomy()                        │
[view_config.yml]               │ Loader.load()                                               │
[catalog(s).yml]                └─────────────────────────────────────────────────────────────┘
[calendar*.csv]                                          │
[simulation_table*.parquet]                              ▼
                                ┌─ STEP 1: Time-filter simulation table ──────────────────────┐
                                │ simulation_table.filter_simulation_table(calendar, path)     │
                                │   inner join on absolute_time_index                          │
                                │   keep only rows where block == calendar.block               │
                                │   pass-through null-index rows (non-time-dependent)          │
                                │ → views/intermediate/simulation_table_filtered.parquet        │
                                └────────────────────────────┬────────────────────────────────┘
                                                             │
                                  ┌──────────────────────────┘
                                  │  for each metric in view_config.metrics:
                                  ▼
                                ┌─ STEP 2a: Build METRIC_STRUCTURE_TABLE ─────────────────────┐
                                │ MetricStructureBuilder.build()                               │
                                │   for each term: find model ids in taxonomy_category         │
                                │                  find component instances                    │
                                │                  apply filter                                │
                                │                  resolve location (LOCATING_FUNCTION)        │
                                │                  format breakdown_properties                 │
                                │ → views/metric_structure/<metric_id>.parquet                 │
                                └────────────────────────────┬────────────────────────────────┘
                                                             │
                                                             ▼
                                ┌─ STEP 2b: Join + aggregate terms ──────────────────────────┐
                                │ Aggregator.aggregate_metric_terms()                         │
                                │   right join filtered_sim_table on (component, output)      │
                                │   group by (metric_id, metric_location,                     │
                                │             breakdown_properties, absolute_time_index,       │
                                │             scenario)                                        │
                                │   apply terms_operator (sum or avg) on value                │
                                │ → views/metric_view/<metric_id>.parquet                     │
                                └────────────────────────────┬────────────────────────────────┘
                                                             │
                                                             ▼
                                ┌─ STEP 2c: Temporal aggregation ────────────────────────────┐
                                │ Aggregator.aggregate_metric_temporally()                    │
                                │   alias granular_date as view_date  ← (no truncation yet)  │
                                │   group by (metric_id, metric_location,                     │
                                │             breakdown_properties, scenario, view_date)       │
                                │   apply time_operator (sum or avg) on granular_metric_value │
                                │ → temporal_aggregation/<metric_id>-<n>.parquet              │
                                └────────────────────────────┬────────────────────────────────┘
                                                             │
                                  └──── end metric loop ─────┘
                                                             │
                                                             ▼
                                ┌─ STEP 3: Merge results ─────────────────────────────────────┐
                                │ Writer.merge_results()                                       │
                                │   scan all temporal_aggregation parts                        │
                                │   sink to results/view<timestamp>.parquet                   │
                                │   delete intermediate files                                  │
                                └─────────────────────────────────────────────────────────────┘
```

---

## Pre-pipeline: validation and loading

### Validation (`ViewBuilder.__init__`)

1. `StudyLayoutValidator(path).validate()` — checks required files exist.
2. `Loader.load(path)` — loads all input files (taxonomy, view_config, catalogs, simulation table, library, system).
3. `validate_catalogs_against_taxonomy(catalogs, taxonomy)` — cross-checks catalog references against taxonomy.

See [`pipeline/02-validation-and-checks.md`](02-validation-and-checks.md) for the full check list.

---

## Step 1 — Time-filtering the simulation table

Source: `simulation_table.py:SimulationTable.filter_simulation_table`

Two sub-steps, written to disk, then merged:

**Time-dependent rows** (non-null `absolute_time_index`):
```
filtered = simulation_table
  INNER JOIN calendar ON absolute_time_index
  WHERE block == calendar.block   ← reference-block filter
```
This removes repeated measurements of the same timestep from overlapping blocks in
rolling-horizon simulations. Adds `granular_date` from the calendar.

**Non-time-dependent rows** (null `absolute_time_index`):
Passed through as-is with `granular_date = null`. These represent constant outputs
(e.g. optimal capacities) that are not tied to a specific timestep.

Result: `views/intermediate/simulation_table_filtered.parquet`

---

## Step 2a — METRIC_STRUCTURE_TABLE

Source: `metrics_builder.py:MetricStructureBuilder.build`

One row per `(metric, contributing component, output)` — independent of time and scenario.

**Schema:**

| Column | Type | Description |
|---|---|---|
| `metric_id` | str | Metric identifier |
| `component` | str | Contributing component instance id |
| `metric_location` | str | Resolved location in `{id}` or `{id1,id2}` format |
| `breakdown_properties` | str | `{(key,val),...}` or `{}` if no breakdown |
| `output` | str | output-id to join against the simulation table |
| `weight_output_id` | int64 | Always `1` currently (future: weighted operators) |

**Algorithm:**

```python
for term in metric.terms:
    model_ids = library.get_components_in_taxonomy_category(term.taxonomy_category)
    for model_id in model_ids:
        for component_id in system.get_instances_by_model(f"{library.id}.{model_id}"):
            component = system.get_component(component_id)
            if filter is None or component.properties[filter.key] == filter.value:
                location = system.get_location(component_id, term.location_ports)
                metric_location = "{" + ",".join(location) + "}"
                breakdown = "{" + ",".join(f"({k},{component.properties.get(k,'None')})"
                                           for k in breakdown_keys) + "}"
                rows.append(...)
```

**LOCATING_FUNCTION** (`system.py:InputSystem.get_location`):

| `location_ports` | Returns |
|---|---|
| `null` | `component_id` (self-location) |
| `"port_name"` | all peer ids connected through that port (str if one, tuple if several) |
| `("p0_port", "p1_port")` | flat tuple of all peer ids from all listed ports |

If the port has no connection at all (absent from the index), `ValueError` is raised.
If the port has **multiple peers**, they are all included — no uniqueness check today.
Enforcing uniqueness (exactly one peer per port) is planned; see [ADR-003](../adr/003-get-location-ownership.md).

**`metric_location` format:**
- Single location: `{busA}`
- Multi-port: `{busA,busB}`

**`breakdown_properties` format:**
- No breakdown: `{}`
- With breakdown: `{(technology,nuclear),(company,rhonepower)}`

---

## Step 2b — Terms aggregation

Source: `aggregator.py:Aggregator.aggregate_metric_terms`

```sql
SELECT
  metric_id, metric_location, breakdown_properties,
  absolute_time_index, scenario_index AS scenario,
  TERMS_OPERATOR(value) AS granular_metric_value,
  first(granular_date) AS granular_date
FROM filtered_simulation_table
RIGHT JOIN metric_structure_table ON (component, output)
GROUP BY metric_id, metric_location, breakdown_properties, absolute_time_index, scenario
```

`TERMS_OPERATOR` = `SUM` or `AVG` from `metric.terms_operator`.

The RIGHT JOIN means rows from `metric_structure_table` with no matching simulation data
produce null `granular_metric_value`.

---

## Step 2c — Temporal aggregation

Source: `aggregator.py:Aggregator.aggregate_metric_temporally`

```sql
SELECT
  metric_id, metric_location, breakdown_properties, scenario,
  granular_date AS view_date,
  TIME_OPERATOR(granular_metric_value) AS metric_value
FROM metric_view
GROUP BY metric_id, metric_location, breakdown_properties, scenario, view_date
```

`TIME_OPERATOR` = `SUM` or `AVG` from `metric.time_operator`.

> **Current limitation**: `view_date` = `granular_date` (no date truncation applied).
> The `time` field in `view_config.aggregation` (`hour|day|week|month|year`) is loaded but
> not yet passed to the aggregator. See [ADR-007](../adr/007-consistency-check-strategy.md).

---

## Step 3 — Merge and write

Source: `writer.py:Writer.merge_results`

Scans all per-metric temporal aggregation parquet files, sinks them into a single
`results/view<timestamp>.parquet`, then deletes the intermediate parts.
Returns `None` if no metrics were processed.

**Intermediate files created and deleted per run:**

| Path | Lifetime |
|---|---|
| `views/intermediate/simulation_table_filtered.parquet` | Steps 1–2, deleted after loop |
| `views/metric_structure/<metric_id>.parquet` | Per-metric Step 2a–2b, deleted per metric |
| `views/metric_view/<metric_id>.parquet` | Per-metric Step 2b–2c, deleted per metric |
| `temporal_aggregation/<metric_id>-<n>.parquet` | Post-loop, deleted by Step 3 |
