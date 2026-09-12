# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

from gems_craft.model.parsing import LibrarySchema, parse_yaml_library  # type: ignore


def load_yml_libs(library_dir: Path) -> list[LibrarySchema]:
    logging.info(f"Loading model libraries from {library_dir}")
    yml_libs: list[LibrarySchema] = []
    already_loaded_libs: set[str] = set()
    for library_file_path in collect_lib_files(library_dir):
        yml_lib = load_lib_file(library_file_path)
        if yml_lib.id in already_loaded_libs:
            raise ValueError(
                f"Library id {yml_lib.id!r} defined more than once in {library_dir} (also found in a different file)"
            )
        already_loaded_libs.add(yml_lib.id)
        yml_libs.append(yml_lib)
    return yml_libs


def collect_lib_files(library_dir: Path) -> list[Path]:
    return list(library_dir.glob("*.yml"))


def load_lib_file(library_file_path: Path) -> LibrarySchema:
    # # GEMS Craft future library could have option to load library model from path
    # # Current blueprint of method inside gemspy is typing.TextIO idk why ?
    logging.debug(f"Loading library YAML from {library_file_path}")
    with open(library_file_path, encoding="utf-8") as f:
        yml_lib = parse_yaml_library(f)
    logging.debug("Library YAML parsed successfully")
    return yml_lib
