# AggregationPattern

> God node · 27 connections · [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L39)

## Call Trace Diagram

```mermaid
sequenceDiagram
    participant P0 as AggregationPattern
    participant P1 as Metric
    participant P2 as ViewConfig
    participant P3 as MetricStructureTableBuilder
    participant P4 as Catalog
    participant P5 as load_view_config()
    participant P6 as RawInputData
    participant P7 as ViewBuilderBasedModel
    participant P8 as AggregationPatternList
    participant P9 as Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.
    participant P10 as AggregationProcessor
    participant P11 as ViewConfigMetricsAgainstCatalogsValidator
    participant P12 as InputConsistencyValidator
    participant P13 as ViewConfigCatalogsValidator
    participant P14 as ViewBuildingInput
    participant P15 as Constructor should not read yaml or parquet.     Multi-file inputs are resolved
    participant P16 as ViewConfigTaxonomyValidator
    participant P17 as ViewBuilder
    participant P18 as Inputs of the view-building algorithm for one view config.
    participant P19 as Build a real RawInputData, skipping only the disk-reading Loader.load() step:
    participant P20 as Union of the patterns' location filters, or None if any pattern keeps every loca
    participant P21 as Runs every aggregation pattern of a view config on one metric.      Each distinc
    participant P22 as Study inputs as loaded from disk, before view-building transformations.
    participant P23 as make_view_config()
    participant P24 as Match the filter clause against component properties.
    participant P25 as A port wired to several peers is only ambiguous when more than one of them belon
    participant P26 as Two peers on the same port both belonging to the term's taxonomy category is an
    participant P27 as A location_port resolves to its connected peer component.
    participant P28 as A term with location_port=None means the component is its own location.      Sel
    participant P29 as (component, output) pairs this metric reads from the simulation table.
    participant P30 as Union of (component, output) pairs read by every metric of every view config.
    participant P31 as Attach taxonomy categories and port connections to components.
    participant P32 as Group components by taxonomy category. Requires supply_components_with_taxon
    participant P33 as Return (component_id, port_id) for side idx in {1,2}, handling both:     - par
    participant P34 as One time build which will be used to save information inside component object.
    participant P35 as Precompute each component's metric locations from catalog terms.      Must run a
    participant P36 as make_view_config()
    participant P37 as make_view_config()
    participant P38 as make_view_config()
    participant P39 as make_view_config()
    participant P40 as make_view_config()
    participant P41 as TimeGranularity
    participant P42 as CatalogsTaxonomyValidator
    participant P43 as TimeAggregator
    participant P44 as TermsAggregator
    participant P45 as test_supply_components_with_locations_raises_on_genuine_ambiguity()
    participant P46 as test_none_location_port_resolves_to_the_component_itself()
    participant P47 as make_metric()
    participant P48 as test_terms_aggregation_sum()
    participant P49 as test_terms_aggregation_avg()
    participant P50 as Granular metric-view parquet (output of the terms aggregation step).
    participant P51 as Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, br
    participant P52 as Aggregate a terms-aggregated metric view to time_granularity; return the ela
    participant P53 as test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()
    participant P54 as make_catalog()
    participant P55 as ExtraLocation
    participant P56 as Location
    participant P57 as Scope
    participant P58 as MetricId
    participant P59 as RawViewConfig
    participant P60 as make_catalog()
    participant P61 as make_metrics()
    participant P62 as to_metric()
    participant P63 as make_metric()
    participant P64 as make_metrics()
    participant P65 as ScenarioAggregator
    participant P66 as ScenarioOperator
    participant P67 as ScenarioAggregation
    participant P68 as ScenarioColumnsAddition
    participant P69 as Minimal parquet for the scenario step: metric_id, metric_location, breakdown_pro
    participant P70 as Operator
    participant P71 as make_pattern()
    participant P72 as Apply the location filter, then the scenario operator; return the elapsed second
    participant P73 as make_pattern()
    P0->>+ P1: uses
    P1-->>- P0: return
    P1->>+ P2: uses
    P2-->>- P1: return
    P2->>+ P1: uses
    P1-->>- P2: return
    P2->>+ P3: uses
    P3-->>- P2: return
    P2->>+ P4: uses
    P4-->>- P2: return
    P2->>+ P5: calls
    P5-->>- P2: return
    P2->>+ P6: uses
    P6-->>- P2: return
    P2->>+ P7: uses
    P7-->>- P2: return
    P2->>+ P8: uses
    P8-->>- P2: return
    P2->>+ P9: uses
    P9-->>- P2: return
    P2->>+ P10: uses
    P10-->>- P2: return
    P2->>+ P11: uses
    P11-->>- P2: return
    P2->>+ P12: uses
    P12-->>- P2: return
    P2->>+ P13: uses
    P13-->>- P2: return
    P2->>+ P14: uses
    P14-->>- P2: return
    P2->>+ P15: uses
    P15-->>- P2: return
    P2->>+ P16: uses
    P16-->>- P2: return
    P2->>+ P17: uses
    P17-->>- P2: return
    P2->>+ P18: uses
    P18-->>- P2: return
    P2->>+ P19: uses
    P19-->>- P2: return
    P2->>+ P20: uses
    P20-->>- P2: return
    P2->>+ P21: uses
    P21-->>- P2: return
    P2->>+ P22: uses
    P22-->>- P2: return
    P2->>+ P23: calls
    P23-->>- P2: return
    P2->>+ P24: uses
    P24-->>- P2: return
    P2->>+ P25: uses
    P25-->>- P2: return
    P2->>+ P26: uses
    P26-->>- P2: return
    P2->>+ P27: uses
    P27-->>- P2: return
    P2->>+ P28: uses
    P28-->>- P2: return
    P2->>+ P29: uses
    P29-->>- P2: return
    P2->>+ P30: uses
    P30-->>- P2: return
    P2->>+ P31: uses
    P31-->>- P2: return
    P2->>+ P32: uses
    P32-->>- P2: return
    P2->>+ P33: uses
    P33-->>- P2: return
    P2->>+ P34: uses
    P34-->>- P2: return
    P2->>+ P35: uses
    P35-->>- P2: return
    P2->>+ P36: calls
    P36-->>- P2: return
    P2->>+ P37: calls
    P37-->>- P2: return
    P2->>+ P38: calls
    P38-->>- P2: return
    P2->>+ P39: calls
    P39-->>- P2: return
    P2->>+ P40: calls
    P40-->>- P2: return
    P1->>+ P0: uses
    P0-->>- P1: return
    P1->>+ P3: uses
    P3-->>- P1: return
    P1->>+ P7: uses
    P7-->>- P1: return
    P1->>+ P41: uses
    P41-->>- P1: return
    P1->>+ P42: uses
    P42-->>- P1: return
    P1->>+ P8: uses
    P8-->>- P1: return
    P1->>+ P43: uses
    P43-->>- P1: return
    P1->>+ P9: uses
    P9-->>- P1: return
    P1->>+ P44: uses
    P44-->>- P1: return
    P1->>+ P10: uses
    P10-->>- P1: return
    P1->>+ P45: calls
    P45-->>- P1: return
    P1->>+ P46: calls
    P46-->>- P1: return
    P1->>+ P20: uses
    P20-->>- P1: return
    P1->>+ P21: uses
    P21-->>- P1: return
    P1->>+ P47: calls
    P47-->>- P1: return
    P1->>+ P48: calls
    P48-->>- P1: return
    P1->>+ P49: calls
    P49-->>- P1: return
    P1->>+ P50: uses
    P50-->>- P1: return
    P1->>+ P29: uses
    P29-->>- P1: return
    P1->>+ P30: uses
    P30-->>- P1: return
    P1->>+ P51: uses
    P51-->>- P1: return
    P1->>+ P52: uses
    P52-->>- P1: return
    P1->>+ P53: calls
    P53-->>- P1: return
    P1->>+ P54: calls
    P54-->>- P1: return
    P1->>+ P55: uses
    P55-->>- P1: return
    P1->>+ P56: uses
    P56-->>- P1: return
    P1->>+ P57: uses
    P57-->>- P1: return
    P1->>+ P58: uses
    P58-->>- P1: return
    P1->>+ P59: uses
    P59-->>- P1: return
    P1->>+ P60: calls
    P60-->>- P1: return
    P1->>+ P61: calls
    P61-->>- P1: return
    P1->>+ P62: calls
    P62-->>- P1: return
    P1->>+ P63: calls
    P63-->>- P1: return
    P1->>+ P64: calls
    P64-->>- P1: return
    P0->>+ P4: uses
    P4-->>- P0: return
    P0->>+ P7: uses
    P7-->>- P0: return
    P0->>+ P8: uses
    P8-->>- P0: return
    P0->>+ P65: uses
    P65-->>- P0: return
    P0->>+ P9: uses
    P9-->>- P0: return
    P0->>+ P66: uses
    P66-->>- P0: return
    P0->>+ P67: uses
    P67-->>- P0: return
    P0->>+ P68: uses
    P68-->>- P0: return
    P0->>+ P69: uses
    P69-->>- P0: return
    P0->>+ P20: uses
    P20-->>- P0: return
    P0->>+ P21: uses
    P21-->>- P0: return
    P0->>+ P23: calls
    P23-->>- P0: return
    P0->>+ P24: uses
    P24-->>- P0: return
    P0->>+ P25: uses
    P25-->>- P0: return
    P0->>+ P26: uses
    P26-->>- P0: return
    P0->>+ P27: uses
    P27-->>- P0: return
    P0->>+ P28: uses
    P28-->>- P0: return
    P0->>+ P70: uses
    P70-->>- P0: return
    P0->>+ P71: calls
    P71-->>- P0: return
    P0->>+ P36: calls
    P36-->>- P0: return
    P0->>+ P37: calls
    P37-->>- P0: return
    P0->>+ P72: uses
    P72-->>- P0: return
    P0->>+ P73: calls
    P73-->>- P0: return
    P0->>+ P39: calls
    P39-->>- P0: return
```

