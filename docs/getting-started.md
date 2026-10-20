# Getting started

This page takes you from installation to a first View, on your own GEMS study.

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

### 1. Prepare your inputs

GVB reads a GEMS study and the results of its simulation. Put them in one folder, for example:

```text
my_study/
├── system.yml            # the GEMS system
├── taxonomy.yml          # the taxonomy of the models
├── calendar.csv          # time index → date
├── libraries/            # the model libraries used by the system (.yml)
├── catalogs/             # the catalogs, which define the metrics (.yml)
├── views/                # the view configs (.yml)
└── output/               # the simulation results
    ├── st-x-mc-1.parquet
    └── st-x-mc-2.parquet
```

The formats of these files are described in the GEMS documentation: [system](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/system/), [taxonomy](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/taxonomy/), [library](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/library/), [catalog](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/catalog/), [view config](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/view-config/) and [SimulationTable](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/simulation-table/).

The view configs say which Views to build. An example is given on the GEMS [view config](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/view-config/) page. In this page, the view config has the id `view_area` and one aggregation pattern, `hourly`.

### 2. Run GVB

Create an output folder, then run:

```bash
mkdir -p views_out

gems-views-builder \
  --system            my_study/system.yml \
  --libraries-dir     my_study/libraries \
  --taxonomy          my_study/taxonomy.yml \
  --catalogs-dir      my_study/catalogs \
  --view-configs      "my_study/views/*.yml" \
  --calendar          my_study/calendar.csv \
  --simulation-tables "my_study/output/st-x-mc-*.parquet" \
  --output-dir        views_out
```

Each option points to one file, folder or pattern of the study. All options are described on the [Command line](user-guide/command-line.md) page.

!!! tip "Quote the patterns"
    Write patterns such as `"my_study/output/st-x-mc-*.parquet"` in quotes, so that GVB expands them and not your shell.

The run ends with:

```text
INFO - View successfully written to views_out
```

### 3. Look at the result

GVB writes the Views in `views_out`, and a log file in `logs`:

```text
views_out/
└── view_area_hourly_20261019T141953.parquet
logs/
└── gems-views-builder-pipeline-run-2026-10-19-14-19-53-072136Z.log
```

Open the View with any Parquet reader, for example Polars:

```python
import polars as pl

view = pl.read_parquet("views_out/view_area_hourly_*.parquet")
print(view.sort("metric_id", "metric_location", "view_date").head())
```

The first rows look like this (example values):

| metric_id | metric_location | breakdown_properties | view_date | scenario_id | metric_value | scenario_aggregation | scenario_stat |
|---|---|---|---|---|---|---|---|
| LOAD | area_1 | {} | 2025-01-01 00:00:00 | 0 | 102.0 | false | null |
| LOAD | area_1 | {} | 2025-01-01 01:00:00 | 0 | 98.0 | false | null |
| LOAD | area_1 | {} | 2025-01-01 02:00:00 | 0 | 95.0 | false | null |
| LOAD | area_1 | {} | 2025-01-01 03:00:00 | 0 | 93.0 | false | null |

Each row is one metric, at one location, at one date, for one scenario. The columns are described on the GEMS [Views](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/views/) page.

To get CSV instead of Parquet, add `--output-format csv`.

## When a run fails

GVB stops at the first problem it finds. The message, printed in the terminal and written to the log file in `logs/`, names the file and the rule that failed. The exit codes are listed on the [Command line](user-guide/command-line.md) page.

Add `--verbose` to get debug messages. The rules GVB checks are listed on the [Validation rules](user-guide/validation-rules.md) page.

## Next steps

- [User guide](user-guide/command-line.md): every option, the rules GVB checks, and the supported versions.
- [Examples](examples/simple-setups.md): more view configs, scenario statistics and several SimulationTables.
