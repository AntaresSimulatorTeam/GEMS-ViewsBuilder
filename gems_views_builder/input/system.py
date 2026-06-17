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

from gems.study.parsing import (  # type: ignore
    ComponentSchema as GemsComponent,
)
from gems.study.parsing import SystemSchema as GemsSystem
from gems.study.parsing import parse_yaml_components


class System:
    """
    Compose a Gems System and expose ViewsBuilder-specific helpers.
    """

    def __init__(self, system: GemsSystem) -> None:
        self._system = system
        self._components_by_model: dict[str, list[str]] = self.models_to_components()
        self._component_port_connections: dict[tuple[str, str], set[str]] = self.build_component_port_connections()

    @property
    def components(self) -> list[GemsComponent]:
        return cast(list[GemsComponent], self._system.components)

    @property
    def connections(self) -> list[Any]:
        return cast(list[Any], getattr(self._system, "connections", None) or [])

    def models_to_components(self) -> dict[str, list[str]]:
        """
        Map each component ``model`` reference (e.g. ``pypsa_models.generator``) to the list of component ids using it.
        Qualified names keep components apart across libraries when the same role (e.g. a generator) behaves differently per library.
        |--> Good practice for future
        """
        groups: defaultdict[str, list[str]] = defaultdict(list)
        for component in self.components:
            model_ref = getattr(component, "model", None)
            if not model_ref or "." not in model_ref:
                continue
            groups[model_ref].append(component.id)
        return groups

    def build_component_port_connections(self) -> dict[tuple[str, str], set[str]]:
        """
        Iterate over connections and for each component and port add other side of connection in dictionary
        """
        component_port_connections: dict[tuple[str, str], set[str]] = defaultdict(set)
        for connection in self.connections:
            component1 = cast(str | None, getattr(connection, "component1", None))
            port1 = cast(str | None, getattr(connection, "port1", None))
            component2 = cast(str | None, getattr(connection, "component2", None))
            port2 = cast(str | None, getattr(connection, "port2", None))

            if port1 is not None and port2 is None:
                port2 = port1

            if (
                component1 is not None
                and component2 is not None
                and port1 is not None
                and port2 is not None
                and component1 != component2
            ):
                component_port_connections[(component1, port1)].add(component2)
                component_port_connections[(component2, port2)].add(component1)

        return component_port_connections

    def _get_peer_component(self, component_id: str, port_id: str) -> str:
        """Return the peer component id for (component_id, port_id), or raise ValueError."""
        if (component_id, port_id) not in self._component_port_connections:
            raise ValueError(f"No connection found for component {component_id!r} on port {port_id!r}")

        peers = self._component_port_connections[(component_id, port_id)]
        if len(peers) > 1:
            raise ValueError(f"Multiple connections found for component {component_id!r} on port {port_id!r}")

        return next(iter(peers))

    def get_instances_by_model(self, qualified_model_ref: str) -> list[str]:
        """Return component instance IDs for the given qualified model reference."""
        return list(self._components_by_model.get(qualified_model_ref, []))

    def get_location(
        self,
        component_0_id: str,
        location_port: str | tuple[str, ...] | None,
    ) -> str | tuple[str, ...]:
        if location_port is None:
            return component_0_id

        if isinstance(location_port, str):
            peer = self._get_peer_component(component_0_id, location_port)
            return peer

        # location_port is tuple[str, ...]
        result: list[str] = []
        for port in location_port:
            peer = self._get_peer_component(component_0_id, port)
            result.append(peer)
        return tuple(result)

    @classmethod
    def from_file(cls, path: Path) -> "System":
        """Load a system yml file."""
        logging.info(f"Loading system from {path}")
        with open(path, encoding="utf-8") as f:
            parsed = parse_yaml_components(f)
        logging.info(f"System loaded from {path}")
        return cls(cast(GemsSystem, parsed))


def load_system(input_data_path: Path) -> System:
    logging.info("Loading system")
    system_path = next(input_data_path.glob("system*"))
    system = System.from_file(system_path)
    logging.info(f"System loaded from {system_path}")
    return system
