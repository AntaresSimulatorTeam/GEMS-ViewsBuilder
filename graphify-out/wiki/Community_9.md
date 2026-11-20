# Community 9

> 34 nodes · cohesion 0.14

## Key Concepts

- [Metric](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L86) (36 connections)
- [AggregationPattern](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L39) (27 connections)
- [Catalog](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L96) (24 connections)
- [ViewBuilderBasedModel](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/base_model.py#L9) (20 connections)
- [catalog.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L1) (17 connections)
- [load_catalog()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L136) (15 connections)
- [view_config.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L1) (13 connections)
- **ViewBuilderBasedModel** (11 connections)
- [test_catalog.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py#L1) (9 connections)
- [TermData](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L29) (6 connections)
- [ExtraLocation](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L18) (5 connections)
- [Location](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L30) (5 connections)
- [MetricId](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L46) (5 connections)
- [RawViewConfig](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L50) (5 connections)
- [Scope](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L34) (5 connections)
- [MetricData](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L50) (4 connections)
- [to_metric()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L120) (4 connections)
- [CatalogData](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L70) (3 connections)
- [CatalogLocationData](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L66) (3 connections)
- [to_term()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L111) (3 connections)
- [test_metric_filter_property_requires_value()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py#L49) (3 connections)
- [load_catalog_file()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L151) (2 connections)
- [test_catalog_known_metrics()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py#L43) (2 connections)
- [test_catalog_loads()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py#L12) (2 connections)
- [test_catalog_metrics_are_typed()](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py#L21) (2 connections)
- *... and 9 more nodes in this community*

## Class Diagram

```mermaid
classDiagram
    class ViewBuilderBasedModel {
        +base_model.py()
    }
    class Catalog {
        +catalog.py()
        +.get_metric()
    }
    class CatalogData {
        +catalog.py()
    }
    class CatalogLocationData {
        +catalog.py()
    }
    class Metric {
        +catalog.py()
    }
    class MetricData {
        +catalog.py()
    }
    class TermData {
        +catalog.py()
    }
    class AggregationPattern {
        +view_config.py()
    }
    class ExtraLocation {
        +view_config.py()
    }
    class Location {
        +view_config.py()
    }
    class MetricId {
        +view_config.py()
    }
    class RawViewConfig {
        +view_config.py()
    }
    class Scope {
        +view_config.py()
    }
    ViewBuilderBasedModel --> TermData
    ViewBuilderBasedModel --> MetricData
    ViewBuilderBasedModel --> CatalogLocationData
    ViewBuilderBasedModel --> CatalogData
    ViewBuilderBasedModel --> Metric
    ViewBuilderBasedModel --> Catalog
    ViewBuilderBasedModel --> ExtraLocation
    ViewBuilderBasedModel --> Location
    ViewBuilderBasedModel --> Scope
    ViewBuilderBasedModel --> AggregationPattern
    ViewBuilderBasedModel --> MetricId
    ViewBuilderBasedModel --> RawViewConfig
    Catalog --> ViewBuilderBasedModel
    Catalog --> ExtraLocation
    Catalog --> Location
    Catalog --> Scope
    Catalog --> AggregationPattern
    Catalog --> MetricId
    Catalog --> RawViewConfig
    CatalogData --> ViewBuilderBasedModel
    CatalogLocationData --> ViewBuilderBasedModel
    Metric --> ViewBuilderBasedModel
    Metric --> ExtraLocation
    Metric --> Location
    Metric --> Scope
    Metric --> AggregationPattern
    Metric --> MetricId
    Metric --> RawViewConfig
    MetricData --> ViewBuilderBasedModel
    TermData --> ViewBuilderBasedModel
    AggregationPattern --> ViewBuilderBasedModel
    AggregationPattern --> Catalog
    AggregationPattern --> Metric
    ExtraLocation --> ViewBuilderBasedModel
    ExtraLocation --> Catalog
    ExtraLocation --> Metric
    Location --> ViewBuilderBasedModel
    Location --> Catalog
    Location --> Metric
    MetricId --> ViewBuilderBasedModel
    MetricId --> Catalog
    MetricId --> Metric
    RawViewConfig --> ViewBuilderBasedModel
    RawViewConfig --> Catalog
    RawViewConfig --> Metric
    Scope --> ViewBuilderBasedModel
    Scope --> Catalog
    Scope --> Metric
```

## Relationships

- No strong cross-community connections detected

## Source Files

- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/base_model.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/base_model.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py)
- [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_catalog.py)

## Audit Trail

- EXTRACTED: 104 (42%)
- INFERRED: 141 (58%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*