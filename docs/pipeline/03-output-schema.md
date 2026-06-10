# Output Schema — View

The pipeline produces a single parquet file at `results/view<timestamp>.parquet`.

---

## Schema

| Column | Type | Nullable | Description |
|---|---|---|---|
| `metric_id` | string | no | Metric identifier as declared in the catalog |
| `metric_location` | string | no | Location component id(s), always wrapped in `{…}` |
| `breakdown_properties` | string | no | Property pairs in declaration order, or `{}` if no breakdown |
| `view_date` | datetime | yes | Date for this row (= `granular_date` from the calendar; no truncation currently) |
| `scenario` | int64 | yes | Scenario index from the simulation table |
| `metric_value` | float64 | yes | Aggregated value after `terms_operator` and `time_operator` |

---

## Column semantics

### `metric_location`

Always formatted as `{<id>}` or `{<id1>,<id2>}`, including for single-location metrics.

| Case | Example value |
|---|---|
| `location-ports: null` (self-location) | `{generator_A1}` |
| `location-ports: balance_port` | `{busA}` |
| `location-ports: [p0_port, p1_port]` | `{busA,busB}` |

### `breakdown_properties`

Pairs are formatted as `(key,value)` and ordered by the catalog `breakdown` key list —
not by `system.yml` property declaration order.

| Case | Example value |
|---|---|
| No breakdown defined | `{}` |
| `breakdown: [{key: technology}]` | `{(technology,nuclear)}` |
| `breakdown: [{key: technology}, {key: company}]` | `{(technology,nuclear),(company,rhonepower)}` |
| Component missing a breakdown key | `{(technology,None)}` |

### `view_date`

Currently equals the raw `granular_date` from the calendar, so each unique date from the
calendar appears as its own row. The `time` field in `view_config.aggregation`
(`hour|day|week|month|year`) is not yet applied. For non-time-dependent rows,
`view_date` is null.

### `scenario`

Copied from `scenario_index` in the simulation table. Null for scenario-independent outputs.

---

## Example output

System: two buses (`busA`, `busB`), generators and a link.
Metric: `PROD` (total production per bus, hourly, sum).

| metric_id | metric_location | breakdown_properties | view_date | scenario | metric_value |
|---|---|---|---|---|---|
| PROD | {busA} | {} | 2025-01-01T00:00:00 | 0 | 48.0 |
| PROD | {busA} | {} | 2025-01-01T01:00:00 | 0 | 36.0 |
| PROD | {busB} | {} | 2025-01-01T00:00:00 | 0 | 100.0 |

Metric: `PRODUCTION_BY_TECH` (production split by technology).

| metric_id | metric_location | breakdown_properties | view_date | scenario | metric_value |
|---|---|---|---|---|---|
| PRODUCTION_BY_TECH | {area} | {(technology,nuclear)} | 2025-01-01T00:00:00 | 0 | 500.0 |
| PRODUCTION_BY_TECH | {area} | {(technology,gas)} | 2025-01-01T00:00:00 | 0 | 250.0 |

---

## One row per unique key

The output has one row per unique combination of:

```
(metric_id, metric_location, breakdown_properties, view_date, scenario)
```

Within that key, values from multiple components (same term) are aggregated by
`terms_operator`, and values from multiple timesteps within the same `view_date` bucket
are aggregated by `time_operator`.

---

## Output file path

```
<input_data_path>/results/view<YYYYMMDDTHHmmss>.parquet
```

Timestamp is UTC. Multiple runs produce separate files (no overwrite).
