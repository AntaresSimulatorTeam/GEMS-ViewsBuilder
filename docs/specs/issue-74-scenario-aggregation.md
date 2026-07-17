# Spec: Scenario aggregation (#74)

## Context

Today, a View's output keeps one row per `scenario` all the way through the
pipeline: `TermsAggregator` renames `scenario_index` to `scenario`, and
`TimeAggregator` (the temporal aggregation step) groups by
`metric_id, metric_location, breakdown_properties, scenario, view_date`
without ever collapsing the scenario dimension.

Issue #74 asks for an optional final step — run after temporal aggregation —
that collapses the scenario dimension into four synthesis statistics per
group: expectation (`exp`), standard deviation (`std`), minimum (`min`) and
maximum (`max`).

As part of this change, the View's `scenario` column is renamed to
**`scenario_id`** — a plain rename, independent of the aggregation feature
itself, done for clarity now that this column sits alongside the new
`scenario_aggregation` / `scenario_stat` columns (see "Output schema" and
"Column rename" below).

## Config schema

`Aggregation` gains a plain `scenario: bool | None = None` field, keeping the
flat YAML shape from the issue's own draft — no wrapper type, no extra
keyword:

```python
class Aggregation(ViewBuilderBasedModel):
    time: TimeAggregation | None = None
    scenario: bool | None = None
```

YAML shape (one aggregation dimension per list entry, matching the existing
convention):

```yaml
aggregation:
  - time: hour
  - scenario: true # (or false)
```

`ViewConfig` gains `scenario_aggregation: bool = False`.

`load_view_config()` currently only inspects `aggregation[0]` — harmless
today since only one entry is ever used, but this feature requires two
entries in the same list, so this needs fixing to scan the whole list:

```python
time_aggregation = next((a.time for a in raw.aggregation if a.time is not None), None)
scenario_aggregation = next((a.scenario for a in raw.aggregation if a.scenario is not None), False)
```

**Forward-looking note:** a future issue will allow *several* time and
scenario aggregation levels in one View (e.g. hourly + daily, or partial +
full scenario synthesis). This spec keeps `scenario_aggregation` a single
scalar for now — that's confirmed as the right scope for this iteration —
but the list-based `aggregation` shape above is chosen deliberately so that
extending it later (more entries, or richer per-entry config) doesn't
require renaming these fields again.

## Pipeline changes

New `ScenarioAggregator` (mirrors `TimeAggregator`'s shape), inserted after
`TimeAggregator.run()` in `ViewBuilder.build()`:

```python
metric_view = terms_aggregator.run(metric_structure_table, metric)
temporal_metric_view = time_aggregator.run(metric_view, metric)
final_metric_view = scenario_aggregator.run(temporal_metric_view, config.scenario_aggregation)
```

New `ScenarioOperator` enum (`gems_views_builder/input/catalog.py`, alongside
`TermsOperator` / `TimeOperator`), values chosen to be written directly into
the `scenario_stat` column via `.value`:

```python
class ScenarioOperator(Enum):
    EXP = "exp"
    STD = "std"
    MIN = "min"
    MAX = "max"
```

- When `scenario_aggregation = True`: group by
  `metric_id, metric_location, breakdown_properties, view_date` (dropping
  `scenario_id`), and emit one row per `ScenarioOperator` — mean / std
  (ddof=0, see below) / min / max of `metric_value` — unpivoted into long
  form (4 rows per group).
- When `scenario_aggregation = False`: pass through unchanged (aside from
  the column rename below).

## Column rename: `scenario` → `scenario_id`

Renamed in `TermsAggregator` (currently
`.with_columns(pl.col("scenario_index").alias("scenario"))` in
`terms_aggregator.py`) to alias to `scenario_id` instead, and correspondingly
in every downstream groupby/select in `TimeAggregator` and the new
`ScenarioAggregator`. Existing tests referencing the `scenario` column
(`test_time_aggregator.py`, `test_filtering_and_breakdown.py`,
`test_view_builder.py`) need updating to `scenario_id`. This is a breaking
change for any external consumer reading View output by column name.

## Output schema

```
metric_id | metric_location | breakdown_properties | view_date | scenario_id | scenario_aggregation | scenario_stat | metric_value
```

Two new columns, present in **every** View's output regardless of config, so
the schema stays uniform across all Views:

- **`scenario_aggregation` (Boolean, non-nullable)** — constant across every
  row of a given View's output, mirroring the View-level
  `aggregation: - scenario: true|false` config. Lets a consumer tell how the
  file was produced without checking the config that generated it.
- **`scenario_stat` (Utf8, nullable)** — `null` when
  `scenario_aggregation = false`; one of `"exp" | "std" | "min" | "max"` when
  `scenario_aggregation = true`.

`scenario_id` (Int64) keeps its current meaning and dtype in both cases —
populated with the scenario index when `scenario_aggregation = false`, `null`
when `true` (a synthesis row no longer corresponds to a single scenario).
This avoids retyping `scenario_id` depending on config, which was the
original concern raised on this issue (reusing it as a string column
would make its dtype flip between `Int64` and `Utf8` depending on config —
a footgun for any downstream consumer with a fixed schema expectation).

| scenario_aggregation | scenario_id | scenario_stat | meaning |
|---|---|---|---|
| `false` | `3` | `null` | ordinary per-scenario row (today's behavior) |
| `true` | `null` | `"std"` | synthesis row, one of 4 per group |

## Std convention

Population standard deviation, `ddof=0` — always defined (0 for a
single-scenario View), no null/NaN edge case to special-case downstream.

## Edge cases

- Single-scenario View with `scenario_aggregation = true`: `exp = min = max
  = value`, `std = 0` (per `ddof=0` above).
- `scenario_aggregation` is set once per View (from the `aggregation` block)
  and applies uniformly to every metric/row in that View's output — not
  configurable per-metric, for now (see forward-looking note above).

## Documentation fixes bundled with this change

Several `catalog.yml` fixtures carry a column-order comment
(`# metric_id | metric_location | breakdown_property | view_date |
scenario_id | metric_value |`). It already says `scenario_id`, so the
rename above actually makes that part of the comment correct — but
`breakdown_property` is still singular where the real column is
`breakdown_properties`, and the comment needs the two new columns added.
Update while touching this area:

- `resources/tests_inputs/test_3/catalogs/catalog.yml`
- `resources/tests_inputs/filtering_and_breakdown/catalogs/catalog.yml`
- (any other fixture carrying the same comment)

## Testing plan

- Unit test for `ScenarioAggregator`, following `tests/test_time_aggregator.py`'s
  `make_metric_view` pattern (synthetic multi-scenario parquet fixture).
- E2E test extending `tests/test_filtering_and_breakdown.py` (fixture already
  has 10 scenarios, ids 0-9) — mirror its
  `_expected_generation_total_by_scenario` pattern to assert `exp` / `std`
  (ddof=0) / `min` / `max` against values computed directly from the raw
  simulation table.
- Regression test confirming `scenario_aggregation = false` (or omitted)
  leaves output unchanged (aside from the `scenario` → `scenario_id` rename
  and the two new columns: `scenario_aggregation = false` on every row,
  `scenario_stat = null`).
- `load_view_config()` test covering a two-entry `aggregation` list
  (`time` + `scenario` together), to lock in the list-scanning fix.
- Sweep of existing tests asserting on the `scenario` column
  (`test_time_aggregator.py`, `test_filtering_and_breakdown.py`,
  `test_view_builder.py`) updated to `scenario_id`.
