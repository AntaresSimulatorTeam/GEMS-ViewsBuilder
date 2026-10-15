# Example: views of an Antares legacy study

A fictitious Antares legacy study: two areas (`fr`, `be`) joined by a link, with load, thermal and renewable
clusters and a battery, simulated hourly over one year (52 weeks) for 2 Monte Carlo years.

[OPERATING_MODE.md](OPERATING_MODE.md) describes the input files, in `inputs/`, and the CLI call that builds the views.
`python run_example.py` builds both the area and link views, on any OS.

## Regenerate the inputs

`generate_inputs.py` builds the study with antares-craft, runs
`antares-solver --output=simulation-tables --simulation-table-stages=optim-nb-2 --parquet`
and writes `simulation_tables/`, `system-for-views.yml` and `calendar.csv` in `inputs/`:

```bash
python generate_inputs.py path/to/antares-10.2.0-Ubuntu-22.04/bin/antares-solver  # Windows: antares-10.2.0-win64/bin/antares-solver.exe
```
