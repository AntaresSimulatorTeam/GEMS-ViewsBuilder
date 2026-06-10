# ADR-002 — Filter cardinality: exactly 0 or 1

**Status**: Decided

## Decision

A metric `filter` is a single `(key, value)` pair, cardinality 0 or 1.
Multiple filter conditions are not supported.

## Rationale

A filter is an exclusion criterion: "only components where `properties[key] == value`
contribute". Supporting multiple conditions would require AND/OR semantics, which hasn't
been designed. Since the primary need is simple type-based filtering (e.g. `technology=nuclear`)
a single condition covers most cases.

`breakdown` is the separate concept: it *groups* by a key without restricting which
components contribute.

## Constraint in code

`MetricData.validate_filter` (`catalog.py`) raises `ValueError` if `filter.value is None`,
ensuring the value field is always present when a filter is declared.

## Source

aoustry PR #51, PR #35.
