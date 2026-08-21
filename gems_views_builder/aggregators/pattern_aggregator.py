from dataclasses import dataclass

from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator, make_scenario_operator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import ViewConfig
from gems_views_builder.metric_view import MetricView


@dataclass
class PatternAggregator:
    time_aggregator: TimeAggregator
    scenario_aggregator: ScenarioAggregator

    def run(self, metric_view: MetricView, metric: Metric) -> MetricView:
        temporal_metric_view = self.time_aggregator.run(metric_view, metric)
        return self.scenario_aggregator.run(temporal_metric_view, metric)


def aggregations_factory(view_config: ViewConfig) -> list[PatternAggregator]:
    return [
        PatternAggregator(
            time_aggregator=TimeAggregator(pattern.time),
            scenario_aggregator=ScenarioAggregator(make_scenario_operator(pattern.scenario)),
        )
        for pattern in view_config.aggregation_patterns
    ]
