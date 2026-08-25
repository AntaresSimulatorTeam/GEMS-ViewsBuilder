from dataclasses import dataclass

from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator, make_scenario_operator
from gems_views_builder.input.view_config import TimeGranularity, ViewConfig
from gems_views_builder.metric_view import MetricView
from gems_views_builder.spatial_filter import SpatialFilter


@dataclass
class PatternAggregator:
    time_granularity: TimeGranularity
    scenario_aggregator: ScenarioAggregator

    def run(self, time_aggregated_metric_views: dict[TimeGranularity, MetricView]) -> MetricView:
        return self.scenario_aggregator.run(time_aggregated_metric_views[self.time_granularity])


def aggregations_factory(view_config: ViewConfig) -> list[PatternAggregator]:
    return [
        PatternAggregator(
            time_granularity=pattern.time,
            scenario_aggregator=ScenarioAggregator(
                make_scenario_operator(pattern.scenario), SpatialFilter(pattern.spatial_filter)
            ),
        )
        for pattern in view_config.aggregation_patterns
    ]
