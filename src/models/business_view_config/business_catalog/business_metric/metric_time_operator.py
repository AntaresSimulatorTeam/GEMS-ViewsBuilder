from dataclasses import dataclass


@dataclass
class MetricTimeOperator:
    metric_time_operator: str  # sum or avg for now
