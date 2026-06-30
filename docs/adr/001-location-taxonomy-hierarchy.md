# ADR-001 — Peer location category check

**Status**: Open

## Context

When `LOCATING_FUNCTION` resolves a location for a component via a port, the peer component
it finds should belong to `catalog.location.taxonomy-category` (e.g. `balance`). This ensures
the resolved location is actually a location component, not an accidental peer of a different type.

## Current behaviour

No category check is performed on the resolved peer. Any peer connected through the named port
is accepted as the location, regardless of its taxonomy category.

## Intended behaviour

After resolving the peer via `_get_peer_components`, verify:

```
system.library.get_taxonomy_category(peer.model) == catalog.location_taxonomy_category
```

If not, raise `ValueError`.

## Open question

The peer check interacts with taxonomy hierarchy: if `balance` has subcategories (e.g.
`regional_balance` with `parent-category: balance`), should a peer of category
`regional_balance` be accepted as a valid location? The intent (from aoustry PR #51) is
yes — the check should accept the category itself and all subcategories. This requires
implementing the taxonomy partial-order walk (see [ADR-006](006-taxonomy-partial-order.md)).

## Impact

Missing this check means a misconfigured `location-ports` that points to a non-location
peer silently produces wrong output rather than a clear error.
