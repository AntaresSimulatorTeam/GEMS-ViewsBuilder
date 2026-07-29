# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""System wrapper with helper methods for component lookup."""

import logging
from pathlib import Path
from typing import Any, cast

from gems_craft.model.library import Library as GemsLibrary  # type: ignore
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


def load_system(input_data_path: Path, resolved_libs: dict[str, GemsLibrary]) -> System:
    logging.info("Loading system")
    system_path = input_data_path / "system.yml"
    with open(system_path, encoding="utf-8") as f:
        parsed = parse_yaml_system(f)
    resolved = resolve_system(parsed, resolved_libs)
    logging.info(f"System loaded and resolved from {system_path}")
    return System(cast(GemsPySystem, resolved))
