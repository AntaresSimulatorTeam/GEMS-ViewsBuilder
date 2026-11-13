# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from gems_views_builder.aggregators.parallel import configured_view_config_workers
from gems_views_builder.cli import build_parser, check_options
from gems_views_builder.common import (
    configure_logging,
    timed_step,
)
from gems_views_builder.input.component import (
    Component,
    create_components,
    enrich_components,
    group_components_by_taxon,
    supply_components_with_locations,
)
from gems_views_builder.input.raw_input_data import RawInputData
from gems_views_builder.input.view_building_input import (
    create_view_building_input,
    make_filtered_simulation_table,
)
from gems_views_builder.input.view_config import ViewConfig, populate_view_configs_with_metrics
from gems_views_builder.input_paths import InputPaths
from gems_views_builder.loader import Loader
from gems_views_builder.metrics_structure_builder import collect_needed_pairs
from gems_views_builder.validation.input_paths_validator import InputPathsValidator
from gems_views_builder.validation.input_validation import validate_input_data
from gems_views_builder.view import ViewBuilder, ViewSinker, ViewSinkerFactory, accumulate_on_disk


def load_and_validate_input_data(input_paths: InputPaths) -> RawInputData:
    raw_input_data = Loader(input_paths).load()
    validate_input_data(raw_input_data)
    return raw_input_data


def build_components_by_taxon(raw_input_data: RawInputData) -> dict[str, list[Component]]:
    components = create_components(raw_input_data.system.components)
    enrich_components(components, raw_input_data)
    return group_components_by_taxon(components)


def run_view_building_process(input_paths: InputPaths, view_sinker: ViewSinker) -> None:
    with timed_step("load and validate inputs"):
        raw_input_data = load_and_validate_input_data(input_paths)
    with timed_step("build components"):
        populate_view_configs_with_metrics(raw_input_data.view_configs, raw_input_data.catalogs)
        components_by_taxon = build_components_by_taxon(raw_input_data)

    # Resolve locations for every view config up front, so the exact set of (component, output)
    # pairs read by any metric is known before the simulation table is filtered and clustered.
    with timed_step("resolve locations and needed pairs"):
        for view_config in raw_input_data.view_configs:
            supply_components_with_locations(components_by_taxon, view_config)
        needed_pairs = collect_needed_pairs(raw_input_data.view_configs, components_by_taxon)
    with timed_step("filter simulation table"):
        filtered_st = make_filtered_simulation_table(raw_input_data, needed_pairs)

    def build_and_write(view_config: ViewConfig) -> None:
        with timed_step(f"[{view_config.id}] build views"):
            view_building_input = create_view_building_input(filtered_st, view_config, components_by_taxon)
            metric_views = ViewBuilder(view_building_input).build()
        with timed_step(f"[{view_config.id}] write output files"):
            accumulate_on_disk(metric_views, view_sinker)
        # Drop this config's intermediate parquet files as soon as it is written.
        del metric_views

    # View configs only read the shared inputs and write files named after their own id, so they
    # can be built concurrently. Threads suffice: Polars releases the GIL while executing queries.
    view_configs = raw_input_data.view_configs
    workers = configured_view_config_workers(len(view_configs))
    if workers <= 1:
        for view_config in view_configs:
            build_and_write(view_config)
        return
    logging.info(f"Building up to {workers} view configs concurrently")
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="gvb-view-config") as executor:
        futures = [executor.submit(build_and_write, view_config) for view_config in view_configs]
        for future in as_completed(futures):
            future.result()


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
        with timed_step("total"):
            run_view_building_process(input_paths, view_sinker)
    except Exception as e:
        raise ValueError(f"View building failed: {e}") from e

    logging.info(f"View successfully written to {view_sinker.output_path}")


if __name__ == "__main__":
    main()
