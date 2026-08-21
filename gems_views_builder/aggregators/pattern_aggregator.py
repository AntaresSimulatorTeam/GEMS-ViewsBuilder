from dataclasses import dataclass

from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.into_scenario_view import ScenarioPatternOperator, to_scenario_view
from gems_views_builder.metric_view import MetricView


@dataclass
class PatternAggregator:
    time_aggregator: TimeAggregator
    scenario_operator: ScenarioPatternOperator

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        temporal_metric_view = self.time_aggregator.run(metric_view, metric)
        to_scenario_view(temporal_metric_view, self.scenario_operator)
        return temporal_metric_view
