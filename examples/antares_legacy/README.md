# Example: views of an Antares legacy study

A fictitious Antares legacy study: two areas (`fr`, `be`) joined by a link, with load, thermal and renewable
clusters and a battery, simulated hourly over one year (52 weeks) for 2 Monte Carlo years.

| Input | File |
|---|---|
| SimulationTables (Antares 10.2.0, one per MC year) | `simulation_tables/*.parquet` |
| System (exported by Antares 10.2.0 next to the simulation tables) | `system-for-views.yml` |
| Calendar (from 2030-01-01, one block per week) | `calendar.csv` |
| Catalogs and taxonomy (copied from [AntaresLegacyModels-to-GEMS-Converter](https://github.com/AntaresSimulatorTeam/AntaresLegacyModels-to-GEMS-Converter) 0.5.0) | `catalogs/`, `antares_legacy_taxonomy_flattened.yml` |
| Library (antares_legacy_models 2.2.0: 2.2.1 adds a `name` property that Antares 10.2.0 does not export) | `libraries/` |
| View configs (hourly per scenario, daily over all scenarios) | `view_config_area.yml`, `view_config_link.yml` |

## Run

From this directory, with `gems-views-builder` installed:

```bash
mkdir -p output/area
gems-views-builder \
  --system system-for-views.yml \
  --libraries-dir libraries \
  --taxonomy antares_legacy_taxonomy_flattened.yml \
  --catalogs-dir catalogs \
  --calendar calendar.csv \
  --simulation-tables "simulation_tables/simulation-table-*-optim-nb-2.parquet" \
  --view-config view_config_area.yml \
  --output output/area \
  --output-format csv
```

This writes `view_hour_<timestamp>.csv` and `view_day_<timestamp>.csv` in `output/area`.
In Windows PowerShell, end the lines with `` ` `` instead of `\` and create the folder with `mkdir output/area`.

`python run_example.py` builds both the area and link views, on any OS.

## Regenerate the inputs

`generate_inputs.py` builds the study with antares-craft, runs
`antares-solver --output=simulation-tables --simulation-table-stages=optim-nb-2 --parquet`
and writes `simulation_tables/`, `system-for-views.yml` and `calendar.csv`:

```bash
python generate_inputs.py path/to/antares-10.2.0-Ubuntu-22.04/bin/antares-solver  # Windows: antares-10.2.0-win64/bin/antares-solver.exe
```
