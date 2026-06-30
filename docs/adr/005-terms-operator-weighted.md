# ADR-005 — Weighted terms operator

**Status**: Planned, not yet implemented

## Context

`terms-operator` and `time-operator` currently support `sum` and `avg`.
The formal spec (PDF2) also defines `weighted_sum` and `weighted_avg`, where each
component's value is multiplied by a weight before aggregation.

The weight is specified per term via `weight-output-id`: another output-id from the same
component, read from the simulation table.

## Current state

- `TermsOperator` and `TimeOperator` enums (`catalog.py`) have `SUM` and `AVG` only.
- `Term.weight_output_id` field exists in the data model but is set to `1` (integer) in
  `MetricStructureBuilder.build()` and never used in `Aggregator`.
- The `weight_output_id` column in `_METRIC_STRUCTURE_SCHEMA` is `Int64` (constant `1`).

## Work needed

1. Add `WEIGHTED_SUM` and `WEIGHTED_AVG` to both enums.
2. In `MetricStructureBuilder.build()`: store the actual `term.weight_output_id` string.
3. In `Aggregator.aggregate_metric_terms()`: for weighted operators, join the weight output
   from the simulation table and multiply `value * weight` before aggregating.
4. Validate that `weight_output_id` is a valid output-id for the term's taxonomy category
   (same rule as `output-id`).
