from dataclasses import dataclass


@dataclass
class MetricTermOperator:
    term_operator: str  # sum or avg for now
