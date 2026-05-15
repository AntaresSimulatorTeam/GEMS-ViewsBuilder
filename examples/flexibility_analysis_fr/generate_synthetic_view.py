"""Generate a synthetic GEMS View for the Flexibility Analysis (FSMS / FSCD) module.

Produces, alongside this script:
  - view.parquet              the 6-column long-format View consumed by the FS module
  - view_config.yml           the GEMS ViewConfig that "produced" view.parquet
  - catalog.yml               the catalog referenced by view_config.yml
  - calendar_file.csv         the calendar referenced by view_config.yml
  - flexibility_analysis.yml  the FS module's own config (paths wired up)

Design: each Flexibility Solution is synthesised as a sum of sinusoids targeting
one or two of the three FFT bands (annual / weekly / daily) plus broadband noise.
RESIDUAL_LOAD is then defined as the exact sum of all FS values, so the energy
conservation invariant (spec section 4.5) holds at machine precision.

Per-FS frequency emphasis (designer-controlled, so plots will be visually clean):

    FS               annual   weekly   daily    role
    NUCLEAR          strong   small    tiny     seasonal baseload modulation
    HYDRO            strong   strong   small    reservoir management
    GAS              small    small    strong   daily peaker
    PSH              -        small    strong   pump-by-night / turbine-by-day
    INTERCO          small    strong   strong   cross-border arbitrage
    DEMAND_RESP      -        small    strong   evening peak shaving

Two scenarios are produced (different RNG seeds, same skeleton) to exercise the
per-scenario pivot path described in spec section 5.1.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent

# --- Time axis ---------------------------------------------------------------
YEAR = 2035  # non-leap year => exactly 8760 hours
N_HOURS = 8760
START = pd.Timestamp(f"{YEAR}-01-01 00:00:00")
TIMESTAMPS = pd.date_range(START, periods=N_HOURS, freq="h")

W_YEAR = 2 * np.pi / N_HOURS  # rad / hour
W_WEEK = 2 * np.pi / (24 * 7)
W_DAY = 2 * np.pi / 24

# --- Zone & scenarios --------------------------------------------------------
LOCATION = "FR"
SCENARIOS = [0, 1]

# --- Flexibility Solutions ---------------------------------------------------
# Amplitudes in MW. annual / weekly / daily are sinusoid amplitudes;
# phase is in radians; noise_sigma is the Gaussian broadband noise stdev.
FS_DESIGN: dict[str, dict] = {
    "NUCLEAR":     dict(mean=30_000, annual=10_000, weekly=  800, daily=  300,
                        phase_year=0.0,  phase_week=0.8, phase_day=0.0,  noise_sigma=200),
    "HYDRO":       dict(mean=     0, annual= 4_000, weekly=2_500, daily=  600,
                        phase_year=0.2,  phase_week=0.0, phase_day=1.6,  noise_sigma=150),
    "GAS":         dict(mean=     0, annual= 2_000, weekly=  500, daily=4_000,
                        phase_year=0.0,  phase_week=0.5, phase_day=-1.6, noise_sigma=400),
    "PSH":         dict(mean=     0, annual=     0, weekly=  200, daily=3_000,
                        phase_year=0.0,  phase_week=1.0, phase_day=-1.6, noise_sigma=300),
    "INTERCO":     dict(mean=     0, annual= 1_000, weekly=1_500, daily=1_500,
                        phase_year=0.6,  phase_week=1.0, phase_day=-0.8, noise_sigma=400),
    "DEMAND_RESP": dict(mean=     0, annual=     0, weekly=  300, daily=2_000,
                        phase_year=0.0,  phase_week=0.3, phase_day=-1.6, noise_sigma=200),
}
FS_IDS = list(FS_DESIGN)
RESIDUAL_LOAD_ID = "RESIDUAL_LOAD"
ALL_METRIC_IDS = FS_IDS + [RESIDUAL_LOAD_ID]

# Display colors (hex) for the FS module's flexibility_analysis.yml.
FS_DISPLAY = {
    "NUCLEAR":     ("Nuclear",              "#DAA520"),
    "HYDRO":       ("Conventional hydro",   "#1E90FF"),
    "GAS":         ("Gas",                  "#B22222"),
    "PSH":         ("Pumped storage hydro", "#104E8B"),
    "INTERCO":     ("Interconnectors",      "#838B8B"),
    "DEMAND_RESP": ("Demand response",      "#66CDAA"),
}


def synthesise_fs(design: dict, seed: int) -> np.ndarray:
    """Build one FS time series in MW for the full year (8760 samples)."""
    t = np.arange(N_HOURS)
    rng = np.random.default_rng(seed)
    series = (
        design["mean"]
        + design["annual"] * np.cos(W_YEAR * t + design["phase_year"])
        + design["weekly"] * np.cos(W_WEEK * t + design["phase_week"])
        + design["daily"]  * np.cos(W_DAY  * t + design["phase_day"])
        + rng.normal(0.0, design["noise_sigma"], size=N_HOURS)
    )
    return series.astype(np.float64)


def build_view_rows() -> pd.DataFrame:
    """Return the View as a long-format DataFrame matching the spec schema."""
    blocks: list[pd.DataFrame] = []
    view_date_str = TIMESTAMPS.strftime("%Y-%m-%d %H:%M:%S").to_numpy()

    for scenario in SCENARIOS:
        # Per scenario, derive an independent seed per FS so noise differs but
        # the deterministic sinusoidal skeleton is identical.
        fs_values: dict[str, np.ndarray] = {}
        for i, fs in enumerate(FS_IDS):
            seed = 1000 * scenario + i  # deterministic, distinct
            fs_values[fs] = synthesise_fs(FS_DESIGN[fs], seed)

        # Residual load = exact sum of FS => energy conservation passes exactly.
        residual = np.zeros(N_HOURS, dtype=np.float64)
        for v in fs_values.values():
            residual += v

        for metric_id in ALL_METRIC_IDS:
            values = residual if metric_id == RESIDUAL_LOAD_ID else fs_values[metric_id]
            blocks.append(pd.DataFrame({
                "metric_id":            metric_id,
                "metric_location":      LOCATION,
                "breakdown_properties": "{}",
                "view_date":            view_date_str,
                "scenario":             np.int64(scenario),
                "metric_value":         values,
            }))

    df = pd.concat(blocks, ignore_index=True)
    df = df.astype({
        "metric_id":            "string",
        "metric_location":      "string",
        "breakdown_properties": "string",
        "view_date":            "string",
        "scenario":             "int64",
        "metric_value":         "float64",
    })
    return df


def write_calendar(path: Path) -> None:
    df = pd.DataFrame({
        "absolute_time_index": np.arange(N_HOURS, dtype=np.int64),
        "block":               np.ones(N_HOURS, dtype=np.int64),
        "granular_date":       TIMESTAMPS.strftime("%Y-%m-%d %H:%M:%S"),
    })
    df.to_csv(path, index=False)


def write_view_config(path: Path) -> None:
    cfg = {
        "view": {
            "id": "view_flexibility_fr",
            "scope": [
                {"location": None, "taxonomy-category": "balance"},
                {"calendar":  "calendar_file"},
            ],
            "aggregation": [
                {"time": "hour"},
            ],
            "catalog": [
                {"id": "catalog"},
            ],
            "metrics": [{"id": f"catalog.{m}"} for m in ALL_METRIC_IDS],
        }
    }
    with path.open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)


def write_catalog(path: Path) -> None:
    """Minimal catalog declaring the 7 metric_ids used in the View.

    Body fields (terms, output-id, …) are placeholders for this synthetic
    example — they are not used to derive the view, since view.parquet is
    generated directly. They are present so a tool reading the catalog
    can still resolve every catalog.<id> reference from view_config.yml.
    """
    metrics_def = []
    for m in ALL_METRIC_IDS:
        metrics_def.append({
            "id": m,
            "terms": [{
                "taxonomy-category": "production",
                "output-id": "p",
                "location-ports": "p_balance_port",
            }],
            "terms-operator": "sum",
            "time-operator":  "sum",
        })
    cfg = {
        "catalog": {
            "id": "catalog",
            "taxonomy": "my_taxonomy",
            "location": {"taxonomy-category": "balance"},
            "metrics-definition": metrics_def,
        }
    }
    with path.open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)


def write_flexibility_analysis_config(path: Path, view_path: Path, view_config_path: Path) -> None:
    cfg = {
        "flexibility_analysis": {
            "view":          str(view_path.name),
            "view_config":   str(view_config_path.name),
            "residual_load": RESIDUAL_LOAD_ID,
            "flexibility_solutions": [
                {"id": fs, "label": FS_DISPLAY[fs][0], "color": FS_DISPLAY[fs][1]}
                for fs in FS_IDS
            ],
            "frequency_cutoffs": {
                "annual_weekly": 20,
                "weekly_daily":  180,
            },
            "fscd_threshold": 0.20,
            "output_dir": "results/flexibility_analysis",
        }
    }
    with path.open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)


def main() -> None:
    view_path             = HERE / "view.parquet"
    view_config_path      = HERE / "view_config.yml"
    catalog_path          = HERE / "catalog.yml"
    calendar_path         = HERE / "calendar_file.csv"
    fs_analysis_cfg_path  = HERE / "flexibility_analysis.yml"

    df = build_view_rows()
    df.to_parquet(view_path, index=False)

    write_view_config(view_config_path)
    write_catalog(catalog_path)
    write_calendar(calendar_path)
    write_flexibility_analysis_config(fs_analysis_cfg_path, view_path, view_config_path)

    # --- Sanity checks (mirror spec section 4) ------------------------------
    assert len(df) == N_HOURS * len(ALL_METRIC_IDS) * len(SCENARIOS), "row count mismatch"
    for scenario in SCENARIOS:
        sub = df[df["scenario"] == scenario]
        pivot = sub.pivot(index="view_date", columns="metric_id", values="metric_value")
        fs_sum = pivot[FS_IDS].sum(axis=1)
        max_err = float((fs_sum - pivot[RESIDUAL_LOAD_ID]).abs().max())
        assert max_err < 1e-6, f"energy conservation broken in scenario {scenario}: {max_err}"

    print(f"Wrote {view_path.name}: {len(df):,} rows, {len(ALL_METRIC_IDS)} metrics, "
          f"{len(SCENARIOS)} scenarios, {N_HOURS} hours.")
    print(f"Wrote {view_config_path.name}, {catalog_path.name}, {calendar_path.name}, "
          f"{fs_analysis_cfg_path.name}.")


if __name__ == "__main__":
    main()