## Connections by Relation

### calls
- [[make_view_config()]] `INFERRED`
- [[make_pattern()]] `INFERRED`
- [[make_view_config()]] `INFERRED`
- [[make_view_config()]] `INFERRED`
- [[make_pattern()]] `INFERRED`
- [[make_view_config()]] `INFERRED`

### contains
- [[view_config.py]] `EXTRACTED`

### inherits
- [[ViewBuilderBasedModel]] `EXTRACTED`

### uses
- [[Metric]] `INFERRED`
- [[Catalog]] `INFERRED`
- [[ViewBuilderBasedModel]] `INFERRED`
- [[AggregationPatternList]] `INFERRED`
- [[ScenarioAggregator]] `INFERRED`
- [[Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.]] `INFERRED`
- [[ScenarioOperator]] `INFERRED`
- [[ScenarioAggregation]] `INFERRED`
- [[ScenarioColumnsAddition]] `INFERRED`
- [[Minimal parquet for the scenario step: metric_id, metric_location, breakdown_pro]] `INFERRED`
- [[Union of the patterns' location filters, or None if any pattern keeps every loca]] `INFERRED`
- [[Runs every aggregation pattern of a view config on one metric.      Each distinc]] `INFERRED`
- [[Match the filter clause against component properties.]] `INFERRED`
- [[A port wired to several peers is only ambiguous when more than one of them belon]] `INFERRED`
- [[Two peers on the same port both belonging to the term's taxonomy category is an]] `INFERRED`
- [[A location_port resolves to its connected peer component.]] `INFERRED`
- [[A term with location_port=None means the component is its own location.      Sel]] `INFERRED`
- [[Operator]] `INFERRED`
- [[Apply the location filter, then the scenario operator; return the elapsed second]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*