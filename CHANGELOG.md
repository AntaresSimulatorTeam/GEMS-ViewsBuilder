# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-27

### Added

- One run can load several view configs and write a view for each of them.
- Catalogs, libraries, and view configs are collected from directories. Simulation tables are collected from a glob, and every table in that glob must use the same extension.
- Each simulation table is checked for the expected columns before views are built.

### Changed

- A view config no longer lists its catalogs. The catalogs it uses are the ones named by its metrics (`<catalog_id>.<metric_id>`).
- `--output` is now `--output-dir`.
- `spatial_filter` in a view config is now `location_filter`.
- Time aggregation is computed once per granularity, including when both scenario settings use that granularity.

## [0.0.1] - 2026-09-21

### Added

- First release of the GEMS Views builder.

[0.1.0]: https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/releases/tag/v0.0.1
