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
│   ├── data-series/
│   └── optim-config.yml
├── taxonomy.yml                        # GVB inputs
├── catalogs/
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

GemsPy writes the SimulationTable to `output/<run id>/simulation_table_<run id>.csv`.

## 2. GVB inputs

### System

GVB reads two things from the [system](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/system/):

- **connections**, to find the location of each component;
- **properties**: `technology` of thermal and renewable units, used by `breakdown` and `filter`, and `country` of the areas, used by `extra-locations`.

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
    --8<-- "docs/examples/two_areas/taxonomy.yml"
    ```

### Calendar

The calendar gives a date to each time step. Its `block` must match the `block` of the SimulationTable:

```text
absolute_time_index,block,granular_date
0,0,2030-01-25 00:00:00
1,0,2030-01-25 01:00:00
…
335,0,2030-02-07 23:00:00
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
| `NET_IMPORT` | `flow` on `out_port`, `minus_flow` on `in_port` | one term per port of the link; positive when the area imports |
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

    - hourly balance of each area, per scenario;
    - `extra-locations` adds `country_1`, from the `country` property of the areas.

=== "areas_summary.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/view-configs/areas_summary.yml"
    ```

    - `monthly`: per month and per scenario;
    - `yearly_stats`: statistics over the scenarios (`exp`, `std`, `min`, `max`);
    - `weekly_country_stats`: weekly statistics, `country_1` only (`location-filter`).

=== "link_hourly.yml"

    ```yaml
    --8<-- "docs/examples/two_areas/view-configs/link_hourly.yml"
    ```

    - link metrics, hourly and as monthly statistics;
    - location category `link`, so only the metrics of `link_catalog`.

## 3. Run GVB

The three view configs, in one run:

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

- Replace `<run id>` with the folder GemsPy created, for example `20261022T0925`.
- Each view config uses only the catalog of its location category.
- GVB writes six Views, one per aggregation pattern. Add `--output-format csv` for CSV files.

## 4. Read the Views

Energies are in MWh.

### Hourly balance and country total

Read the hourly View with polars, and print `LOAD` and `NET_IMPORT` of scenario 0 at 13:00 on 29 January, for the two areas and the country:

```python
import polars as pl
from datetime import datetime

view = pl.read_parquet("views/areas_hourly*.parquet")
print(view.filter(
    pl.col("metric_id").is_in(["LOAD", "NET_IMPORT"]),
    pl.col("scenario_id") == 0,
    pl.col("view_date") == datetime(2030, 1, 29, 13),
).sort("metric_id", "metric_location"))
```

```text
┌────────────┬────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ metric_id  ┆ metric_loc ┆ breakdown_ ┆ view_date ┆ scenario_ ┆ metric_va ┆ scenario_ ┆ scenario_ │
│ ---        ┆ ation      ┆ properties ┆ ---       ┆ id        ┆ lue       ┆ aggregati ┆ stat      │
│ str        ┆ ---        ┆ ---        ┆ datetime[ ┆ ---       ┆ ---       ┆ on        ┆ ---       │
│            ┆ str        ┆ str        ┆ μs]       ┆ i64       ┆ f64       ┆ ---       ┆ str       │
│            ┆            ┆            ┆           ┆           ┆           ┆ bool      ┆           │
╞════════════╪════════════╪════════════╪═══════════╪═══════════╪═══════════╪═══════════╪═══════════╡
│ LOAD       ┆ country_1  ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 5344.6    ┆ false     ┆ null      │
│            ┆            ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
│ LOAD       ┆ north      ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 3002.0    ┆ false     ┆ null      │
│            ┆            ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
│ LOAD       ┆ south      ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 2342.6    ┆ false     ┆ null      │
│            ┆            ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
│ NET_IMPORT ┆ country_1  ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 0.0       ┆ false     ┆ null      │
│            ┆            ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
│ NET_IMPORT ┆ north      ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ -800.0    ┆ false     ┆ null      │
│            ┆            ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
│ NET_IMPORT ┆ south      ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 800.0     ┆ false     ┆ null      │
│            ┆            ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
└────────────┴────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

