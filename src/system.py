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

"""InputSystem wrapper with helper methods for component lookup."""

from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from gems.study.parsing import InputComponent as GemsInputComponent  # type: ignore[import-untyped]
from gems.study.parsing import InputSystem as GemsInputSystem
from gems.study.parsing import parse_yaml_components


class InputSystem:
    """
    Compose a Gems InputSystem and expose ViewsBuilder-specific helpers.
    """

    def __init__(self, system: GemsInputSystem) -> None:
        self._system = system
        self._components_by_model: dict[str, list[str]] = self.models_to_components()

    @property
    def components(self) -> list[GemsInputComponent]:
        return cast(list[GemsInputComponent], self._system.components)

    @property
    def connections(self) -> list[Any]:
        return cast(list[Any], getattr(self._system, "connections", None) or [])

    def models_to_components(self) -> dict[str, list[str]]:
        groups: defaultdict[str, list[str]] = defaultdict(list)
        for component in self.components:
            model_ref = getattr(component, "model", None)
            if not model_ref or "." not in model_ref:
                continue
            groups[model_ref].append(component.id)
        return groups

    def get_components(self, model_id: str) -> list[str]:
        """Return all component ids for the given model type (e.g. 'generator' -> ['generator_A1', ...])."""
        return self._components_by_model.get(model_id, [])

    def get_component_by_id(self, component_id: str) -> GemsInputComponent:
        for component in self.components:
            if component.id == component_id:
                return component
        raise ValueError(f"Component {component_id} not found")

    def _get_peer_component(self, component_id: str, port_id: str) -> str | None:
        """
        Find the component connected to (component_id, port_id).

        Returns None if not found.
        """
        # GemsPy exposes `connections` as a list of pydantic objects (e.g. InputPortConnections),
        # so we must use attribute access (not dict `.get()`).
        for conn in self.connections:
            c1 = cast(str | None, getattr(conn, "component1", None))
            p1 = cast(str | None, getattr(conn, "port1", None))
            c2 = cast(str | None, getattr(conn, "component2", None))
            p2 = cast(str | None, getattr(conn, "port2", None))
            if (c1, p1) == (component_id, port_id):
                return c2
            if (c2, p2) == (component_id, port_id):
                return c1
        return None

    def get_location(
        self,
        component_0_id: str,
        location_port: str | tuple[str, ...] | None,
    ) -> str | tuple[str, ...]:
        if location_port is None:
            return component_0_id

        if isinstance(location_port, str):
            peer = self._get_peer_component(component_0_id, location_port)
            if peer is None:
                raise ValueError(f"No connection found for component {component_0_id!r} on port {location_port!r}")
            return peer

        # location_port is tuple[str, ...]
        result: list[str] = []
        for port in location_port:
            peer = self._get_peer_component(component_0_id, port)
            if peer is None:
                raise ValueError(f"No connection found for component {component_0_id} on port {port}")
            result.append(peer)
        return tuple(result)

    @classmethod
    def from_file(cls, path: Path) -> "InputSystem":
        """Load InputSystem from a system yml file."""
        with open(path) as f:
            parsed = parse_yaml_components(f)
        return cls(cast(GemsInputSystem, parsed))
