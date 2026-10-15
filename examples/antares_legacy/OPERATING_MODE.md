# Operating mode

## Files

All the inputs of the ViewsBuilder are in `inputs/`. The library, the taxonomy and the catalogs are copied from
[AntaresLegacyModels-to-GEMS-Converter](https://github.com/AntaresSimulatorTeam/AntaresLegacyModels-to-GEMS-Converter) 0.5.0.

| File | Content | Origin |
|---|---|---|
| `simulation_tables/simulation-table-<year>-optim-nb-2.parquet` | One SimulationTable per Monte Carlo year: the hourly value of each output of each component | Antares 10.2.0, run with `--output=simulation-tables --simulation-table-stages=optim-nb-2 --parquet` |
| `system-for-views.yml` | The components (id, model, properties) and their connections | Antares 10.2.0, written next to the simulation tables |
| `calendar.csv` | The date (`granular_date`, from 2030-01-01) and the week (`block`) of each time index (`absolute_time_index`) | Written for this example |
| `libraries/antares_legacy_models.yml` | The models of the components | Converter, library 2.2.0: 2.2.1 adds a `name` property that Antares 10.2.0 does not export |
| `antares_legacy_taxonomy_flattened.yml` | The categories of the models, with their outputs and properties | Converter |
| `catalogs/antares_legacy_area_catalog.yml`, `catalogs/antares_legacy_link_catalog.yml` | The metrics: which outputs of which categories they combine, and how | Converter |
| `view_config_area.yml`, `view_config_link.yml` | The views: locations (areas or links), time granularities, scenario aggregation and metrics | Written for this example |

The views are written in `output/area/` and `output/link/`.

## CLI call

From `examples/antares_legacy`, with the ViewsBuilder installed (`uv sync` at the root of the repository):

```bash
gems-views-builder \
  --system inputs/system-for-views.yml \
  --libraries-dir inputs/libraries \
  --taxonomy inputs/antares_legacy_taxonomy_flattened.yml \
  --catalogs inputs/catalogs/antares_legacy_area_catalog.yml \
  --calendar inputs/calendar.csv \
  --simulation-tables "inputs/simulation_tables/simulation-table-*-optim-nb-2.parquet" \
  --view-config inputs/view_config_area.yml \
  --output output/area \
  --output-format csv
```

This writes one file per time granularity of the view config in `output/area/`: `view_hour_<timestamp>.csv` and
`view_day_<timestamp>.csv`. For the link view, use `--catalogs inputs/catalogs/antares_legacy_link_catalog.yml
--view-config inputs/view_config_link.yml --output output/link`.

`--catalogs` takes the catalogs of the view's location only: the ViewsBuilder rejects a catalog located elsewhere,
such as the link catalog for the area view.

In Windows PowerShell, end the lines with `` ` `` instead of `\`.
