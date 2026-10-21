# Simple setups

This example follows GVB through one run, on a small study built with the GEMS [basic models library](https://github.com/AntaresSimulatorTeam/GEMS/blob/main/libraries/basic_models_library.yml) and simulated with [GemsPy](https://github.com/AntaresSimulatorTeam/GemsPy). It explains what each GVB input file does in this study, and what GVB writes.

All the files are in [`docs/examples/simple_study`](https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/tree/main/docs/examples/simple_study) in the repository. Their formats are described in the [GEMS documentation](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/overview/).

## The study

One area, `area_1`, simulated for one week (168 hours) and 3 scenarios:

| Component | Model | Role |
|---|---|---|
| `area_1` | `bus` | the area: balances production and load |
| `load_1` | `load` | hourly demand, different in each scenario |
| `gen_base` | `generator` | 350 MW at 20 €/MWh |
| `gen_peak` | `generator` | 140 MW at 80 €/MWh |
| `storage_1` | `storage` | 400 MWh, 100 MW, 90 % charging efficiency |

```text
simple_study/
├── input/                          # GemsPy study
│   ├── model-libraries/basic_models_library.yml
│   ├── system.yml
│   ├── data-series/load_series.txt
│   └── optim-config.yml
├── taxonomy.yml                    # GVB inputs
├── catalogs/catalog.yml
├── calendar.csv
└── view-configs/
    ├── area_hourly.yml
    └── area_summary.yml
```

From the root of the GVB repository, install the environment, then run the simulation of the simple study with GemsPy:

```bash
uv sync
cd docs/examples/simple_study
uv run gemspy --study .
```

Outputs in the SimulationTable:

- `area_1`: `spillage`, `unsupplied_energy`
- `load_1`: `load`
- `gen_base`, `gen_peak`: `generation`
- `storage_1`: `level`, `p_injection`, `p_withdrawal`

## How GVB builds the Views

For each view config, GVB:

1. **gives each component a taxonomy category**, from the `taxonomy-category` of its model in the library;
2. **finds the location of each component** used by a metric: the component of the location category it is connected to;
3. **reads the outputs** named by the metric terms in the SimulationTable, and gives each time step its date from the calendar;
4. **combines the components** of each location with the `terms-operator`;
5. **aggregates** each metric to the time granularity of each aggregation pattern with the `time-operator`, then across scenarios if the pattern asks for it, and writes one View per pattern.

The sections below show which file drives each step.

## The library: taxonomy categories

The library is a copy of the basic models library, version 1.0.1, with two additions:

- each model used in the system declares a `taxonomy-category`: `bus` → `balance`, `generator` → `production`, `load` → `consumption`, `storage` → `storage` (step 1). Without it, GVB cannot use the component;
- the `load` model gets an extra-output `load`. In the basic library, `load` is only a parameter, and metrics can only read variables and extra-outputs.

```yaml
    - id: load
      taxonomy-category: consumption
      ...
      extra-outputs:
        - id: load
          expression: load
```

## Taxonomy

The [taxonomy](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/taxonomy/) declares, for each category, what the catalog may use: the `variables` and `extra-outputs` that metrics can read, and the `ports` through which a component reaches its location.

```yaml
--8<-- "docs/examples/simple_study/taxonomy.yml"
```

Each category matches one model. `consumption` has no variable, only the extra-output `load` added to the library.

## Catalog

The [catalog](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/catalog/) defines the metrics. Its `location` is the `balance` category, so every metric is located on `area_1`.

```yaml
--8<-- "docs/examples/simple_study/catalogs/catalog.yml"
```

| Metric | Reads | Location (step 2) | Time operator |
|---|---|---|---|
| `LOAD` | `load` of `consumption` components | through `balance_port` → `area_1` | `sum` |
| `PRODUCTION` | `generation` of `production` components | through `balance_port` → `area_1` | `sum` |
| `UNSUPPLIED_ENERGY` | `unsupplied_energy` of `balance` components | `null`: the area is its own location | `sum` |
| `STORAGE_LEVEL` | `level` of `storage` components | through `injection_port` → `area_1` | `avg` |

- `terms-operator: sum` adds the components of a location at each time step (step 4): `PRODUCTION` is `gen_base` plus `gen_peak`.
- `time-operator` aggregates over time (step 5). Energies are summed. A reservoir level is averaged, since a sum of hourly levels has no meaning.

## Calendar

The calendar gives a date to each time step (step 3): `absolute_time_index` 0 to 167, `block`, and `granular_date`, one hour apart from 2030-01-07 00:00.

```text
absolute_time_index,block,granular_date
0,0,2030-01-07 00:00:00
1,0,2030-01-07 01:00:00
2,0,2030-01-07 02:00:00
...
```

GemsPy solved the study in one block, `0`, so every calendar row has block `0`. GVB keeps a SimulationTable row only if both its time index and its block match a calendar row.

## View configs

A [view config](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/view-config/) selects metrics and says how to aggregate them (step 5). The study has two.

=== "area_hourly.yml"

    ```yaml
    --8<-- "docs/examples/simple_study/view-configs/area_hourly.yml"
    ```

    One pattern, `hourly`: every hour, every scenario.

=== "area_summary.yml"

    ```yaml
    --8<-- "docs/examples/simple_study/view-configs/area_summary.yml"
    ```

    Two patterns:

    - `daily`: one value per day and per scenario;
    - `weekly_stats`: one value for the week, with `scenario: true`. Instead of one row per scenario, the View gives statistics over the scenarios: expectation (`exp`), standard deviation (`std`, population formula), `min` and `max`.

## Run GVB

Both view configs are built in one run. The libraries and the system are the ones GemsPy used:

```bash
mkdir -p views
uv run gems-views-builder \
  --libraries-dir     input/model-libraries \
  --system            input/system.yml \
  --taxonomy          taxonomy.yml \
  --catalogs-dir      catalogs \
  --calendar          calendar.csv \
  --view-configs      "view-configs/*.yml" \
  --simulation-tables "output/<run id>/simulation_table_*.csv" \
  --output-dir        views
```

Replace `<run id>` with the folder GemsPy created, for example `20261021T0847`. The output folder must exist before the run.

GVB writes three Views in `views/`: one for `area_hourly`, and one for each pattern of `area_summary`. The options are described on the [Command line](../user-guide/command-line.md) page, and the columns of a View on the GEMS [Views](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/views/) page.

## The Views

### Hourly, scenario 2

`PRODUCTION` for the first 5 hours:

```python
import polars as pl

view = pl.read_parquet("views/area_hourly*.parquet")
print(view.filter(pl.col("metric_id") == "PRODUCTION", pl.col("scenario_id") == 2).sort("view_date").head())
```

```text
shape: (5, 8)
┌────────────┬────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ metric_id  ┆ metric_loc ┆ breakdown_ ┆ view_date ┆ scenario_ ┆ metric_va ┆ scenario_ ┆ scenario_ │
│ ---        ┆ ation      ┆ properties ┆ ---       ┆ id        ┆ lue       ┆ aggregati ┆ stat      │
│ str        ┆ ---        ┆ ---        ┆ datetime[ ┆ ---       ┆ ---       ┆ on        ┆ ---       │
│            ┆ str        ┆ str        ┆ μs]       ┆ i64       ┆ f64       ┆ ---       ┆ str       │
│            ┆            ┆            ┆           ┆           ┆           ┆ bool      ┆           │
╞════════════╪════════════╪════════════╪═══════════╪═══════════╪═══════════╪═══════════╪═══════════╡
│ PRODUCTION ┆ area_1     ┆ {}         ┆ 2030-01-0 ┆ 2         ┆ 350.0     ┆ false     ┆ null      │
│            ┆            ┆            ┆ 7         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ PRODUCTION ┆ area_1     ┆ {}         ┆ 2030-01-0 ┆ 2         ┆ 350.0     ┆ false     ┆ null      │
│            ┆            ┆            ┆ 7         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 01:00:00  ┆           ┆           ┆           ┆           │
│ PRODUCTION ┆ area_1     ┆ {}         ┆ 2030-01-0 ┆ 2         ┆ 350.0     ┆ false     ┆ null      │
│            ┆            ┆            ┆ 7         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 02:00:00  ┆           ┆           ┆           ┆           │
│ PRODUCTION ┆ area_1     ┆ {}         ┆ 2030-01-0 ┆ 2         ┆ 318.42222 ┆ false     ┆ null      │
│            ┆            ┆            ┆ 7         ┆           ┆ 2         ┆           ┆           │
│            ┆            ┆            ┆ 03:00:00  ┆           ┆           ┆           ┆           │
│ PRODUCTION ┆ area_1     ┆ {}         ┆ 2030-01-0 ┆ 2         ┆ 350.0     ┆ false     ┆ null      │
│            ┆            ┆            ┆ 7         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 04:00:00  ┆           ┆           ┆           ┆           │
└────────────┴────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

### Weekly statistics over the scenarios

| metric_id | exp | std | min | max |
|---|---|---|---|---|
| LOAD | 67863.2 | 3517.1 | 63866.4 | 72425.7 |
| PRODUCTION | 67676.2 | 2884.6 | 64177.5 | 71242.4 |
| UNSUPPLIED_ENERGY | 498.1 | 704.5 | 0.0 | 1494.4 |

Only scenario 2 has unsupplied energy: the `min` is 0 and the `max` is 1494.4 MWh. `STORAGE_LEVEL` is not in this view config.
