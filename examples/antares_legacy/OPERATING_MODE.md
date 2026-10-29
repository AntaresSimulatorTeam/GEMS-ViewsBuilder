# Operating mode

## Files

All the inputs of the ViewsBuilder are in `inputs/`. The library, the taxonomy and the catalogs are copied from
[AntaresLegacyModels-to-GEMS-Converter](https://github.com/AntaresSimulatorTeam/AntaresLegacyModels-to-GEMS-Converter).

| File | Content | Origin |
|---|---|---|
| `simulation_tables/simulation-table-<year>-optim-nb-2.parquet` | One SimulationTable per Monte Carlo year: the hourly value of each output of each component | Antares 10.2.0, run with `--output=simulation-tables --simulation-table-stages=optim-nb-2 --parquet` |
| `system-for-views.yml` | The components (id, model, properties) and their connections | Antares 10.2.0, written next to the simulation tables |
| `calendar.csv` | The date (`granular_date`, from 2030-01-01) and the week (`block`) of each time index (`absolute_time_index`) | Written for this example |
| `libraries/antares_legacy_models.yml` | The models of the components | Converter 0.5.0, library 2.2.0 (see below) |
| `antares_legacy_taxonomy_flattened.yml` | The categories of the models, with their outputs and properties | Converter `main` (see below) |
| `catalogs/antares_legacy_area_catalog.yml`, `catalogs/antares_legacy_link_catalog.yml` | The metrics: which outputs of which categories they combine, and how | Converter 0.5.0 |
| `view_config_area.yml`, `view_config_link.yml` | The views: locations (areas or links), time granularities, scenario aggregation and metrics | Written for this example |

The library and the taxonomy differ from the converter files in two ways:

- the taxonomy is the one of the converter `main` branch, where the `balance` category declares `binding-constraints`
  instead of `constraints`. Without this fix, gems-views-builder 0.1.0 rejects the `area` model of the library.
- the library is version 2.2.0, and the `name` property is removed from the `dispatchable_generation` and
  `short_term_storage` categories of the taxonomy. Library 2.2.1 and the taxonomy require a `name` property on `thermal`
  and `short_term_storage`, but Antares 10.2.0 does not export it in `system-for-views.yml`. No catalog uses it.

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

This builds both views in one run, and writes one file per view config and aggregation pattern in `output/`:

```text
output/
├── view_area--hourly_per_scenario--<timestamp>.csv
├── view_area--daily_all_scenario--<timestamp>.csv
├── view_link--hourly_per_scenario--<timestamp>.csv
└── view_link--daily_all_scenario--<timestamp>.csv
```

The log file is written in `logs/`. To build one view only, pass its view config, for example
`--view-configs inputs/view_config_area.yml`.

In Windows PowerShell, end the lines with `` ` `` instead of `\`.
