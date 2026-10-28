# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-10-27

### Added

- One run can load several view configs and write a view for each of them.
- Catalogs, libraries are collected from directories. Simulation tables are collected from a glob, and every table in that glob must use the same extension.
- Each simulation table is checked for the expected columns before views are built.

### Changed

- A view config no longer lists its catalogs. The catalogs it uses are the ones named by its metrics (`<catalog_id>.<metric_id>`). Catalogs remain CLI args.
- A view config no longer has a `calendar` field. Calendar remains a CLI arg.
- `--output` is now `--output-dir`.
- Parquet/CSV files are exported one per view config and aggregation pattern (`<view_config_id>--<aggregation_pattern_id>--<timestamp>.parquet`).
- `spatial_filter` in a view config is now `location_filter`.
- Time aggregation is computed once per granularity, including when both scenario settings use that granularity.

## [0.0.1] - 2026-09-21

### Added

- First release of the GEMS Views builder.

[0.1.0]: https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/releases/tag/v0.0.1
