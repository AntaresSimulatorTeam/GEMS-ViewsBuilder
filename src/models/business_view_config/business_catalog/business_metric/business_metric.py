from dataclasses import dataclass
from typing import Optional

from .business_metric_term import BusinessMetricTerm
from .metric_term_operator import MetricTermOperator
from .metric_time_operator import MetricTimeOperator


@dataclass
class BusinessMetric:
    id: str
    terms: list[BusinessMetricTerm]
    term_operator: MetricTermOperator
    time_operator: MetricTimeOperator
    breakdown_property: Optional[str] = None