- `country_1` comes from `extra-locations`: its value is the sum of `north` and `south`, for example `LOAD` 3002.0 + 2342.6 = 5344.6.
- Its `NET_IMPORT` is 0: the link is inside the country.

### The link

Same hour, from the link View:

```python
import polars as pl
from datetime import datetime

view = pl.read_parquet("views/link_hourly*.parquet")
print(view.filter(
    pl.col("scenario_id") == 0,
    pl.col("view_date") == datetime(2030, 1, 29, 13),
).sort("metric_id"))
```

```text
┌────────────┬────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ metric_id  ┆ metric_loc ┆ breakdown_ ┆ view_date ┆ scenario_ ┆ metric_va ┆ scenario_ ┆ scenario_ │
│ ---        ┆ ation      ┆ properties ┆ ---       ┆ id        ┆ lue       ┆ aggregati ┆ stat      │
│ str        ┆ ---        ┆ ---        ┆ datetime[ ┆ ---       ┆ ---       ┆ on        ┆ ---       │
│            ┆ str        ┆ str        ┆ μs]       ┆ i64       ┆ f64       ┆ ---       ┆ str       │
│            ┆            ┆            ┆           ┆           ┆           ┆ bool      ┆           │
╞════════════╪════════════╪════════════╪═══════════╪═══════════╪═══════════╪═══════════╪═══════════╡
│ CONGESTED_ ┆ north_sout ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 1.0       ┆ false     ┆ null      │
│ HOURS      ┆ h          ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
│ FLOW       ┆ north_sout ┆ {}         ┆ 2030-01-2 ┆ 0         ┆ 800.0     ┆ false     ┆ null      │
│            ┆ h          ┆            ┆ 9         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 13:00:00  ┆           ┆           ┆           ┆           │
└────────────┴────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

The link is its own location (`location-port: null`), so `metric_location` is `north_south`.

### Generation by technology

February, scenario 3, `country_1`, from the `monthly` pattern:

```python
import polars as pl
from datetime import datetime

view = pl.read_parquet("views/areas_summary*.parquet")
print(view.filter(
    pl.col("metric_id") == "GENERATION_BY_TECHNOLOGY",
    pl.col("metric_location") == "country_1",
    pl.col("scenario_id") == 3,
    pl.col("view_date") == datetime(2030, 2, 1),
).sort("breakdown_properties"))
```

```text
┌────────────┬────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ metric_id  ┆ metric_loc ┆ breakdown_ ┆ view_date ┆ scenario_ ┆ metric_va ┆ scenario_ ┆ scenario_ │
│ ---        ┆ ation      ┆ properties ┆ ---       ┆ id        ┆ lue       ┆ aggregati ┆ stat      │
│ str        ┆ ---        ┆ ---        ┆ datetime[ ┆ ---       ┆ ---       ┆ on        ┆ ---       │
│            ┆ str        ┆ str        ┆ μs]       ┆ i64       ┆ f64       ┆ ---       ┆ str       │
│            ┆            ┆            ┆           ┆           ┆           ┆ bool      ┆           │
╞════════════╪════════════╪════════════╪═══════════╪═══════════╪═══════════╪═══════════╪═══════════╡
│ GENERATION ┆ country_1  ┆ {(technolo ┆ 2030-02-0 ┆ 3         ┆ 286195.6  ┆ false     ┆ null      │
│ _BY_TECHNO ┆            ┆ gy,gas)}   ┆ 1         ┆           ┆           ┆           ┆           │
│ LOGY       ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ GENERATION ┆ country_1  ┆ {(technolo ┆ 2030-02-0 ┆ 3         ┆ 450039.5  ┆ false     ┆ null      │
│ _BY_TECHNO ┆            ┆ gy,nuclear ┆ 1         ┆           ┆           ┆           ┆           │
│ LOGY       ┆            ┆ )}         ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ GENERATION ┆ country_1  ┆ {(technolo ┆ 2030-02-0 ┆ 3         ┆ 2385.0    ┆ false     ┆ null      │
│ _BY_TECHNO ┆            ┆ gy,oil)}   ┆ 1         ┆           ┆           ┆           ┆           │
│ LOGY       ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ GENERATION ┆ country_1  ┆ {(technolo ┆ 2030-02-0 ┆ 3         ┆ 14586.8   ┆ false     ┆ null      │
│ _BY_TECHNO ┆            ┆ gy,solar)} ┆ 1         ┆           ┆           ┆           ┆           │
│ LOGY       ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ GENERATION ┆ country_1  ┆ {(technolo ┆ 2030-02-0 ┆ 3         ┆ 61929.8   ┆ false     ┆ null      │
│ _BY_TECHNO ┆            ┆ gy,wind)}  ┆ 1         ┆           ┆           ┆           ┆           │
│ LOGY       ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
└────────────┴────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

