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

> **Gap**: tuple `location-ports` values (multi-port) are not iterated; only string values
> are checked.

### Calendar (`load_calendar` → `_check_calendar_columns`)

Source: `calendar.py`

| Check | Error raised |
|---|---|
| File exists | `FileNotFoundError` |
| File extension is `.csv` | `ValueError` |
| Columns are `[absolute_time_index, block, granular_date]` in that exact order | `ValueError` |
| `absolute_time_index` is contiguous `0, 1, …, N-1` | `ValueError` |
| Spacing between consecutive `granular_date` values is constant | `ValueError` |

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

## Checks not yet implemented

The following rules are defined (see [`input-data/05-consistency-rules.md`](../input-data/05-consistency-rules.md))
but have no corresponding code check today:

| Rule | Status |
|---|---|
| `term.output-id` is a valid variable/port-field-def/extra-output for the term's taxonomy-category models | ❌ not implemented |
| `view_config.scope.taxonomy-category` matches `catalog.location.taxonomy-category` | ❌ not implemented |
| Peer component resolved via location port belongs to `catalog.location.taxonomy-category` | ❌ not implemented |
| Calendar covers all `absolute_time_index` values in simulation table | ❌ silent (inner join drops unmatched rows) |

---

## Execution-time checks

Run inside the per-metric loop during `ViewBuilder.build()`.

| Check | When | Source | Error raised |
|---|---|---|---|
| Each named location port resolves to exactly 1 peer | Step 2a, per `(component, port)` | `system.py:InputSystem._get_peer_components` | `ValueError` |
| Named port has at least one connection | same | same | `ValueError` |

These checks run at execution time because they depend on the system graph, which requires
the library to be loaded and resolved. With a fail-fast strategy (see ADR-007), they could
run upfront as a dry-validation pass before any computation.

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
  └─ per-metric loop
       └─ system.get_location()             ← uniqueness check (execution time)
```
