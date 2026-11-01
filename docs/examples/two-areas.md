# Two areas, from simulation to Views

This example uses GVB on a study with two areas and a link, and shows the GVB features that [Simple setups](simple-setups.md) does not use:

| Feature | Where |
|---|---|
| A location that groups several areas (the country), with `extra-locations` | [View configs](#view-configs) |
| The net import of each area through a link | [Catalogs](#catalogs) |
| Generation split by technology, with `breakdown`, and a single technology, with `filter` | [Catalogs](#catalogs) |
| Metrics located on the link instead of the areas | [Catalogs](#catalogs) |
| Monthly, weekly and yearly patterns, and a `location-filter` | [View configs](#view-configs) |

All the files are in [`docs/examples/two_areas`](https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder/tree/main/docs/examples/two_areas) in the repository. Their formats are described in the [GEMS documentation](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/overview/).

## The study

Two areas, `north` and `south`, of one country, `country_1`, joined by the link `north_south`. The study is built with the GEMS [Antares legacy library](https://github.com/AntaresSimulatorTeam/GEMS/blob/main/libraries/antares_legacy_models.yml) and simulated with [GemsPy](https://github.com/AntaresSimulatorTeam/GemsPy): two weeks (336 hours), 4 scenarios, synthetic data.

| Component | Model | Taxonomy category |
|---|---|---|
| `north`, `south` | `area` | `balance` |
| `load_north`, `load_south` | `load` | `fatal_consumption` |
| `nuclear_north`, `gas_south`, `oil_south` | `thermal` | `dispatchable_generation` |
| `wind_north`, `solar_south` | `renewable` | `renewable_fatal_generation` |
| `north_south` | `link` | `link` |

Files of the example (GVB does not expect any folder structure, each input is given by its own option):

```text
two_areas/
├── input/                              # GemsPy study
│   ├── model-libraries/antares_legacy_models.yml
│   ├── system.yml
│   ├── taxonomy.yml                    # read by GemsPy and GVB
│   ├── data-series/
│   └── optim-config.yml
├── catalogs/                           # GVB inputs
│   ├── area_catalog.yml
│   └── link_catalog.yml
├── calendar.csv
└── view-configs/
    ├── areas_hourly.yml
    ├── areas_summary.yml
    └── link_hourly.yml
```

## 1. Run GemsPy

From the root of the GVB repository, install the environment, then run the simulation of the two-area study with GemsPy:

```bash
uv sync
cd docs/examples/two_areas
uv run gemspy --study .
```

GemsPy writes the Simulation Table in `output/<run id>/simulation_table/`: one Parquet file per scenario, and `scenario-common.parquet` for the outputs that do not depend on the scenario.

## 2. GVB inputs

### System

GVB reads two things from the [system](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/system/):

- **connections**, to find the location of each component
- **properties**: `technology` of thermal and renewable units, used by `breakdown` and `filter`, and `country` of the areas, used by `extra-locations`

=== "Area"

    ```yaml
    --8<-- "docs/examples/two_areas/input/system.yml:area"
    ```

=== "Renewable"

    ```yaml
    --8<-- "docs/examples/two_areas/input/system.yml:renewable"
    ```

=== "Connections of the link"

    ```yaml
    --8<-- "docs/examples/two_areas/input/system.yml:link-connections"
    ```

### Taxonomy

The [taxonomy](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/taxonomy/) `antares_legacy_taxonomy`, in its flattened form, from the [Antares legacy converter](https://github.com/AntaresSimulatorTeam/AntaresLegacyModels-to-GEMS-Converter): each category lists all its outputs and ports itself, without `parent-category`. The categories of the components are given in [The study](#the-study).

??? example "taxonomy.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/input/taxonomy.yml"
    ```

### Calendar

The calendar gives a date to each time step. Its `block` must match the `block` of the Simulation Table:

```text
absolute_time_index,block,granular_date
0,0,2030-01-01 00:00:00
1,0,2030-01-01 01:00:00
…
335,0,2030-01-14 23:00:00
```

### Catalogs

Two [catalogs](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/catalog/): one for the areas, one for the link.

#### `area_catalog`: metrics located on the areas

??? example "area_catalog.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/catalogs/area_catalog.yml"
    ```

| Metric | Reads | Notes |
|---|---|---|
| `LOAD` | `actual_load` of the loads | |
| `GENERATION` | `generation_power` of thermal and renewable units | two terms, one per category |
| `GENERATION_BY_TECHNOLOGY` | same as `GENERATION` | `breakdown` on `technology` |
| `THERMAL_GENERATION` | `generation_power` of thermal units | |
| `GAS_GENERATION` | `generation_power` of thermal units | `filter` on `technology: gas` |
| `NET_IMPORT` | `flow` on `out_port`, `minus_flow` on `in_port` | one term per port of the link, read for the area on that port. Positive when the area imports |
| `UNSUPPLIED_ENERGY`, `SPILLED_ENERGY` | variables of the areas | `location-port: null` |
| `CO2_EMISSIONS` | `co2_emissions` of thermal units | t of CO₂ |

With these metrics, each area balances at every hour:

```text
LOAD = GENERATION + NET_IMPORT + UNSUPPLIED_ENERGY − SPILLED_ENERGY
```

#### `link_catalog`: metrics located on the link

??? example "link_catalog.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/catalogs/link_catalog.yml"
    ```

The link has two ports: `out_port` injects `flow` into the area connected to it (`south`), and `in_port` injects `-flow` (into `north`). A positive `flow` therefore goes from north to south.

| Metric | Reads | Notes |
|---|---|---|
| `FLOW` | `flow` | positive from north to south |
| `CONGESTED_HOURS` | `is_directly_congested`, `is_indirectly_congested` | number of hours at full capacity |

### View configs

Three [view configs](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/view-config/):

=== "areas_hourly.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/view-configs/areas_hourly.yml"
    ```

    - hourly balance of each area, per scenario
    - `extra-locations` adds `country_1`, from the `country` property of the areas

=== "areas_summary.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/view-configs/areas_summary.yml"
    ```

    - `monthly`: per month and per scenario
    - `yearly_stats`: statistics over the scenarios (`exp`, `std`, `min`, `max`)
    - `weekly_country_stats`: weekly statistics, `country_1` only (`location-filter`)

=== "link_hourly.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/view-configs/link_hourly.yml"
    ```

    - link metrics, hourly and as monthly statistics
    - location category `link`, so only the metrics of `link_catalog`

## 3. Run GVB

The three view configs, in one run:

```bash
mkdir -p views
uv run gems-views-builder \
  --libraries-dir     input/model-libraries \
  --system            input/system.yml \
  --taxonomy          input/taxonomy.yml \
  --catalogs-dir      catalogs \
  --calendar          calendar.csv \
  --view-configs      "view-configs/*.yml" \
  --simulation-tables "output/<run id>/simulation_table/scenario-*.parquet" \
  --output-dir        views
```

- Replace `<run id>` with the folder GemsPy created, for example `20261101T132927-9e71dc`.
- Each view config uses only the catalog of its location category.
- GVB writes six Views, one per aggregation pattern. Add `--output-format csv` for CSV files.

Each file is named `<view id>--<pattern id>--<timestamp>`:

```text
views/
├── areas_hourly--hourly--20261101T123629.parquet
├── areas_summary--monthly--20261101T123629.parquet
├── areas_summary--weekly_country_stats--20261101T123629.parquet
├── areas_summary--yearly_stats--20261101T123629.parquet
├── link_hourly--hourly--20261101T123629.parquet
└── link_hourly--monthly_stats--20261101T123629.parquet
```

!!! note "Run again"
    Each GVB run writes new files with a new timestamp, so after a second run the patterns below read both and every row appears twice. Empty `views/` before running GVB again, for example with `rm -rf views/*`. In the same way, each GemsPy run creates a new `output/<run id>/` folder: use the newest one in the GVB command.

## 4. Read the Views

### Hourly values and country total

Read the hourly View with polars, and print `LOAD` and `NET_IMPORT` of scenario 0 at 13:00 on 5 January, for the two areas and the country:

```python
import polars as pl
from datetime import datetime

view = pl.read_parquet("views/areas_hourly--hourly--*.parquet")
print(
    view.filter(
        pl.col("metric_id").is_in(["LOAD", "NET_IMPORT"]),
        pl.col("scenario_id") == 0,
        pl.col("view_date") == datetime(2030, 1, 5, 13),
    )
    .sort("metric_id", "metric_location")
    .select("metric_id", "metric_location", "metric_value")
)
```

```text
┌────────────┬─────────────────┬──────────────┐
│ metric_id  ┆ metric_location ┆ metric_value │
│ ---        ┆ ---             ┆ ---          │
│ str        ┆ str             ┆ f64          │
╞════════════╪═════════════════╪══════════════╡
│ LOAD       ┆ country_1       ┆ 5344.6       │
│ LOAD       ┆ north           ┆ 3002.0       │
│ LOAD       ┆ south           ┆ 2342.6       │
│ NET_IMPORT ┆ country_1       ┆ 0.0          │
│ NET_IMPORT ┆ north           ┆ -800.0       │
│ NET_IMPORT ┆ south           ┆ 800.0        │
└────────────┴─────────────────┴──────────────┘
```

- `country_1` comes from `extra-locations`: its value is the sum of `north` and `south`, for example `LOAD` 3002.0 + 2342.6 = 5344.6.
- Its `NET_IMPORT` is 0: the link is inside the country.

### The link

Same hour, from the link View:

```python
import polars as pl
from datetime import datetime

view = pl.read_parquet("views/link_hourly--hourly--*.parquet")
print(
    view.filter(
        pl.col("scenario_id") == 0,
        pl.col("view_date") == datetime(2030, 1, 5, 13),
    )
    .sort("metric_id")
    .select("metric_id", "metric_location", "metric_value")
)
```

```text
┌─────────────────┬─────────────────┬──────────────┐
│ metric_id       ┆ metric_location ┆ metric_value │
│ ---             ┆ ---             ┆ ---          │
│ str             ┆ str             ┆ f64          │
╞═════════════════╪═════════════════╪══════════════╡
│ CONGESTED_HOURS ┆ north_south     ┆ 1.0          │
│ FLOW            ┆ north_south     ┆ 800.0        │
└─────────────────┴─────────────────┴──────────────┘
```

The link is its own location (`location-port: null`), so `metric_location` is `north_south`.

### Generation by technology

January, scenario 3, `country_1`, from the `monthly` pattern:

```python
import polars as pl

view = pl.read_parquet("views/areas_summary--monthly--*.parquet")
print(
    view.filter(
        pl.col("metric_id") == "GENERATION_BY_TECHNOLOGY",
        pl.col("metric_location") == "country_1",
        pl.col("scenario_id") == 3,
    )
    .sort("breakdown_properties")
    .select("breakdown_properties", "metric_value")
)
```

```text
┌────────────────────────┬──────────────┐
│ breakdown_properties   ┆ metric_value │
│ ---                    ┆ ---          │
│ str                    ┆ f64          │
╞════════════════════════╪══════════════╡
│ {(technology,gas)}     ┆ 548061.4     │
│ {(technology,nuclear)} ┆ 885981.5     │
│ {(technology,oil)}     ┆ 4071.3       │
│ {(technology,solar)}   ┆ 29280.5      │
│ {(technology,wind)}    ┆ 139308.0     │
└────────────────────────┴──────────────┘
```

`breakdown` gives one row per value of `technology`, written in `breakdown_properties`.

### Statistics over the scenarios

Unsupplied energy of `country_1` over the two weeks, from the `yearly_stats` pattern:

```python
import polars as pl

view = pl.read_parquet("views/areas_summary--yearly_stats--*.parquet")
print(
    view.filter(
        pl.col("metric_id") == "UNSUPPLIED_ENERGY",
        pl.col("metric_location") == "country_1",
    )
    .sort("scenario_stat")
    .select("scenario_stat", "metric_value")
)
```

```text
┌───────────────┬──────────────┐
│ scenario_stat ┆ metric_value │
│ ---           ┆ ---          │
│ str           ┆ f64          │
╞═══════════════╪══════════════╡
│ exp           ┆ 39.05        │
│ max           ┆ 156.2        │
│ min           ┆ 0.0          │
│ std           ┆ 67.636584    │
└───────────────┴──────────────┘
```

One row per statistic, in `scenario_stat`. In these rows, `scenario_id` is empty and `scenario_aggregation` is `true`.

### Weekly statistics for the country

Expected load of `country_1` per week, from the `weekly_country_stats` pattern (`location-filter` keeps `country_1` only):

```python
import polars as pl

view = pl.read_parquet("views/areas_summary--weekly_country_stats--*.parquet")
print(
    view.filter(pl.col("metric_id") == "LOAD", pl.col("scenario_stat") == "exp")
    .sort("view_date")
    .select("view_date", "metric_location", "metric_value")
)
```

```text
┌─────────────────────┬─────────────────┬──────────────┐
│ view_date           ┆ metric_location ┆ metric_value │
│ ---                 ┆ ---             ┆ ---          │
│ datetime[μs]        ┆ str             ┆ f64          │
╞═════════════════════╪═════════════════╪══════════════╡
│ 2029-12-31 00:00:00 ┆ country_1       ┆ 655704.525   │
│ 2030-01-07 00:00:00 ┆ country_1       ┆ 773642.875   │
│ 2030-01-14 00:00:00 ┆ country_1       ┆ 114142.075   │
└─────────────────────┴─────────────────┴──────────────┘
```

!!! note "`view_date` is the start of the period"
    Monthly and yearly values are dated `2030-01-01` and cover the 14 days of the calendar. Weekly values are dated the Monday of their week, even when the calendar covers only part of it: `2029-12-31` holds 1 to 6 January, `2030-01-07` a full week, and `2030-01-14` only 14 January.
