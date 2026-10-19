# Getting started

This page takes you from installation to a first View, using a small study shipped with the GVB repository.

## Requirements

- **Python 3.11 or later.** The supported versions are listed on the [Compatibility](user-guide/compatibility.md) page.
- **GemsPy** is installed automatically with GVB, at the version GVB is pinned to. You do not need to install it separately.

## Install

=== "pip"

    ```bash
    pip install gems-views-builder
    ```

=== "From the repository (uv)"

    ```bash
    git clone https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder.git
    cd GEMS-ViewsBuilder
    uv sync
    ```

    With uv, prefix the commands on this page with `uv run`, for example `uv run gems-views-builder --help`.

## Check the install

```bash
gems-views-builder --help
```

The command prints the list of options. If your shell does not find `gems-views-builder`, check that the Python environment where you installed it is active.

## First run

### 1. Get the example study

The GVB repository contains a small study in `resources/tests_inputs/test_3`: two buses (`busA`, `busB`), one day at hourly resolution, one scenario. If you installed GVB with pip, clone the repository to get it:

```bash
git clone https://github.com/AntaresSimulatorTeam/GEMS-ViewsBuilder.git
cd GEMS-ViewsBuilder
```

The study contains:

```text
resources/tests_inputs/test_3/
├── system.yml                       # the GEMS system
├── libraries/
│   └── library.yml                  # the model library used by the system
├── taxonomy.yml                     # categories of the models
├── catalogs/
│   └── catalog.yml                  # metric definitions (one or more catalogs)
├── view_config.yml                  # which metrics, which location, which aggregation
├── calendar_file.csv                # time index → date
└── simulation_table--20260318-0623.parquet   # the simulation results
```

The [view config](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/view-config/) asks for three metrics, `PROD`, `LOAD` and `BALANCE`, per bus (taxonomy category `balance`), at hourly resolution, for each scenario:

```yaml
view:
  id: view_area
  taxonomy: my_taxonomy
  scope:
    location:
      taxonomy-category: balance
    calendar: calendar_file
  aggregations-patterns:
    - id: hourly
      time_granularity: hour
      scenario: false
  metrics:
    - id: catalog.PROD
    - id: catalog.LOAD
    - id: catalog.BALANCE
```

### 2. Run GVB

Create an output folder, then run:

```bash
mkdir -p results

gems-views-builder \
  --system            resources/tests_inputs/test_3/system.yml \
  --libraries-dir     resources/tests_inputs/test_3/libraries \
  --taxonomy          resources/tests_inputs/test_3/taxonomy.yml \
  --catalogs-dir      resources/tests_inputs/test_3/catalogs \
  --view-configs      resources/tests_inputs/test_3/view_config.yml \
  --calendar          resources/tests_inputs/test_3/calendar_file.csv \
  --simulation-tables "resources/tests_inputs/test_3/simulation_table*.parquet" \
  --output            results
```

| Option | What to give |
|---|---|
| `--system` | The GEMS system file of the study. |
| `--libraries-dir` | The folder with the model libraries the system uses. It may contain only `.yml` files. |
| `--taxonomy` | The taxonomy file. |
| `--catalogs-dir` | The folder with the catalogs. It may contain only `.yml` files. |
| `--view-configs` | One view config file, or a pattern matching several (for example `"views/*.yml"`). GVB builds the Views of each one in the same run. |
| `--calendar` | The calendar file. |
| `--simulation-tables` | One SimulationTable file, or a pattern matching several (for example one file per Monte Carlo batch). |
| `--output` | An existing folder where the Views are written. |

!!! tip "Quote the patterns"
    Put patterns such as `"simulation_table*.parquet"` in quotes, so that GVB expands them and not your shell. A pattern may point to the current folder, for example `"st-*.parquet"`.

The run ends with:

```text
INFO - View successfully written to results
```

### 3. Look at the result

GVB writes one View file per view config and aggregation pattern, named `<view id>_<aggregation-pattern id>_<timestamp>`. Here the view config `view_area` has one pattern, `hourly`, so there is one file, plus a log file in `logs/`:

```text
results/
└── view_area_hourly_20261019T141953.parquet
logs/
└── gems-views-builder-pipeline-run-2026-10-19-14-19-53-072136Z.log
```

Open the View with any Parquet reader, for example Polars:

```python
import polars as pl

view = pl.read_parquet("results/view_area_hourly_*.parquet")
print(view.sort("metric_id", "metric_location", "view_date").head())
```

| metric_id | metric_location | breakdown_properties | view_date | scenario_id | metric_value | scenario_aggregation | scenario_stat |
|---|---|---|---|---|---|---|---|
| BALANCE | busA | {} | 2025-01-01 00:00:00 | 0 | 98.0 | false | null |
| BALANCE | busA | {} | 2025-01-01 01:00:00 | 0 | 96.0 | false | null |
| BALANCE | busA | {} | 2025-01-01 02:00:00 | 0 | 94.0 | false | null |
| BALANCE | busA | {} | 2025-01-01 03:00:00 | 0 | 92.0 | false | null |

Each row is one metric, at one location, at one date, for one scenario. The columns are described on the GEMS [Views](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/views/) page.

To get CSV instead of Parquet, add `--output-format csv`.

## When a run fails

GVB stops at the first problem and returns an exit code:

| Exit code | Meaning | Where to look |
|---|---|---|
| `0` | The Views were written. | — |
| `1` | The options were fine, but an input file is invalid or inconsistent with another, or view building failed. | The log file in `logs/` (or in the folder given with `--log-dir`) names the file and the rule that failed. |
| `2` | An option is missing, or a path does not exist. | The message printed in the terminal. |

Add `--verbose` to get debug messages in the terminal. The rules GVB checks are listed on the [Validation rules](user-guide/validation-rules.md) page.

## Next steps

- [Examples](examples/simple-setups.md): more view configs, scenario statistics and several SimulationTables.
- [Command line](user-guide/command-line.md): every option in detail.