`breakdown` gives one row per value of `technology`, written in `breakdown_properties`.

### Statistics over the scenarios

Unsupplied energy of `country_1` over the two weeks, from the `yearly_stats` pattern:

```python
import polars as pl
from datetime import datetime

view = pl.read_parquet("views/areas_summary*.parquet")
print(view.filter(
    pl.col("metric_id") == "UNSUPPLIED_ENERGY",
    pl.col("metric_location") == "country_1",
    pl.col("view_date") == datetime(2030, 1, 1),
    pl.col("scenario_aggregation"),
).sort("scenario_stat"))
```

```text
┌────────────┬────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ metric_id  ┆ metric_loc ┆ breakdown_ ┆ view_date ┆ scenario_ ┆ metric_va ┆ scenario_ ┆ scenario_ │
│ ---        ┆ ation      ┆ properties ┆ ---       ┆ id        ┆ lue       ┆ aggregati ┆ stat      │
│ str        ┆ ---        ┆ ---        ┆ datetime[ ┆ ---       ┆ ---       ┆ on        ┆ ---       │
│            ┆ str        ┆ str        ┆ μs]       ┆ i64       ┆ f64       ┆ ---       ┆ str       │
│            ┆            ┆            ┆           ┆           ┆           ┆ bool      ┆           │
╞════════════╪════════════╪════════════╪═══════════╪═══════════╪═══════════╪═══════════╪═══════════╡
│ UNSUPPLIED ┆ country_1  ┆ {}         ┆ 2030-01-0 ┆ null      ┆ 39.05     ┆ true      ┆ exp       │
│ _ENERGY    ┆            ┆            ┆ 1         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ UNSUPPLIED ┆ country_1  ┆ {}         ┆ 2030-01-0 ┆ null      ┆ 156.2     ┆ true      ┆ max       │
│ _ENERGY    ┆            ┆            ┆ 1         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ UNSUPPLIED ┆ country_1  ┆ {}         ┆ 2030-01-0 ┆ null      ┆ 0.0       ┆ true      ┆ min       │
│ _ENERGY    ┆            ┆            ┆ 1         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
│ UNSUPPLIED ┆ country_1  ┆ {}         ┆ 2030-01-0 ┆ null      ┆ 67.636584 ┆ true      ┆ std       │
│ _ENERGY    ┆            ┆            ┆ 1         ┆           ┆           ┆           ┆           │
│            ┆            ┆            ┆ 00:00:00  ┆           ┆           ┆           ┆           │
└────────────┴────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

One row per statistic, in `scenario_stat`; `scenario_id` is empty and `scenario_aggregation` is `true`.

!!! note "Periods are cut by date"
    `view_date` is the start of the period: `2030-01-01` for January and for the year, even though the calendar starts on 25 January. Weeks start on Monday.

## Next steps

- Add an area with another `country` value, to get a second country total.
- Add a `breakdown` on `name` to see each thermal cluster.
- The rules GVB checks on these files are listed on the [Validation rules](../user-guide/validation-rules.md) page.
