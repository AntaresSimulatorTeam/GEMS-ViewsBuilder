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

from gems.model.resolve_library import resolve_library  # type: ignore[import-untyped]
from gems.study import Component  # type: ignore[import-untyped]
from gems.study.parsing import parse_yaml_components  # type: ignore[import-untyped]
from gems.study.resolve_components import (  # type: ignore[import-untyped]
    System as GemsSystem,
)
from gems.study.resolve_components import (
    resolve_system,
)

from gems_views_builder.input.library import load_library_file


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
        self._components_by_model: dict[str, list[str]] = self._models_to_components()
        self._component_port_connections: dict[tuple[str, str], set[str]] = self.build_component_port_connections()
        logging.info(
            f"Input system indexes ready: {len(self._components_by_model)} model mapping(s), "
            f"{len(self._component_port_connections)} component-port mapping(s)"
        )

    @property
    def components(self) -> list[Component]:
        return list(self._system.components)

    @property
    def connections(self) -> list[Any]:
        return cast(list[Any], getattr(self._system, "connections", None) or [])

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

    def build_component_port_connections(self) -> dict[tuple[str, str], set[str]]:
        """
        Iterate over connections and for each component and port add other side of connection in dictionary
        """
        logging.info("Building component-port connection index")

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

        logging.info(f"Built component-port connection index with {len(component_port_connections)} entry(ies)")
        return component_port_connections

    def _get_peer_components(self, component_id: str, port_id: str) -> tuple[str, ...]:
        """Return every peer component id connected to ``(component_id, port_id)``."""
        return tuple(self._component_port_connections.get((component_id, port_id), ()))

    def get_instances_by_model(self, qualified_model_ref: str) -> list[str]:
        """Return component instance IDs for the given qualified model reference."""
        instances = list(self._components_by_model.get(qualified_model_ref, []))
        logging.debug(f"Resolved {len(instances)} instance(s) for model reference {qualified_model_ref!r}")
        return instances

    def get_component(self, component_id: str) -> Component:
        return cast(Component, self._system.get_component(component_id))

    def get_location(
        self,
        component_0_id: str,
        location_port: str | tuple[str, ...] | None,
    ) -> str | tuple[str, ...]:
        if location_port is None:
            logging.debug(f"Using component {component_0_id!r} as location because no location port is defined")
            return component_0_id

        if isinstance(location_port, str):
            return self._resolve_unique_location(component_0_id, location_port)

        # location_port is tuple[str, ...] — resolve each port individually (reusing
        # the single-port logic, which enforces the uniqueness rule per port) and
        # keep one location per port, in order.
        return tuple(self._resolve_unique_location(component_0_id, port) for port in location_port)

    def _resolve_unique_location(self, component_0_id: str, location_port: str) -> str:
        """Resolve a single location port to its UNIQUE peer component id.

        For metric building each port must resolve to exactly one peer: the locating
        peer component has to be unique. Zero or multiple peers is an error here (the
        general-purpose :meth:`_get_peer_components` lookup itself stays permissive).
        """
        peers = self._get_peer_components(component_0_id, location_port)
        if len(peers) != 1:
            raise ValueError(
                f"Expected exactly one peer component for component {component_0_id!r} "
                f"on port {location_port!r}, but found {len(peers)}: {peers!r}"
            )
        peer = peers[0]
        logging.debug(f"Resolved location for component {component_0_id!r} via port {location_port!r} to {peer!r}")
        return peer


def load_system(input_data_path: Path) -> System:
    logging.info("Loading system")
    system_path = input_data_path / "system.yml"
    library_path = input_data_path / "library.yml"
    with open(system_path, encoding="utf-8") as f:
        parsed = parse_yaml_components(f)
    library_schema = load_library_file(library_path)
    resolved_libs = resolve_library([library_schema])
    resolved = resolve_system(parsed, resolved_libs)
    logging.info(f"System loaded and resolved from {system_path}")
    return System(cast(GemsSystem, resolved))
