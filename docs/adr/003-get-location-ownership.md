# ADR-003 — Ownership of `get_location` and peer category check

**Status**: Open

## Context

`get_location(component_id, location_port)` currently lives in `InputSystem` (`system.py`).
It calls `_get_peer_components` and enforces the uniqueness constraint (exactly one peer).

Two operations are bundled in `InputSystem`:
1. **Graph traversal** — `_get_peer_components`: general-purpose, returns all connected peers
   for a `(component, port)` pair.
2. **Business rule** — uniqueness enforcement + (future) peer category check: these are
   metric-building semantics, not general system semantics.

## Open question

Should `get_location` move to `MetricStructureBuilder` (`metrics_builder.py`)?

**Arguments for moving:**
- The uniqueness constraint ("exactly one peer") and the peer-category check (ADR-001)
  are catalogue-level business rules, not system-graph invariants.
- `InputSystem` would expose only `_get_peer_components` (no constraint), keeping it
  reusable for other purposes.
- The business validation code would be co-located with `MetricStructureBuilder.build()`.

**Arguments for keeping in `InputSystem`:**
- The current callers are only metric builders; moving prematurely adds abstraction.
- `InputSystem` already holds the connection index; putting location resolution there
  is natural.

## Current state

`get_location` lives in `InputSystem`. The peer category check (ADR-001) is not yet
implemented in either location.

## Source

aoustry PR #51.
