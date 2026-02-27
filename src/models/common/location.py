from dataclasses import dataclass


@dataclass
class LocationPorts:
    location_ports: str | tuple[str] | None
