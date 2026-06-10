# ADR-007 — Consistency check strategy

**Status**: Open — no explicit strategy exists today

## Context

Consistency checks are currently scattered across four locations with no governing principle:

| Check | Location | Phase |
|---|---|---|
| File layout | `StudyLayoutValidator` | Startup |
| Calendar columns and ordering | `calendar.py:_check_calendar_columns` | Load time |
| SimulationTable column set | `simulation_table.py:_check_simulation_table_columns` | Load time |
| Catalog ↔ taxonomy (partial) | `catalog_taxonomy_validator.py` | Startup, after load |
| Location port uniqueness | `system.py:_get_peer_components` | Execution time, per metric |

## Coverage gaps

The following rules (defined in [`input-data/05-consistency-rules.md`](../input-data/05-consistency-rules.md))
have **no code enforcement** today:

| Rule | Impact if violated |
|---|---|
| `term.output-id` is a valid variable/port-field-def/extra-output for its taxonomy category | Wrong or empty metric output (no error) |
| `view_config.taxonomy-category` matches `catalog.location.taxonomy-category` | Location resolution may use wrong components |
| Peer component belongs to `catalog.location.taxonomy-category` | Location points to a non-location component |
| Calendar covers all simulation table timesteps | Mismatched timesteps silently dropped |

## Open design questions

### 1. Fail-fast vs. lazy

Should all cross-file consistency checks run before any pipeline computation begins?

**Arguments for fail-fast:**
- A consistent set of inputs is a precondition for meaningful output. Running 3 hours of
  computation only to fail on a config error wastes time.
- All required data is already loaded (`Loader.load` runs before `validate_catalogs_against_taxonomy`).

**Arguments for lazy:**
- Some checks (e.g. location resolution) require iterating the full system, which may be
  expensive for large studies.
- A partial result with a warning may be more useful than a hard failure for exploratory runs.

### 2. Ownership

Where should each check live? Current options:
- Keep each check co-located with the code that needs the constraint (current approach).
- Introduce a dedicated `validate(loader)` function in `validation/` that runs all checks
  in a defined order after loading.

A dedicated validator would make the check sequence explicit and testable as a unit.

### 3. Error quality

Current checks raise `ValueError` or `FileNotFoundError` with varying message formats.
No distinction between user configuration errors and internal programmer errors.
A structured approach would use custom exception types (e.g. `StudyConfigError`) for
user-facing validation failures, reserving `AssertionError` for internal invariants.

## Recommendation

Adopt fail-fast: all cross-file consistency checks should run in `ViewBuilder.__init__()`
after `Loader.load()`, in cheapest-to-most-expensive order:

```
1. Layout check        (file existence, O(1))
2. Calendar format     (already at load time — keep there)
3. SimulationTable     (already at load time — keep there)
4. Catalog ↔ taxonomy  (already at startup — keep, extend to cover output-id)
5. view_config ↔ catalog location category  (add, O(catalogs))
6. Peer category check  (add, O(components × terms))
```

Execution-time checks (uniqueness) become assertions — if inputs are valid, uniqueness is
guaranteed by construction.
