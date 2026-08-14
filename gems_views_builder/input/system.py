# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""System wrapper with helper methods for component lookup."""

import logging
from pathlib import Path
from typing import Any, cast

from gems_craft.model.parsing import LibrarySchema  # type: ignore
from gems_craft.model.resolve_library import resolve_library  # type: ignore
from gems_craft.study import Component as GemsPyComponent  # type: ignore
from gems_craft.study.parsing import parse_yaml_system  # type: ignore
from gems_craft.study.resolve_components import (  # type: ignore
    System as GemsPySystem,
)
from gems_craft.study.resolve_components import (
    resolve_system,
)


class System:
    """
    Compose a Gems System and expose ViewsBuilder-specific helpers.
    """

    def __init__(self, system: GemsPySystem) -> None:
        self._system = system
        logging.info(
            f"Initializing input system with {len(self.components)} component(s) "
            f"and {len(self.connections)} connection(s)"
        )

    @property
    def components(self) -> list[GemsPyComponent]:
        return list(self._system.components)

    @property
    def connections(self) -> list[Any]:
        return cast(list[Any], getattr(self._system, "connections", None) or [])


def load_system(system_file_path: Path, parsed_libraries: list[LibrarySchema]) -> System:
    logging.info("Loading system")
    with open(system_file_path, encoding="utf-8") as f:
        parsed = parse_yaml_system(f)
    resolved = resolve_system(parsed, resolve_library(parsed_libraries))
    logging.info(f"System loaded and resolved from {system_file_path}")
    return System(cast(GemsPySystem, resolved))
