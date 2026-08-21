from dataclasses import dataclass

from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.metric_view import MetricView


@dataclass
class PatternAggregator:
    time_aggregator: TimeAggregator
    scenario_aggregator: ScenarioAggregator

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        temporal_metric_view = self.time_aggregator.run(metric_view, metric)
        return self.scenario_aggregator.run(temporal_metric_view, metric)
