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

from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from gems.study import Component  # type: ignore[import-untyped]
from gems.study.parsing import parse_yaml_components  # type: ignore[import-untyped]
from gems.study.resolve_components import System, resolve_system  # type: ignore[import-untyped]
from gems.study.system import PortsConnection  # type: ignore[import-untyped]

from gems_views_builder.common import logger
from gems_views_builder.library import ModelLibrary


class InputSystem:
    """
    Compose a Gems InputSystem and expose ViewsBuilder-specific helpers.
    """

    def __init__(self, system: System, *, library_id: str | None = None) -> None:
        self._system = system
        self._library_id = library_id
        logger.info(
            f"Initializing input system with {len(self.components)} component(s) "
            f"and {len(self.connections)} connection(s)"
        )
        self._components_by_model: dict[str, list[str]] = self._models_to_components()
        self._component_port_connections: dict[tuple[str, str], set[str]] = self.build_component_port_connections()
        logger.info(
            f"Input system indexes ready: {len(self._components_by_model)} model mapping(s), "
            f"{len(self._component_port_connections)} component-port mapping(s)"
        )

    @property
    def components(self) -> list[Component]:
        return list(self._system.components)

    @property
    def connections(self) -> list[PortsConnection]:
        # Resolved system always has `connections: list[PortsConnection]` in GemsPy.
        return cast(list[PortsConnection], self._system.connections)

    def _models_to_components(self) -> dict[str, list[str]]:
        """
        Map each component ``model`` reference to the list of component ids using it.
        - Parsed input system: a string like ``<library_id>.<model_id>``.
        Qualified names keep components apart across libraries when the same role (e.g. a generator) behaves differently per library.
        |--> Good practice for future
        """
        logger.info("Building model-to-components index")
        groups: defaultdict[str, list[str]] = defaultdict(list)
        for component in self.components:
            model_ref = getattr(component, "model", None)
            key = model_ref if isinstance(model_ref, str) else getattr(model_ref, "id", None)
            if not isinstance(key, str) or "." not in key:
                continue
            groups[key].append(component.id)
        logger.info(f"Built model-to-components index with {len(groups)} qualified model reference(s)")
        return groups

    def build_component_port_connections(self) -> dict[tuple[str, str], set[str]]:
        """
        Iterate over connections and for each component and port add other side of connection in dictionary
        """
        logger.info("Building component-port connection index")

        def _endpoint(conn: Any, idx: int) -> tuple[str, str] | None:
            """
            Return (component_id, port_id) for side `idx` in {1,2}, handling both:
            - parsed YAML connections (string fields component1/port1/component2/port2)
            - resolved connections (PortRef objects in port1/port2)
            """
            comp = getattr(conn, f"component{idx}", None)
            port = getattr(conn, f"port{idx}", None)

            # Resolved `PortsConnection`: port is a PortRef with {component, port_id}
            if comp is None and port is not None and not isinstance(port, str):
                comp_obj = getattr(port, "component", None)
                comp = getattr(comp_obj, "id", None)
                port = getattr(port, "port_id", None)

            if not (isinstance(comp, str) and comp and isinstance(port, str) and port):
                return None
            return comp, port

        component_port_connections: dict[tuple[str, str], set[str]] = defaultdict(set)
        for connection in self.connections:
            e1 = _endpoint(connection, 1)
            e2 = _endpoint(connection, 2)
            if e1 is None or e2 is None:
                continue

            (c1, p1), (c2, p2) = e1, e2

            # Some datasets omit port2, callers treated that as "same as port1".
            if not p2:
                p2 = p1

            if c1 == c2:
                continue

            component_port_connections[(c1, p1)].add(c2)
            component_port_connections[(c2, p2)].add(c1)

        logger.info(f"Built component-port connection index with {len(component_port_connections)} entry(ies)")
        return component_port_connections

    def _get_peer_components(self, component_id: str, port_id: str) -> str | tuple[str, ...]:
        """Return the peer component id(s) for (component_id, port_id), or raise ValueError."""
        if (component_id, port_id) not in self._component_port_connections:
            raise ValueError(f"No connection found for component {component_id!r} on port {port_id!r}")

        peers = self._component_port_connections[(component_id, port_id)]
        if len(peers) == 1:
            return next(iter(peers))
        return tuple(peers)

    def get_instances_by_model(self, qualified_model_ref: str) -> list[str]:
        """Return component instance IDs for the given qualified model reference."""
        instances = list(self._components_by_model.get(qualified_model_ref, []))
        logger.debug(f"Resolved {len(instances)} instance(s) for model reference {qualified_model_ref!r}")
        return instances

    def get_component(self, component_id: str) -> Component:
        # Resolved-only design: delegate to GemsPy's implementation.
        return cast(Component, self._system.get_component(component_id))

    def get_location(
        self,
        component_0_id: str,
        location_port: str | tuple[str, ...] | None,
    ) -> str | tuple[str, ...]:
        if location_port is None:
            logger.debug(f"Using component {component_0_id!r} as location because no location port is defined")
            return component_0_id

        if isinstance(location_port, str):
            peer = self._get_peer_components(component_0_id, location_port)
            logger.debug(f"Resolved location for component {component_0_id!r} via port {location_port!r} to {peer!r}")
            return peer

        # location_port is tuple[str, ...] — each named port resolves to one or more peers
        result: list[str] = []
        for port in location_port:
            peer = self._get_peer_components(component_0_id, port)
            if isinstance(peer, str):
                result.append(peer)
            else:
                result.extend(peer)
        logger.debug(
            f"Resolved location tuple for component {component_0_id!r} via ports {location_port!r} to {tuple(result)!r}"
        )
        return tuple(result)

    @classmethod
    def load(cls, path: Path, library: "ModelLibrary") -> "InputSystem":
        """
        Load and resolve a Gems system from a `system.yml` file using a loaded model library.

        This keeps the public API as `InputSystem.load(path, library)` while delegating
        the lower-level "already-resolved libraries" variant to `from_file_resolved(...)`.
        """
        logger.info(f"Loading input system from {path}")
        libraries = library.resolve_libraries()
        return cls.from_file_resolved(path, libraries, library_id=library.id)

    @classmethod
    def from_file_resolved(
        cls, path: Path, libraries: dict[str, object], *, library_id: str | None = None
    ) -> "InputSystem":
        """
        Load and resolve a Gems system from a `system.yml` file using already-resolved libraries.
        """
        logger.info(f"Parsing system YAML from {path}")
        with open(path, encoding="utf-8") as f:
            parsed = parse_yaml_components(f)
        logger.info(f"Resolving system from {path} with {len(libraries)} librar(y/ies)")
        resolved = resolve_system(parsed, libraries)
        logger.info(f"System resolved successfully from {path}")
        return cls(cast(System, resolved), library_id=library_id)
