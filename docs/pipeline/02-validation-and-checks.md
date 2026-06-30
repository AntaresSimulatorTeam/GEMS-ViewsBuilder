# Validation & Consistency Checks

This page documents **how** consistency rules are enforced in code: which function runs each
check, when it runs, and what error is raised. For the logical rules themselves, see
[`input-data/05-consistency-rules.md`](../input-data/05-consistency-rules.md).

The current implementation has no explicit strategy — checks are scattered across several
functions and run at different phases. See [ADR-007](../adr/007-consistency-check-strategy.md).

---

## Parsing-time checks

Run once at startup in `ViewBuilder.__init__()` before any pipeline step.

### Study layout (`StudyLayoutValidator.validate`)

Source: `validation/study_layout_validator.py`

| Check | Error raised |
|---|---|
| `input_data_path` exists and is a directory | `NotADirectoryError` |
| `catalogs/` subdirectory exists and is non-empty | `NotADirectoryError` / `FileNotFoundError` |
| Each of `taxonomy.yml`, `view_config.yml`, `library.yml`, `system.yml` is present | `FileNotFoundError` |
| Exactly one file matching `calendar*.csv` exists | `FileNotFoundError` (none) / `ValueError` (multiple) |
| That file has `.csv` extension | `ValueError` |
| Exactly one file matching `simulation_table*.parquet` exists | `FileNotFoundError` / `ValueError` |
| That file has `.parquet` extension | `ValueError` |

### Catalog ↔ taxonomy (`validate_catalogs_against_taxonomy`)

Source: `validation/catalog_taxonomy_validator.py`

| Check | Error raised |
|---|---|
| `catalog.taxonomy == taxonomy.id` | `ValueError` |
| Every `term.taxonomy-category` is in `taxonomy.categories[*].id` | `ValueError` |
| Every string `term.location-ports` is in the ports of `term.taxonomy-category` | `ValueError` |

> **Bug**: tuple `location-ports` values (multi-port) trigger a false `ValueError` — the
> tuple is compared against the set of string port ids and never matches, so any multi-port
> term would incorrectly fail validation.

### SimulationTable (`SimulationTable.load` → `_check_simulation_table_columns`)

Source: `simulation_table.py`

| Check | Error raised |
|---|---|
| File extension is `.parquet` | `ValueError` |
| All 8 required columns are present (no missing, no extra) | `ValueError` |

### ViewConfig (`ViewConfig.load_into_self`)

Source: `metrics.py`

| Check | Error raised |
|---|---|
| `view_config.yml` contains a `view` root key | `ValueError` |
| At least one `scope` entry has `taxonomy-category` | `ValueError` |
| Each `metrics[*].id` is in `<catalog>.<metric>` format (not starting or ending with `.`) | `ValueError` |

---

## Step 1 checks (during `build()`)

These run when the calendar is loaded at the start of `ViewBuilder.build()`.
`load_calendar()` is called from `build()`, **not** from `Loader.load()`.

### Calendar (`view_config.load_calendar()` → `calendar.py:_check_calendar_columns`)

| Check | Error raised |
|---|---|
| Calendar file exists | `FileNotFoundError` |
| File extension is `.csv` | `ValueError` |
| Columns are `[absolute_time_index, block, granular_date]` in that exact order | `ValueError` |
| `absolute_time_index` is contiguous `0, 1, …, N-1` | `ValueError` |
| Spacing between consecutive `granular_date` values is constant | `ValueError` |

---

## Checks not yet implemented

The following rules are defined (see [`input-data/05-consistency-rules.md`](../input-data/05-consistency-rules.md))
but have no corresponding code check today:

| Rule | Status |
|---|---|
| `term.output-id` is a valid variable/port-field-def/extra-output for the term's taxonomy-category models | ❌ not implemented |
| `view_config.scope.taxonomy-category` matches `catalog.location.taxonomy-category` | ❌ not implemented |
| Location port connects to exactly 1 peer (uniqueness — multiple peers currently silently merged) | ❌ not implemented |
| Peer component resolved via location port belongs to `catalog.location.taxonomy-category` | ❌ not implemented |
| Calendar covers all `absolute_time_index` values in simulation table | ❌ silent (inner join drops unmatched rows) |

---

## Execution-time checks

Run inside the per-metric loop during `ViewBuilder.build()`.

| Check | When | Source | Error raised |
|---|---|---|---|
| Named port has at least 1 connection | Step 2a, per `(component, port)` | `system.py:InputSystem._get_peer_components` | `ValueError` |

> **Multiple peers**: if a port connects to several components, all peers are merged into
> `metric_location` as `{peer1,peer2,...}`. This is the current behaviour; enforcing
> uniqueness is planned (see [ADR-003](../adr/003-get-location-ownership.md)).

---

## Where things currently stand

```
ViewBuilder.__init__()
  ├─ StudyLayoutValidator.validate()         ← file layout only
  ├─ Loader.load()
  │    ├─ load_taxonomy()                    ← no cross-checks
  │    ├─ ViewConfig.load()                  ← format checks only
  │    ├─ load_catalogs()                    ← no cross-checks
  │    ├─ SimulationTable.load()             ← column presence
  │    ├─ ModelLibrary.load()                ← no cross-checks
  │    └─ InputSystem.load()                 ← no cross-checks
  └─ validate_catalogs_against_taxonomy()    ← catalog ↔ taxonomy (partial)

ViewBuilder.build()
  ├─ Step 1: view_config.load_calendar()    ← calendar format + column checks
  └─ per-metric loop
       └─ system.get_location()             ← 0-peer check only; multiple peers silently merged
```
