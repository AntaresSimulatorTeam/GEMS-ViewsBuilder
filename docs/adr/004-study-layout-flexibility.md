# ADR-004 — Study layout flexibility

**Status**: Open

## Context

`StudyLayoutValidator` enforces a strict layout:
- Exact filenames for 4 files (`taxonomy.yml`, `view_config.yml`, `library.yml`, `system.yml`).
- Exactly one file matching `calendar*.csv` (any name with `.csv` extension).
- Exactly one file matching `simulation_table*.parquet`.
- A `catalogs/` subdirectory with at least one file.

## Open question

This strict layout was chosen for simplicity at the current stage. Future needs may include:
- Multiple library files.
- User-controlled filenames for `taxonomy.yml` or `system.yml`.
- Multiple calendar files (per scenario set or per simulation block).
- Multiple simulation tables (partial outputs merged at load time).

## Current state

The validator (`study_layout_validator.py`) is implemented as a standalone class with clear
separation between each check. It can be extended without touching `ViewBuilder`.

The wildcard matching for `calendar*` and `simulation_table*` already provides some
flexibility (any suffix after the prefix). Full flexibility requires a more explicit
configuration mechanism (e.g. a path manifest in `view_config.yml`).

## Source

aoustry PR #50.
