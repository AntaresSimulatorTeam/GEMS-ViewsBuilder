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
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from gems.model.library import Library as GemsLibrary  # type: ignore
from gems.study import Component as GemsComponent  # type: ignore
from gems.study.parsing import parse_yaml_components  # type: ignore
from gems.study.resolve_components import (  # type: ignore
    System as GemsSystem,
)
from gems.study.resolve_components import (
    resolve_system,
)


class System:
    """
    Compose a Gems System and expose ViewsBuilder-specific helpers.
    """

    def __init__(self, system: GemsSystem) -> None:
        self._system = system
        logging.info(
            f"Initializing input system with {len(self.components)} component(s) "
            f"and {len(self.connections)} connection(s)"
        )

    @property
    def components(self) -> list[GemsComponent]:
        return list(self._system.components)

    @property
    def connections(self) -> list[Any]:
        return cast(list[Any], getattr(self._system, "connections", None) or [])

    # # This could be removed also
    # # I would like to keep this function as reminder
    # # When time comes we will be able to have multiple libraries as input so we need to keep distinction
    # # between components which will have same id but they will be in different libraries with different definitions
    def _models_to_components(self) -> dict[str, list[str]]:
        """
        Map each component ``model`` reference to the list of component ids using it.
        - Parsed input system: a string like ``<library_id>.<model_id>``.
        Qualified names keep components apart across libraries when the same role (e.g. a generator) behaves differently per library.
        |--> Good practice for future
        """
        logging.info("Building model-to-components index")
        groups: defaultdict[str, list[str]] = defaultdict(list)
        for component in self.components:
            model_ref = getattr(component, "model", None)
            key = model_ref if isinstance(model_ref, str) else getattr(model_ref, "id", None)
            if not isinstance(key, str) or "." not in key:
                continue
            groups[key].append(component.id)
        logging.info(f"Built model-to-components index with {len(groups)} qualified model reference(s)")
        return groups


def load_system(input_data_path: Path, resolved_libs: dict[str, GemsLibrary]) -> System:
    logging.info("Loading system")
    system_path = input_data_path / "system.yml"
    with open(system_path, encoding="utf-8") as f:
        parsed = parse_yaml_components(f)
    resolved = resolve_system(parsed, resolved_libs)
    logging.info(f"System loaded and resolved from {system_path}")
    return System(cast(GemsSystem, resolved))
