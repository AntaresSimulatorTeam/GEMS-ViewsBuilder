# Command line

GVB is run with one command, `gems-views-builder`. It reads a GEMS study and its simulation results, checks them, and writes the [Views](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/views/) asked for by the view configs.

```text
gems-views-builder --libraries-dir DIR --catalogs-dir DIR
                   --system FILE --taxonomy FILE --calendar FILE
                   --view-configs PATTERN --simulation-tables PATTERN
                   -o DIR [-f {parquet,csv}] [-l DIR] [-v]
```

`python -m gems_views_builder` runs the same command.

## Example

```bash
gems-views-builder \
  --libraries-dir     study/libraries \
  --catalogs-dir      study/catalogs \
  --system            study/system.yml \
  --taxonomy          study/taxonomy.yml \
  --calendar          study/calendar.csv \
  --view-configs      "study/views/*.yml" \
  --simulation-tables "output/st-x-mc-*.parquet" \
  --output-dir        views
```

## Options

### Inputs

All input options are required.

| Option | Value | Description |
|---|---|---|
| `--libraries-dir` | folder | Folder of [model library](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/library/) files. It must contain only `.yml` files; all of them are loaded. |
| `--catalogs-dir` | folder | Folder of [catalog](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/catalog/) files. It must contain only `.yml` files; all of them are loaded. |
| `--system` | file | [System](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/system/) file (`.yml`). |
| `--taxonomy` | file | [Taxonomy](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/taxonomy/) file (`.yml`). |
| `--calendar` | file | Calendar file (`.csv`). |
| `--view-configs` | pattern | One [view config](https://gems-energy.readthedocs.io/en/latest/user-guide/input-files/view-config/) file (`.yml`), or a pattern matching several, for example `"views/*.yml"`. All of them are built in the same run. |
| `--simulation-tables` | pattern | Pattern for the [SimulationTable](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/simulation-table/) files (all `.parquet` or all `.csv`), for example `"output/st-x-mc-*.parquet"`. |

### Output and logs

| Option | Value | Default | Description |
|---|---|---|---|
| `-o`, `--output-dir` | folder | — (required) | Existing folder where the [Views](https://gems-energy.readthedocs.io/en/latest/user-guide/outputs/views/) are written. |
| `-f`, `--output-format` | `parquet` or `csv` | `parquet` | Format of the View files. |
| `-l`, `--log-dir` | folder | `logs` in the current folder | Folder where the log file is written. |
| `-v`, `--verbose` | — | off | Adds debug messages to the terminal and the log file. |
| `-h`, `--help` | — | — | Prints the list of options and exits. |

Options must be written in full: `--catalogs` is not read as `--catalogs-dir`.

## How inputs are passed

Each kind of input is passed in one way:

| Input | Passed as | Example |
|---|---|---|
| One file: system, taxonomy, calendar | file path | `--system study/system.yml` |
| A set of files of the same kind: libraries, catalogs | folder, option name ends in `-dir` | `--catalogs-dir study/catalogs` |
| View configs, SimulationTables | file name pattern, plural option name | `--simulation-tables "output/st-x-mc-*.parquet"` |

A pattern picks files out of one folder that may also hold other files, such as the other outputs of a simulation:

- the wildcards go in the **file name** only: `*` matches any characters, `?` matches one character. The folder part is read as it is written, so `"output/*/st-*.parquet"` is rejected
- the pattern ends with a file name or a file name pattern, never with a folder: `"output/"` is rejected
- its folder part must exist. It may be the current folder, as in `"st-*.parquet"`
- at least one file must match, otherwise the run stops with `No files matched global pattern: …`;
- a plain file name is a pattern that matches one file: `--view-configs study/view_config.yml`.

!!! tip "Quote the patterns"
    Write patterns in quotes, as in `"output/st-*.parquet"`. Without quotes, your shell replaces the pattern by the list of matching files before GVB starts. As soon as more than one file matches, the run stops with `unrecognized arguments`.

## Logs

Each run writes one log file, except when the option parser rejects the command line (exit code `2`):

```text
<log dir>/gems-views-builder-pipeline-run-<UTC timestamp>.log
```

The log folder is the one given with `--log-dir`, or `logs` in the current folder. It is created if it does not exist. The same messages are printed in the terminal, on standard error.

By default the log holds the steps of the run: files loaded, checks passed, Views written. With `--verbose` it also holds debug messages, for example each metric and term being processed. When a run fails, the log stops at the last step that ran; the error itself is printed in the terminal only (see below).

## Errors and exit codes

GVB stops at the first problem it finds.

| Code | Meaning |
|---|---|
| `0` | The Views were written. |
| `1` | GVB found a problem: a path that does not exist, or an input that is invalid or inconsistent with another. The rules are listed on the [Validation rules](validation-rules.md) page. |
| `2` | The option parser rejected the command line: an option is missing or unknown, or has no value. |

For code `2`, the parser prints the usage and the reason:

```text
gems-views-builder: error: the following arguments are required: --catalogs-dir
```

For code `1`, the error is printed in the terminal as a Python traceback. Its last line names the file and the rule, after the prefix `Command lines options :` when a file or folder given on the command line does not exist, or `View building failed:` for every other problem:

```text
ValueError: Command lines options : --system is not a file: study/system.yml
```

```text
ValueError: View building failed: Metric 'PROD' used in view config 'view_area' doesn't exist in catalog 'catalog'
```

The error is not written to the log file.

Scripts and CI jobs can use the exit code to know whether the run succeeded.
