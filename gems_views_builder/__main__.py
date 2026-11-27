# Copyright 2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
import tempfile
from pathlib import Path

from psutil import cpu_count

from gems_views_builder.cli import build_parser, check_options
from gems_views_builder.common import configure_logging
from gems_views_builder.input.component import (
    Component,
    create_components,
    enrich_components,
    group_components_by_taxon,
    supply_components_with_locations,
)
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.simulation_table import PersistentSimulationTable, create_simulation_table_chunks
from gems_views_builder.input.view_building_input import (
    ViewBuildingInput,
    create_view_building_input,
    make_filtered_simulation_table,
)
from gems_views_builder.input.view_config import ViewConfig, populate_view_configs_with_metrics
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.loader import Loader
from gems_views_builder.metric_structure_table import MetricStructureTable, get_pair_lookup_rows
from gems_views_builder.metrics_structure_builder import build_metric_structure_tables
from gems_views_builder.pair_lookup_table import PersistentPairLookupTable
from gems_views_builder.parallel_views_builder_executor import ParallelViewsBuilderExecutor
from gems_views_builder.validation.input_paths_validator import InputPathsValidator
from gems_views_builder.validation.input_validation import validate_input_data
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk

PHYSICAL_CORES = cpu_count(logical=False) or 1


def load_and_validate_input_data(input_paths: InputPaths) -> RawInputData:
    raw_input_data = Loader(input_paths).load()
    validate_input_data(raw_input_data)
    return raw_input_data


def build_components_by_taxon(raw_input_data: RawInputData) -> dict[str, list[Component]]:
    components = create_components(raw_input_data.system.components)
    enrich_components(components, raw_input_data)
    return group_components_by_taxon(components)


def view_building_process(view_building_input: ViewBuildingInput, view_sinker: ViewSinker) -> None:
    metric_views = ViewBuilder(view_building_input).build()
    accumulate_on_disk(metric_views, view_sinker)
    del metric_views


def create_view_building_inputs(
    simulation_table_chunks: dict[int, PersistentSimulationTable],
    view_configs: list[ViewConfig],
    ms_tables_by_view_config: dict[str, dict[str, MetricStructureTable]],
) -> list[ViewBuildingInput]:
    view_building_inputs: list[ViewBuildingInput] = []
    for view_config in view_configs:
        view_building_input = create_view_building_input(
            simulation_table_chunks, view_config, ms_tables_by_view_config[view_config.id]
        )
        view_building_inputs.append(view_building_input)
    return view_building_inputs


def run_view_building_process(input_paths: InputPaths, view_sinker: ViewSinker) -> None:
    raw_input_data = load_and_validate_input_data(input_paths)
    populate_view_configs_with_metrics(raw_input_data.view_configs, raw_input_data.catalogs)
    components_by_taxon = build_components_by_taxon(raw_input_data)

    supply_components_with_locations(components_by_taxon, raw_input_data.view_configs)
    ms_tables_by_view_config = build_metric_structure_tables(raw_input_data.view_configs, components_by_taxon)
    pair_lookup_rows = get_pair_lookup_rows(ms_tables_by_view_config)
    pair_lookup_table = PersistentPairLookupTable(pair_lookup_rows)

    filtered_simulation_table = make_filtered_simulation_table(raw_input_data, pair_lookup_table.dataframe)
    simulation_table_chunks = create_simulation_table_chunks(filtered_simulation_table, Path(tempfile.mkdtemp()))

    view_building_inputs = create_view_building_inputs(
        simulation_table_chunks, raw_input_data.view_configs, ms_tables_by_view_config
    )

    num_workers = len(view_building_inputs) if PHYSICAL_CORES >= len(view_building_inputs) else 1
    ParallelViewsBuilderExecutor(view_building_inputs, view_sinker).execute(num_workers)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose, log_dir=args.log_dir)

    try:
        check_options(args)
    except Exception as e:
        raise ValueError(f"Command lines options : {str(e)}") from e

    try:
        logging.info("Starting view building process")
        input_paths = InputPaths(args)
        InputPathsValidator(input_paths).validate()
        view_sinker = ViewSinkerFactory(args.output_dir, args.output_format).make()
        run_view_building_process(input_paths, view_sinker)
    except Exception as e:
        raise ValueError(f"View building failed: {e}") from e

    logging.info(f"View successfully written to {view_sinker.output_path}")


if __name__ == "__main__":
    main()
