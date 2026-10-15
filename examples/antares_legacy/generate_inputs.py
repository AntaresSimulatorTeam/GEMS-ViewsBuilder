# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Regenerate the simulation tables, the system and the calendar of this example from a small fictitious Antares
legacy study.

Requires antares-craft and an Antares Simulator 10.2.0 binary:
    python generate_inputs.py path/to/antares-10.2.0-Ubuntu-22.04/bin/antares-solver
    python generate_inputs.py path/to/antares-10.2.0-win64/bin/antares-solver.exe
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from antares.craft.model.area import AreaProperties
from antares.craft.model.link import LinkProperties
from antares.craft.model.renewable import RenewableClusterGroup, RenewableClusterProperties, TimeSeriesInterpretation
from antares.craft.model.settings.advanced_parameters import AdvancedParametersUpdate, RenewableGenerationModeling
from antares.craft.model.settings.general import GeneralParametersUpdate, Month, WeekDay
from antares.craft.model.settings.study_settings import StudySettingsUpdate
from antares.craft.model.st_storage import STStorageGroup, STStorageProperties
from antares.craft.model.study import Study, create_study_local
from antares.craft.model.thermal import ThermalClusterGroup, ThermalClusterProperties, ThermalCostGeneration

EXAMPLE_DIR = Path(__file__).parent
HOURS = 8760
NB_YEARS = 2
STAGE = "optim-nb-2"
CALENDAR_START = "2030-01-01"  # a Tuesday, as the study's 1st January

rng = np.random.default_rng(42)
hours = np.arange(HOURS)
winter = np.cos(2 * np.pi * hours / HOURS)  # 1 in January, -1 in July
daily = -np.cos(2 * np.pi * (hours % 24) / 24)  # peak in the evening, trough at night
daylight = np.clip(np.sin(2 * np.pi * ((hours % 24) - 6) / 24), 0, None)


def scenarios(profile: np.ndarray, noise: float) -> pd.DataFrame:
    """One column per MC year: the profile with some independent noise."""
    return pd.DataFrame({y: profile * (1 + noise * rng.standard_normal(HOURS)) for y in range(NB_YEARS)}).clip(0)


def build_study(parent_dir: Path) -> Study:
    study = create_study_local("two_areas", "9.2", parent_dir)
    study.update_settings(
        StudySettingsUpdate(
            general_parameters=GeneralParametersUpdate(
                nb_years=NB_YEARS,
                simulation_end=364,  # 52 full weeks
                january_first=WeekDay.TUESDAY,  # 2030-01-01, the first date of the calendar
                first_month_in_year=Month.JANUARY,
            ),
            advanced_parameters=AdvancedParametersUpdate(
                renewable_generation_modelling=RenewableGenerationModeling.CLUSTERS
            ),
        )
    )

    areas = {}
    for area_id, mean_load in (("fr", 9000), ("be", 2200)):
        area = study.create_area(area_id, properties=AreaProperties(energy_cost_unsupplied=3000, energy_cost_spilled=1))
        area.set_load(scenarios(mean_load * (1 + 0.25 * winter + 0.1 * daily), noise=0.05))
        areas[area_id] = area

    thermals = [
        ("fr", "nuclear", ThermalClusterGroup.NUCLEAR, 8, 1000, 15.0, 0.0),
        ("fr", "ccgt", ThermalClusterGroup.GAS, 8, 450, 60.0, 0.37),
        ("be", "ccgt", ThermalClusterGroup.GAS, 5, 400, 65.0, 0.37),
        ("be", "oil_peaker", ThermalClusterGroup.OIL, 6, 100, 150.0, 0.8),
    ]
    for area_id, name, group, units, capacity, cost, co2 in thermals:
        cluster = areas[area_id].create_thermal_cluster(
            name,
            properties=ThermalClusterProperties(
                group=group,
                unit_count=units,
                nominal_capacity=capacity,
                marginal_cost=cost,
                market_bid_cost=cost,
                co2=co2,
                cost_generation=ThermalCostGeneration.SET_MANUALLY,
            ),
        )
        cluster.set_series(pd.DataFrame(np.full((HOURS, 1), units * capacity)))

    renewables = [
        ("fr", "wind_onshore", RenewableClusterGroup.WIND_ON_SHORE, 3000, 0.3 + 0.1 * winter),
        ("fr", "solar_pv", RenewableClusterGroup.PV_SOLAR, 2000, daylight * (0.6 - 0.2 * winter)),
        ("be", "wind_offshore", RenewableClusterGroup.WIND_OFF_SHORE, 1000, 0.45 + 0.1 * winter),
        ("be", "solar_pv", RenewableClusterGroup.PV_SOLAR, 800, daylight * (0.5 - 0.2 * winter)),
    ]
    for area_id, name, group, capacity, factor in renewables:
        cluster = areas[area_id].create_renewable_cluster(
            name,
            properties=RenewableClusterProperties(
                group=group,
                nominal_capacity=capacity,
                ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR,
            ),
        )
        cluster.set_series(scenarios(factor, noise=0.3).clip(upper=1))

    areas["be"].create_st_storage(
        "battery",
        properties=STStorageProperties(
            group=STStorageGroup.BATTERY,
            injection_nominal_capacity=300,
            withdrawal_nominal_capacity=300,
            reservoir_capacity=600,
            efficiency=0.9,
        ),
    )

    link = study.create_link(area_from="be", area_to="fr", properties=LinkProperties(hurdles_cost=True))
    link.set_capacity_direct(pd.DataFrame(np.full((HOURS, 1), 1500)))
    link.set_capacity_indirect(pd.DataFrame(np.full((HOURS, 1), 1500)))
    # Columns: direct and indirect hurdle costs, impedances, loop flow, phase shifter min and max.
    link.set_parameters(pd.DataFrame(np.tile([0.5, 0.5, 0, 0, 0, 0], (HOURS, 1))))
    return study


def main(antares_solver: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        study_dir = Path(tmp_dir) / "two_areas"
        build_study(Path(tmp_dir))
        subprocess.run(
            [
                antares_solver,
                study_dir,
                "--output=simulation-tables",
                f"--simulation-table-stages={STAGE}",
                "--parquet",
            ],
            check=True,
        )
        output_dir = next((study_dir / "output").iterdir())
        tables_dir = EXAMPLE_DIR / "simulation_tables"
        shutil.rmtree(tables_dir, ignore_errors=True)
        tables_dir.mkdir()
        for table in sorted(output_dir.glob(f"simulation-table-*-{STAGE}.parquet")):
            shutil.copy(table, tables_dir / table.name)
        # Antares names the system after the absolute study path: name it after the study instead.
        system = (output_dir / "system-for-views.yml").read_text(encoding="utf-8")
        system = re.sub(r"^  id: .*$", "  id: two_areas", system, count=1, flags=re.MULTILINE)
        (EXAMPLE_DIR / "system-for-views.yml").write_text(system, encoding="utf-8", newline="\n")

    # One row per simulated hour (52 weeks), one block per week, as in the simulation tables.
    time_index = np.arange(52 * 168)
    pd.DataFrame(
        {
            "absolute_time_index": time_index,
            "block": time_index // 168,
            "granular_date": pd.date_range(CALENDAR_START, periods=len(time_index), freq="h"),
        }
    ).to_csv(EXAMPLE_DIR / "calendar.csv", index=False, lineterminator="\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
