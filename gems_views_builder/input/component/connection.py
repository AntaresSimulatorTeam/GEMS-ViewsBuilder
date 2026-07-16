from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gems_views_builder.input.component.component import Component


@dataclass
class ConnectionThroughPort:
    """Peer components connected to a component on a given port."""

    # port id -> list of components connected on that port
    port_components: dict[str, list[Component]] = field(default_factory=dict)

    def get_components(self, port_id: str) -> list[Component]:
        return self.port_components.get(port_id, [])
