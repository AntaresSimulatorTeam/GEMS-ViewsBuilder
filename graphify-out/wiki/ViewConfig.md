# ViewConfig

> God node · 42 connections · [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py#L59)

## Call Trace Diagram

```mermaid
sequenceDiagram
    participant P0 as ViewConfig
    participant P1 as Metric
    participant P2 as AggregationPattern
    participant P3 as Catalog
    participant P4 as ViewBuilderBasedModel
    participant P5 as AggregationPatternList
    participant P6 as ScenarioAggregator
    participant P7 as Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.
    participant P8 as ScenarioOperator
    participant P9 as ScenarioAggregation
    participant P10 as ScenarioColumnsAddition
    participant P11 as Minimal parquet for the scenario step: metric_id, metric_location, breakdown_pro
    participant P12 as Union of the patterns' location filters, or None if any pattern keeps every loca
    participant P13 as Runs every aggregation pattern of a view config on one metric.      Each distinc
    participant P14 as make_view_config()
    participant P15 as Match the filter clause against component properties.
    participant P16 as A port wired to several peers is only ambiguous when more than one of them belon
    participant P17 as Two peers on the same port both belonging to the term's taxonomy category is an
    participant P18 as A location_port resolves to its connected peer component.
    participant P19 as A term with location_port=None means the component is its own location.      Sel
    participant P20 as Operator
    participant P21 as make_pattern()
    participant P22 as make_view_config()
    participant P23 as make_view_config()
    participant P24 as Apply the location filter, then the scenario operator; return the elapsed second
    participant P25 as make_pattern()
    participant P26 as make_view_config()
    participant P27 as MetricStructureTableBuilder
    participant P28 as TimeGranularity
    participant P29 as CatalogsTaxonomyValidator
    participant P30 as TimeAggregator
    participant P31 as TermsAggregator
    participant P32 as AggregationProcessor
    participant P33 as test_supply_components_with_locations_raises_on_genuine_ambiguity()
    participant P34 as test_none_location_port_resolves_to_the_component_itself()
    participant P35 as make_metric()
    participant P36 as test_terms_aggregation_sum()
    participant P37 as test_terms_aggregation_avg()
    participant P38 as Granular metric-view parquet (output of the terms aggregation step).
    participant P39 as (component, output) pairs this metric reads from the simulation table.
    participant P40 as Union of (component, output) pairs read by every metric of every view config.
    participant P41 as Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, br
    participant P42 as Aggregate a terms-aggregated metric view to time_granularity; return the ela
    participant P43 as test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()
    participant P44 as make_catalog()
    participant P45 as ExtraLocation
    participant P46 as Location
    participant P47 as Scope
    participant P48 as MetricId
    participant P49 as RawViewConfig
    participant P50 as make_catalog()
    participant P51 as make_metrics()
    participant P52 as to_metric()
    participant P53 as make_metric()
    participant P54 as make_metrics()
    participant P55 as load_view_config()
    participant P56 as RawInputData
    participant P57 as ViewConfigMetricsAgainstCatalogsValidator
    participant P58 as InputConsistencyValidator
    participant P59 as ViewConfigCatalogsValidator
    participant P60 as ViewBuildingInput
    participant P61 as Constructor should not read yaml or parquet.     Multi-file inputs are resolved
    participant P62 as ViewConfigTaxonomyValidator
    participant P63 as ViewBuilder
    participant P64 as Inputs of the view-building algorithm for one view config.
    participant P65 as Build a real RawInputData, skipping only the disk-reading Loader.load() step:
    participant P66 as Study inputs as loaded from disk, before view-building transformations.
    participant P67 as Attach taxonomy categories and port connections to components.
    participant P68 as Group components by taxonomy category. Requires supply_components_with_taxon
    participant P69 as Return (component_id, port_id) for side idx in {1,2}, handling both:     - par
    participant P70 as One time build which will be used to save information inside component object.
    participant P71 as Precompute each component's metric locations from catalog terms.      Must run a
    participant P72 as make_view_config()
    participant P73 as make_view_config()
    P0->>+ P1: uses
    P1-->>- P0: return
    P1->>+ P0: uses
    P0-->>- P1: return
    P1->>+ P2: uses
    P2-->>- P1: return
    P2->>+ P1: uses
    P1-->>- P2: return
    P2->>+ P3: uses
    P3-->>- P2: return
    P2->>+ P4: uses
    P4-->>- P2: return
    P2->>+ P5: uses
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
    P2->>+ P14: calls
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
    P2->>+ P21: calls
    P21-->>- P2: return
    P2->>+ P22: calls
    P22-->>- P2: return
    P2->>+ P23: calls
    P23-->>- P2: return
    P2->>+ P24: uses
    P24-->>- P2: return
    P2->>+ P25: calls
    P25-->>- P2: return
    P2->>+ P26: calls
    P26-->>- P2: return
    P1->>+ P27: uses
    P27-->>- P1: return
    P1->>+ P4: uses
    P4-->>- P1: return
    P1->>+ P28: uses
    P28-->>- P1: return
    P1->>+ P29: uses
    P29-->>- P1: return
    P1->>+ P5: uses
    P5-->>- P1: return
    P1->>+ P30: uses
    P30-->>- P1: return
    P1->>+ P7: uses
    P7-->>- P1: return
    P1->>+ P31: uses
    P31-->>- P1: return
    P1->>+ P32: uses
    P32-->>- P1: return
    P1->>+ P33: calls
    P33-->>- P1: return
    P1->>+ P34: calls
    P34-->>- P1: return
    P1->>+ P12: uses
    P12-->>- P1: return
    P1->>+ P13: uses
    P13-->>- P1: return
    P1->>+ P35: calls
    P35-->>- P1: return
    P1->>+ P36: calls
    P36-->>- P1: return
    P1->>+ P37: calls
    P37-->>- P1: return
    P1->>+ P38: uses
    P38-->>- P1: return
    P1->>+ P39: uses
    P39-->>- P1: return
    P1->>+ P40: uses
    P40-->>- P1: return
    P1->>+ P41: uses
    P41-->>- P1: return
    P1->>+ P42: uses
    P42-->>- P1: return
    P1->>+ P43: calls
    P43-->>- P1: return
    P1->>+ P44: calls
    P44-->>- P1: return
    P1->>+ P45: uses
    P45-->>- P1: return
    P1->>+ P46: uses
    P46-->>- P1: return
    P1->>+ P47: uses
    P47-->>- P1: return
    P1->>+ P48: uses
    P48-->>- P1: return
    P1->>+ P49: uses
    P49-->>- P1: return
    P1->>+ P50: calls
    P50-->>- P1: return
    P1->>+ P51: calls
    P51-->>- P1: return
    P1->>+ P52: calls
    P52-->>- P1: return
    P1->>+ P53: calls
    P53-->>- P1: return
    P1->>+ P54: calls
    P54-->>- P1: return
    P0->>+ P27: uses
    P27-->>- P0: return
    P0->>+ P3: uses
    P3-->>- P0: return
    P0->>+ P55: calls
    P55-->>- P0: return
    P0->>+ P56: uses
    P56-->>- P0: return
    P0->>+ P4: uses
    P4-->>- P0: return
    P0->>+ P5: uses
    P5-->>- P0: return
    P0->>+ P7: uses
    P7-->>- P0: return
    P0->>+ P32: uses
    P32-->>- P0: return
    P0->>+ P57: uses
    P57-->>- P0: return
    P0->>+ P58: uses
    P58-->>- P0: return
    P0->>+ P59: uses
    P59-->>- P0: return
    P0->>+ P60: uses
    P60-->>- P0: return
    P0->>+ P61: uses
    P61-->>- P0: return
    P0->>+ P62: uses
    P62-->>- P0: return
    P0->>+ P63: uses
    P63-->>- P0: return
    P0->>+ P64: uses
    P64-->>- P0: return
    P0->>+ P65: uses
    P65-->>- P0: return
    P0->>+ P12: uses
    P12-->>- P0: return
    P0->>+ P13: uses
    P13-->>- P0: return
    P0->>+ P66: uses
    P66-->>- P0: return
    P0->>+ P14: calls
    P14-->>- P0: return
    P0->>+ P15: uses
    P15-->>- P0: return
    P0->>+ P16: uses
    P16-->>- P0: return
    P0->>+ P17: uses
    P17-->>- P0: return
    P0->>+ P18: uses
    P18-->>- P0: return
    P0->>+ P19: uses
    P19-->>- P0: return
    P0->>+ P39: uses
    P39-->>- P0: return
    P0->>+ P40: uses
    P40-->>- P0: return
    P0->>+ P67: uses
    P67-->>- P0: return
    P0->>+ P68: uses
    P68-->>- P0: return
    P0->>+ P69: uses
    P69-->>- P0: return
    P0->>+ P70: uses
    P70-->>- P0: return
    P0->>+ P71: uses
    P71-->>- P0: return
    P0->>+ P22: calls
    P22-->>- P0: return
    P0->>+ P23: calls
    P23-->>- P0: return
    P0->>+ P72: calls
    P72-->>- P0: return
    P0->>+ P26: calls
    P26-->>- P0: return
    P0->>+ P73: calls
    P73-->>- P0: return
```

## Connections by Relation

### calls
- [[load_view_config()]] `EXTRACTED`
- [[make_view_config()]] `INFERRED`
- [[make_view_config()]] `INFERRED`
- [[make_view_config()]] `INFERRED`
- [[make_view_config()]] `INFERRED`
- [[make_view_config()]] `INFERRED`
- [[make_view_config()]] `INFERRED`

### contains
- [[view_config.py]] `EXTRACTED`

### method
- [[.populate_with_metrics()]] `EXTRACTED`
- [[.get_metrics()]] `EXTRACTED`

### uses
- [[Metric]] `INFERRED`
- [[MetricStructureTableBuilder]] `INFERRED`
- [[Catalog]] `INFERRED`
- [[RawInputData]] `INFERRED`
- [[ViewBuilderBasedModel]] `INFERRED`
- [[AggregationPatternList]] `INFERRED`
- [[Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.]] `INFERRED`
- [[AggregationProcessor]] `INFERRED`
- [[ViewConfigMetricsAgainstCatalogsValidator]] `INFERRED`
- [[InputConsistencyValidator]] `INFERRED`
- [[ViewConfigCatalogsValidator]] `INFERRED`
- [[ViewBuildingInput]] `INFERRED`
- [[Constructor should not read yaml or parquet.     Multi-file inputs are resolved]] `INFERRED`
- [[ViewConfigTaxonomyValidator]] `INFERRED`
- [[ViewBuilder]] `INFERRED`
- [[Inputs of the view-building algorithm for one view config.]] `INFERRED`
- [[Build a real RawInputData, skipping only the disk-reading Loader.load() step:]] `INFERRED`
- [[Union of the patterns' location filters, or None if any pattern keeps every loca]] `INFERRED`
- [[Runs every aggregation pattern of a view config on one metric.      Each distinc]] `INFERRED`
- [[Study inputs as loaded from disk, before view-building transformations.]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*