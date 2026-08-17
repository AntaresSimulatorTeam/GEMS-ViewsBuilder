# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""System wrapper with helper methods for component lookup."""

import logging
from pathlib import Path
from typing import Any, cast

from gems_craft.model.parsing import LibrarySchema  # type: ignore
from gems_craft.model.resolve_library import resolve_library  # type: ignore
from gems_craft.study import Component as GemsPyComponent  # type: ignore
from gems_craft.study import PortRef
from gems_craft.study.parsing import ComponentSchema, SystemSchema, parse_yaml_system  # type: ignore
from gems_craft.study.resolve_components import (  # type: ignore
    System as GemsPySystem,
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


def _resolve_component_without_parameter_check(
    resolved_libraries: dict[str, Any], component: ComponentSchema
) -> GemsPyComponent:
    lib_id, _ = component.model.split(".")
    model = resolved_libraries[lib_id].models[component.model]

    properties: dict[str, str] = {}
    for item in component.properties or []:
        if item.id in properties:
            raise ValueError(f"Component {component.id!r}: duplicate properties id {item.id!r}")
        properties[item.id] = item.value
    missing = sorted(k for k in model.properties if k not in properties)
    if missing:
        raise ValueError(
            f"Component {component.id!r} (model {model.id!r}) is missing properties declared by the model: {missing}"
        )

    return GemsPyComponent(model=model, id=component.id, scenario_group=component.scenario_group, properties=properties)


def resolve_system_tolerating_missing_parameters(
    yml_system: SystemSchema, resolved_libraries: dict[str, Any]
) -> GemsPySystem:
    """Resolve a system like GemsPy's ``resolve_system``, minus the parameter completeness check.

    The ViewsBuilder reads component ids, model ids, properties and connections, never
    parameter values (the resolved GemsPy ``Component`` does not carry them), so systems
    written for view building may omit ``parameters``. Property completeness is still enforced.
    """
    system = GemsPySystem("study")
    components_by_id: dict[str, Any] = {}
    for component_schema in yml_system.components:
        component = _resolve_component_without_parameter_check(resolved_libraries, component_schema)
        system.add_component(component)
        components_by_id[component.id] = component

    for connection in yml_system.connections or []:
        system.connect(
            PortRef(components_by_id[connection.component1], connection.port1),
            PortRef(components_by_id[connection.component2], connection.port2),
        )
    return system


def load_system(system_file_path: Path, yml_libs: list[LibrarySchema]) -> System:
    logging.info("Loading system")
    with open(system_file_path, encoding="utf-8") as f:
        yml_system = parse_yaml_system(f)
    resolved_system = resolve_system_tolerating_missing_parameters(yml_system, resolve_library(yml_libs))
    logging.info(f"System loaded and resolved from {system_file_path}")
    return System(cast(GemsPySystem, resolved_system))
