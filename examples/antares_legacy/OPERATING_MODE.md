# Operating mode

## Files

All the inputs of the ViewsBuilder are in `inputs/`. The library, the taxonomy and the catalogs are copied from
[AntaresLegacyModels-to-GEMS-Converter](https://github.com/AntaresSimulatorTeam/AntaresLegacyModels-to-GEMS-Converter).

| File | Content | Origin |
|---|---|---|
| `simulation_tables/simulation-table-<year>-optim-nb-2.parquet` | One SimulationTable per Monte Carlo year: the hourly value of each output of each component | Antares 10.2.0, run with `--output=simulation-tables --simulation-table-stages=optim-nb-2 --parquet` |
| `system-for-views.yml` | The components (id, model, properties) and their connections | Antares 10.2.0, written next to the simulation tables, completed (see below) |
| `calendar.csv` | The date (`granular_date`, from 2030-01-01) and the week (`block`) of each time index (`absolute_time_index`) | Written for this example |
| `libraries/antares_legacy_models.yml` | The models of the components | Converter `main`, library 2.3.0 |
| `antares_legacy_taxonomy_flattened.yml` | The categories of the models, with their outputs and properties | Converter `main` |
| `catalogs/antares_legacy_<area, link, thermal_cluster, renewable_cluster, short_term_storage>_catalog.yml` | The metrics: which outputs of which categories they combine, and how | Converter `main` |
| `view_config_<area, link, thermal, renewable, sts>.yml` | The views: locations, time granularities, scenario aggregation and metrics | Written for this example, from the converter view configs |

The library, the taxonomy and the catalogs are the files of the converter `main` branch, unchanged.

The view configs keep the location category and the taxonomy of the converter view configs, and fill their
aggregation patterns. The area and link views keep a selection of metrics, the thermal, renewable and storage views all
the metrics of their catalog. These three views break down their metrics per cluster `name`, in each area.

Library 2.3.0 requires properties that Antares 10.2.0 does not write in `system-for-views.yml`, so the file is
completed with the values the converter gives them:

- `name` on the `thermal`, `renewable` and `short_term_storage` components: the cluster name (`ccgt`, `solar_pv`,
  `battery`…), or `wind`, `solar` and `run_of_river` for the aggregated renewable components.
- `technology` instead of `group` on the `short_term_storage` components, with the same value (`battery`).

The views are written in `output/`.

## Installation

The example runs with **gems-views-builder 0.1.0**, published on PyPI (Python 3.11 or later). Install it with pip,
in a virtual environment:

```bash
pip install gems-views-builder==0.1.0
```

or with uv:

```bash
uv tool install gems-views-builder==0.1.0
```

It also runs with the `main` branch of this repository: run `uv sync` at the repository root, then replace
`gems-views-builder` with `uv run gems-views-builder` in the CLI call below.

## CLI call

From `examples/antares_legacy`:

```bash
gems-views-builder \
  --system            inputs/system-for-views.yml \
  --libraries-dir     inputs/libraries \
  --taxonomy          inputs/antares_legacy_taxonomy_flattened.yml \
  --catalogs-dir      inputs/catalogs \
  --calendar          inputs/calendar.csv \
  --simulation-tables "inputs/simulation_tables/simulation-table-*-optim-nb-2.parquet" \
  --view-configs      "inputs/view_config_*.yml" \
  --output-dir        output \
  --output-format     csv
```

This builds the 5 views in one run, and writes one file per view config and aggregation pattern in `output/`:

```text
output/
├── view_area--hourly_per_scenario--<timestamp>.csv
├── view_area--daily_all_scenario--<timestamp>.csv
├── view_link--hourly_per_scenario--<timestamp>.csv
├── view_link--daily_all_scenario--<timestamp>.csv
├── view_thermal--hourly_per_scenario--<timestamp>.csv
├── view_thermal--daily_all_scenario--<timestamp>.csv
├── view_renewable--hourly_per_scenario--<timestamp>.csv
├── view_renewable--daily_all_scenario--<timestamp>.csv
├── view_storage--hourly_per_scenario--<timestamp>.csv
└── view_storage--daily_all_scenario--<timestamp>.csv
```

The log file is written in `logs/`. To build one view only, pass its view config, for example
`--view-configs inputs/view_config_area.yml`.

In Windows PowerShell, end the lines with `` ` `` instead of `\`.
