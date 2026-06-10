# GEMS-ViewsBuilder — Technical Documentation

## What this tool does

GEMS-ViewsBuilder transforms simulation outputs into aggregated **Views**.
It reads a set of input files describing a study (topology, simulation results, metric
definitions) and produces a single parquet file — one row per
`(metric, location, breakdown, date, scenario)`.

Entry point:

```python
from pathlib import Path
from gems_views_builder.views import ViewBuilder

ViewBuilder(Path("path/to/study")).build()
# → path/to/study/results/view20260610T120000.parquet
```

## Two-part documentation

| Part | Folder | Answers |
|---|---|---|
| **Input data** | [`input-data/`](input-data/) | What files does the tool read? What are their schemas? How do they reference each other? |
| **Pipeline** | [`pipeline/`](pipeline/) | What does the code do with those inputs, step by step? |

Design decisions and open questions are in [`adr/`](adr/).

## Input files at a glance

| File | Role |
|---|---|
| `taxonomy.yml` | Shared vocabulary: category hierarchy, ports, output types |
| `library.yml` | Model definitions: variables, ports, extra-outputs per model |
| `system.yml` | Component instances and their port connections |
| `calendar*.csv` | Maps each simulation timestep to a date and block |
| `simulation_table*.parquet` | Raw simulation outputs (one row per component × output × time × scenario) |
| `catalogs/<id>.yml` | Business metric definitions |
| `view_config.yml` | Selects which metrics to compute and how to aggregate them |

See [`input-data/02-input-files.md`](input-data/02-input-files.md) for schemas and relationships.

## Output

`results/view<timestamp>.parquet` — schema documented in [`pipeline/03-output-schema.md`](pipeline/03-output-schema.md).
