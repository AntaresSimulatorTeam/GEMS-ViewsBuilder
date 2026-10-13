# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

from gems_craft.model.parsing import LibrarySchema  # type: ignore
from gems_craft.model.resolve_library import resolve_library  # type: ignore
from gems_craft.study.parsing import parse_yaml_system  # type: ignore

from gems_views_builder.input.system import System, resolve_system


def load_system(system_file_path: Path, yml_libs: list[LibrarySchema]) -> System:
    logging.info("Loading system")
    with open(system_file_path, encoding="utf-8") as f:
        yml_system = parse_yaml_system(f)
    resolved_system = resolve_system(yml_system, resolve_library(yml_libs))
    logging.info(f"System loaded and resolved from {system_file_path}")
    return System(resolved_system)
