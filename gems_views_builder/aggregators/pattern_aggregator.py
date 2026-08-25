from gems_views_builder.aggregators.scenario_aggregator import ScenarioAggregator, make_scenario_operator
from gems_views_builder.aggregators.time_aggregator import TimeAggregator
from gems_views_builder.input.catalog import Metric
from gems_views_builder.input.view_config import AggregationPattern, ViewConfig
from gems_views_builder.metric_view import MetricView, TemporalMetricView


class PatternAggregator:
    def __init__(self, pattern: AggregationPattern):
        self.time_aggregator = TimeAggregator(pattern.time_granularity)
        self.scenario_aggregator = ScenarioAggregator(make_scenario_operator(pattern.scenario))

    def run(self, metric_view: TemporalMetricView, metric: Metric) -> MetricView:
        temporal_metric_view = self.time_aggregator.run(metric_view, metric)
        return self.scenario_aggregator.run(temporal_metric_view, metric)


def aggregations_factory(view_config: ViewConfig) -> list[PatternAggregator]:
    pattern_aggregators = []
    for pattern in view_config.aggregation_patterns:
        pattern_aggregators.append(PatternAggregator(pattern))
    return pattern_aggregators
