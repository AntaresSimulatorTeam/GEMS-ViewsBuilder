from dataclasses import dataclass
from typing import Optional

from models.common.location import LocationPorts


@dataclass
class BusinessMetricTerm:
    taxonomy_category: str
    location_ports: LocationPorts
    output: str  # in simulation table is also output(to be consistent)
    weight_output_id: Optional[str] = None
    filter: Optional[str] = None
