# Operating mode: from an Antares legacy study to views

How to build views of your own Antares legacy study, as done in this example.

## 1. Run Antares (10.2.0 or later)

```bash
antares-solver <study> --output=simulation-tables --simulation-table-stages=optim-nb-2 --parquet
```

- `--output=simulation-tables` writes the simulation tables (they are not written by default; `--output=all`
  also keeps the usual `mc-ind` / `mc-all` results).
- `--simulation-table-stages=optim-nb-2` keeps the final optimisation pass only. Use `optim-nb-1` when
  `unit-commitment-mode = milp` (no second pass), and `peak-shaving` or `adq-patch` if the study uses the hydro
  remix or the adequacy patch.
- `--parquet` keeps the tables small (in this example, 69 MB per MC year in CSV, 1.7 MB in parquet).

`<study>/output/<run>/` then holds, for the ViewsBuilder:

- `simulation-table-<year>-<stage>.parquet`: one SimulationTable per MC year;
- `system-for-views.yml`: the system, with the ids of the legacy components.

## 2. Gather the business inputs

From [AntaresLegacyModels-to-GEMS-Converter](https://github.com/AntaresSimulatorTeam/AntaresLegacyModels-to-GEMS-Converter) (`src/antares_gems_converter/`):

| Input | Where | Note |
|---|---|---|
| Library | `libs/antares_historic/antares_legacy_models.yml` | Use 2.2.0 with Antares 10.2.0: 2.2.1 requires a `name` property that Antares does not export |
| Taxonomy | `taxonomies/antares_legacy_taxonomy_flattened.yml` | The flattened one: the ViewsBuilder does not resolve parent categories |
| Catalogs | `catalogs/` | One per location type: area, link, thermal cluster, short-term storage |
| View config templates | `views_config/` | Fill `aggregations-patterns` and `metrics` |

## 3. Write the calendar

`calendar.csv` maps each time index of the simulation tables to a date:

| Column | Value |
|---|---|
| `absolute_time_index` | 0 to 8735 (52 weeks of 168 hours) |
| `block` | `absolute_time_index // 168`: Antares solves one week per block |
| `granular_date` | Hourly dates from the study's first day (e.g. `2030-01-01 00:00:00`) |

## 4. Write a view config per view

- `scope.location.taxonomy-category`: `balance` for areas, `link` for links.
- `aggregations-patterns`: `time-granularity` among `hour`, `day`, `week`, `month`, `year`; `scenario: false` keeps
  one row per MC year, `scenario: true` aggregates them (`exp`, `std`, `min`, `max`).
- `metrics`: `<catalog id>.<metric id>`, taken from the catalogs.

## 5. Build the views

Gather the inputs of steps 1 to 4 in one folder, as `inputs/` in this example, then:

```bash
gems-views-builder --system inputs/system-for-views.yml --libraries-dir inputs/libraries \
  --taxonomy inputs/antares_legacy_taxonomy_flattened.yml --catalogs-dir inputs/catalogs \
  --calendar inputs/calendar.csv --simulation-tables "inputs/simulation_tables/simulation-table-*-optim-nb-2.parquet" \
  --view-config inputs/view_config_area.yml --output output/area --output-format csv
```

Quote the `--simulation-tables` pattern: the ViewsBuilder expands it itself, on every OS.
The output folder must exist. It receives one file per time granularity, `view_<granularity>_<timestamp>.csv`,
whose name does not tell the view apart: use one output folder per view.

## 6. Read the views

| Column | Meaning |
|---|---|
| `metric_id`, `metric_location` | Metric and location (area node, link…) |
| `breakdown_properties` | Breakdown key and value, e.g. `{(technology,gas)}` |
| `view_date` | First date of the time step |
| `scenario_id` | MC year, when scenarios are not aggregated |
| `scenario_stat` | `exp`, `std`, `min` or `max`, when they are |
| `metric_value` | Value |

Components that Antares declares but that have no data in the simulation tables can give rows with no date and a
value of 0 (here, the `wind`, `solar` and `run_of_river` breakdowns of `RES_GENERATION`: renewables are modelled
as clusters).
