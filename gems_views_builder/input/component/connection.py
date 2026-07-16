from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gems_views_builder.input.component.component import Component


@dataclass
class ConnectionThroughPort:
    """Peer components connected to a component on a given port."""

    port: str
    components: list[Component] = field(default_factory=list)
