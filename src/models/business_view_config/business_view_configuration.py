from dataclasses import dataclass

from .business_catalog.business_catalog import BusinessCatalog


@dataclass
class BusinessViewConfiguration:
    id: str
    catalogs: list[BusinessCatalog]
    callendar_id: str
    metrics_id: list[list[str]]  # list of couples (catalog_id, metric_id)
