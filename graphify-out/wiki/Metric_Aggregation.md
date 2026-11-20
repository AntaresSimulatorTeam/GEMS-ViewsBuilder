# Metric Aggregation

> 94 nodes · cohesion 0.05

## Key Concepts

- [TemporalMetricView](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/metric_view.py#L23) (22 connections)
- [TimeGranularity](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L22) (19 connections)
- [MetricView](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/metric_view.py#L12) (16 connections)
- [AggregationPatternList](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/pattern_aggregator.py#L33) (15 connections)
- [.run()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L103) (13 connections)
- [TimeAggregator](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/time_aggregator.py#L29) (13 connections)
- [ScenarioAggregator](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L97) (12 connections)
- [TermsAggregator](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/terms_aggregator.py#L16) (11 connections)
- [Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_pattern_aggregator.py#L43) (11 connections)
- [scenario_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L1) (10 connections)
- [AggregOperatorType](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L24) (9 connections)
- [test_pattern_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_pattern_aggregator.py#L1) (9 connections)
- [LocationFilter](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/location_filter.py#L10) (9 connections)
- **Enum** (8 connections)
- [test_scenario_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/test_scenario_aggregator.py#L1) (8 connections)
- [aggregate_scenarios()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L83) (8 connections)
- [ScenarioAggregation](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L46) (8 connections)
- [ScenarioColumnsAddition](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L68) (8 connections)
- [ScenarioOperator](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py#L37) (8 connections)
- [get_executor()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/parallel.py#L49) (7 connections)
- [Union of the patterns' location filters, or None if any pattern keeps every loca](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/pattern_aggregator.py#L23) (7 connections)
- [Runs every aggregation pattern of a view config on one metric.      Each distinc](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/pattern_aggregator.py#L34) (7 connections)
- [test_patterns_match_one_pattern_at_a_time()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_pattern_aggregator.py#L100) (7 connections)
- [Minimal parquet for the scenario step: metric_id, metric_location, breakdown_pro](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/test_scenario_aggregator.py#L33) (7 connections)
- [test_terms_aggregation_avg()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_terms_aggregator.py#L67) (7 connections)
- *... and 69 more nodes in this community*

## Class Diagram

```mermaid
classDiagram
    class AggregOperatorType {
        +catalog.py()
    }
    class LocationFilter {
        +location_filter.py()
    }
    class MetricView {
        +metric_view.py()
        +.__del__()
    }
    class TemporalMetricView {
        +metric_view.py()
    }
    class SerialExecutor {
        +parallel.py()
        +.submit()
    }
    class AggregationPatternList {
        +pattern_aggregator.py()
        +.__init__()
        +.run()
    }
    class Operator {
        +scenario_aggregator.py()
    }
    class ScenarioAggregation {
        +scenario_aggregator.py()
        +.apply()
    }
    class ScenarioAggregator {
        +scenario_aggregator.py()
        +.__init__()
        +.run()
    }
    class ScenarioColumnsAddition {
        +scenario_aggregator.py()
        +.apply()
    }
    class ScenarioOperator {
        +scenario_aggregator.py()
        +.run()
    }
    class TermsAggregator {
        +terms_aggregator.py()
        +.__init__()
        +.run()
        +.__del__()
    }
    class TimeAggregator {
        +time_aggregator.py()
        +.__init__()
        +.run()
    }
    class TimeGranularity {
        +view_config.py()
    }
    AggregOperatorType --> TimeAggregator
    AggregOperatorType --> TermsAggregator
    LocationFilter --> Operator
    LocationFilter --> ScenarioOperator
    LocationFilter --> ScenarioAggregation
    LocationFilter --> ScenarioColumnsAddition
    LocationFilter --> ScenarioAggregator
    TemporalMetricView <|-- MetricView
    MetricView --> TimeAggregator
    MetricView --> TermsAggregator
    MetricView --> AggregationPatternList
    MetricView <|-- TemporalMetricView
    TemporalMetricView --> TimeAggregator
    TemporalMetricView --> AggregationPatternList
    TemporalMetricView --> Operator
    TemporalMetricView --> ScenarioOperator
    TemporalMetricView --> ScenarioAggregation
    TemporalMetricView --> ScenarioColumnsAddition
    TemporalMetricView --> ScenarioAggregator
    AggregationPatternList --> TimeGranularity
    AggregationPatternList --> MetricView
    AggregationPatternList --> TemporalMetricView
    Operator --> LocationFilter
    Operator --> TemporalMetricView
    ScenarioOperator <|-- ScenarioAggregation
    ScenarioAggregation --> LocationFilter
    ScenarioAggregation --> TemporalMetricView
    ScenarioAggregator --> LocationFilter
    ScenarioAggregator --> TemporalMetricView
    ScenarioOperator <|-- ScenarioColumnsAddition
    ScenarioColumnsAddition --> LocationFilter
    ScenarioColumnsAddition --> TemporalMetricView
    ScenarioAggregation <|-- ScenarioOperator
    ScenarioColumnsAddition <|-- ScenarioOperator
    ScenarioOperator --> LocationFilter
    ScenarioOperator --> TemporalMetricView
    TermsAggregator --> AggregOperatorType
    TermsAggregator --> MetricView
    TimeAggregator --> AggregOperatorType
    TimeAggregator --> TimeGranularity
    TimeAggregator --> MetricView
    TimeAggregator --> TemporalMetricView
    TimeGranularity --> TimeAggregator
    TimeGranularity --> AggregationPatternList
```

## Relationships

- No strong cross-community connections detected

## Source Files

- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/aggregations_processor.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/aggregations_processor.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/parallel.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/parallel.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/pattern_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/pattern_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/scenario_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/terms_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/terms_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/time_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/aggregators/time_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/common.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/common.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/location_filter.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/location_filter.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/metric_view.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/metric_view.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/test_scenario_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/test_scenario_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/test_time_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/test_time_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_pattern_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_pattern_aggregator.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_terms_aggregator.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_terms_aggregator.py)

## Audit Trail

- EXTRACTED: 250 (50%)
- INFERRED: 247 (50%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*