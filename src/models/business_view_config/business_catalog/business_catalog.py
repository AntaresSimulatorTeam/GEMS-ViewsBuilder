from dataclasses import dataclass

from .business_metric.business_metric import BusinessMetric


@dataclass
class BusinessCatalog:
    id: str
    location_taxonomy_category: str | tuple[str]
    metrics: dict[str, BusinessMetric]
