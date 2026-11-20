# Metric

> God node · 36 connections · [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/catalog.py#L86)

## Call Trace Diagram

```mermaid
sequenceDiagram
    participant P0 as Metric
    participant P1 as ViewConfig
    participant P2 as MetricStructureTableBuilder
    participant P3 as Component
    participant P4 as test_breakdown_missing_property_keys_use_none_literal()
    participant P5 as MetricStructureTable
    participant P6 as Term
    participant P7 as build()
    participant P8 as ViewBuildingInput
    participant P9 as Inputs of the view-building algorithm for one view config.
    participant P10 as test_none_location_port_resolves_to_the_component_itself()
    participant P11 as collect_needed_pairs()
    participant P12 as Match the filter clause against component properties.
    participant P13 as A port wired to several peers is only ambiguous when more than one of them belon
    participant P14 as Two peers on the same port both belonging to the term's taxonomy category is an
    participant P15 as A location_port resolves to its connected peer component.
    participant P16 as A term with location_port=None means the component is its own location.      Sel
    participant P17 as test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()
    participant P18 as test_located_component_emits_primary_and_extra_locations()
    participant P19 as test_no_extra_locations_keeps_primary_only()
    participant P20 as test_missing_extra_properties_keeps_primary_only()
    participant P21 as test_partial_extra_locations_emits_only_present_ones()
    participant P22 as create_view_building_input()
    participant P23 as Catalog
    participant P24 as load_view_config()
    participant P25 as RawInputData
    participant P26 as ViewBuilderBasedModel
    participant P27 as AggregationPatternList
    participant P28 as Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.
    participant P29 as AggregationProcessor
    participant P30 as ViewConfigMetricsAgainstCatalogsValidator
    participant P31 as InputConsistencyValidator
    participant P32 as ViewConfigCatalogsValidator
    participant P33 as Constructor should not read yaml or parquet.     Multi-file inputs are resolved
    participant P34 as ViewConfigTaxonomyValidator
    participant P35 as ViewBuilder
    participant P36 as Build a real RawInputData, skipping only the disk-reading Loader.load() step:
    participant P37 as Union of the patterns' location filters, or None if any pattern keeps every loca
    participant P38 as Runs every aggregation pattern of a view config on one metric.      Each distinc
    participant P39 as Study inputs as loaded from disk, before view-building transformations.
    participant P40 as make_view_config()
    participant P41 as (component, output) pairs this metric reads from the simulation table.
    participant P42 as Union of (component, output) pairs read by every metric of every view config.
    participant P43 as Attach taxonomy categories and port connections to components.
    participant P44 as Group components by taxonomy category. Requires supply_components_with_taxon
    participant P45 as Return (component_id, port_id) for side idx in {1,2}, handling both:     - par
    participant P46 as One time build which will be used to save information inside component object.
    participant P47 as Precompute each component's metric locations from catalog terms.      Must run a
    participant P48 as make_view_config()
    participant P49 as make_view_config()
    participant P50 as make_view_config()
    participant P51 as make_view_config()
    participant P52 as make_view_config()
    participant P53 as AggregationPattern
    participant P54 as TimeGranularity
    participant P55 as CatalogsTaxonomyValidator
    participant P56 as TimeAggregator
    participant P57 as TermsAggregator
    participant P58 as test_supply_components_with_locations_raises_on_genuine_ambiguity()
    participant P59 as make_metric()
    participant P60 as test_terms_aggregation_sum()
    participant P61 as test_terms_aggregation_avg()
    participant P62 as Granular metric-view parquet (output of the terms aggregation step).
    participant P63 as Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, br
    participant P64 as Aggregate a terms-aggregated metric view to time_granularity; return the ela
    participant P65 as make_catalog()
    participant P66 as ExtraLocation
    participant P67 as Location
    participant P68 as Scope
    participant P69 as MetricId
    participant P70 as RawViewConfig
    participant P71 as make_catalog()
    participant P72 as make_metrics()
    participant P73 as to_metric()
    participant P74 as make_metric()
    participant P75 as make_metrics()
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
    P2->>+ P0: uses
    P0-->>- P2: return
    P2->>+ P4: calls
    P4-->>- P2: return
    P2->>+ P5: uses
    P5-->>- P2: return
    P2->>+ P6: uses
    P6-->>- P2: return
    P2->>+ P7: calls
    P7-->>- P2: return
    P2->>+ P8: uses
    P8-->>- P2: return
    P2->>+ P9: uses
    P9-->>- P2: return
    P2->>+ P10: calls
    P10-->>- P2: return
    P2->>+ P11: calls
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
    P2->>+ P17: calls
    P17-->>- P2: return
    P2->>+ P18: calls
    P18-->>- P2: return
    P2->>+ P19: calls
    P19-->>- P2: return
    P2->>+ P20: calls
    P20-->>- P2: return
    P2->>+ P21: calls
    P21-->>- P2: return
    P2->>+ P22: calls
    P22-->>- P2: return
    P1->>+ P23: uses
    P23-->>- P1: return
    P1->>+ P24: calls
    P24-->>- P1: return
    P1->>+ P25: uses
    P25-->>- P1: return
    P1->>+ P26: uses
    P26-->>- P1: return
    P1->>+ P27: uses
    P27-->>- P1: return
    P1->>+ P28: uses
    P28-->>- P1: return
    P1->>+ P29: uses
    P29-->>- P1: return
    P1->>+ P30: uses
    P30-->>- P1: return
    P1->>+ P31: uses
    P31-->>- P1: return
    P1->>+ P32: uses
    P32-->>- P1: return
    P1->>+ P8: uses
    P8-->>- P1: return
    P1->>+ P33: uses
    P33-->>- P1: return
    P1->>+ P34: uses
    P34-->>- P1: return
    P1->>+ P35: uses
    P35-->>- P1: return
    P1->>+ P9: uses
    P9-->>- P1: return
    P1->>+ P36: uses
    P36-->>- P1: return
    P1->>+ P37: uses
    P37-->>- P1: return
    P1->>+ P38: uses
    P38-->>- P1: return
    P1->>+ P39: uses
    P39-->>- P1: return
    P1->>+ P40: calls
    P40-->>- P1: return
    P1->>+ P12: uses
    P12-->>- P1: return
    P1->>+ P13: uses
    P13-->>- P1: return
    P1->>+ P14: uses
    P14-->>- P1: return
    P1->>+ P15: uses
    P15-->>- P1: return
    P1->>+ P16: uses
    P16-->>- P1: return
    P1->>+ P41: uses
    P41-->>- P1: return
    P1->>+ P42: uses
    P42-->>- P1: return
    P1->>+ P43: uses
    P43-->>- P1: return
    P1->>+ P44: uses
    P44-->>- P1: return
    P1->>+ P45: uses
    P45-->>- P1: return
    P1->>+ P46: uses
    P46-->>- P1: return
    P1->>+ P47: uses
    P47-->>- P1: return
    P1->>+ P48: calls
    P48-->>- P1: return
    P1->>+ P49: calls
    P49-->>- P1: return
    P1->>+ P50: calls
    P50-->>- P1: return
    P1->>+ P51: calls
    P51-->>- P1: return
    P1->>+ P52: calls
    P52-->>- P1: return
    P0->>+ P53: uses
    P53-->>- P0: return
    P0->>+ P2: uses
    P2-->>- P0: return
    P0->>+ P26: uses
    P26-->>- P0: return
    P0->>+ P54: uses
    P54-->>- P0: return
    P0->>+ P55: uses
    P55-->>- P0: return
    P0->>+ P27: uses
    P27-->>- P0: return
    P0->>+ P56: uses
    P56-->>- P0: return
    P0->>+ P28: uses
    P28-->>- P0: return
    P0->>+ P57: uses
    P57-->>- P0: return
    P0->>+ P29: uses
    P29-->>- P0: return
    P0->>+ P58: calls
    P58-->>- P0: return
    P0->>+ P10: calls
    P10-->>- P0: return
    P0->>+ P37: uses
    P37-->>- P0: return
    P0->>+ P38: uses
    P38-->>- P0: return
    P0->>+ P59: calls
    P59-->>- P0: return
    P0->>+ P60: calls
    P60-->>- P0: return
    P0->>+ P61: calls
    P61-->>- P0: return
    P0->>+ P62: uses
    P62-->>- P0: return
    P0->>+ P41: uses
    P41-->>- P0: return
    P0->>+ P42: uses
    P42-->>- P0: return
    P0->>+ P63: uses
    P63-->>- P0: return
    P0->>+ P64: uses
    P64-->>- P0: return
    P0->>+ P17: calls
    P17-->>- P0: return
    P0->>+ P65: calls
    P65-->>- P0: return
    P0->>+ P66: uses
    P66-->>- P0: return
    P0->>+ P67: uses
    P67-->>- P0: return
    P0->>+ P68: uses
    P68-->>- P0: return
    P0->>+ P69: uses
    P69-->>- P0: return
    P0->>+ P70: uses
    P70-->>- P0: return
    P0->>+ P71: calls
    P71-->>- P0: return
    P0->>+ P72: calls
    P72-->>- P0: return
    P0->>+ P73: calls
    P73-->>- P0: return
    P0->>+ P74: calls
    P74-->>- P0: return
    P0->>+ P75: calls
    P75-->>- P0: return
```

## Connections by Relation

### calls
- [[test_supply_components_with_locations_raises_on_genuine_ambiguity()]] `INFERRED`
- [[test_none_location_port_resolves_to_the_component_itself()]] `INFERRED`
- [[make_metric()]] `INFERRED`
- [[test_terms_aggregation_sum()]] `INFERRED`
- [[test_terms_aggregation_avg()]] `INFERRED`
- [[test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()]] `INFERRED`
- [[make_catalog()]] `INFERRED`
- [[make_catalog()]] `INFERRED`
- [[make_metrics()]] `INFERRED`
- [[to_metric()]] `EXTRACTED`
- [[make_metric()]] `INFERRED`
- [[make_metrics()]] `INFERRED`

### contains
- [[catalog.py]] `EXTRACTED`

### uses
- [[ViewConfig]] `INFERRED`
- [[AggregationPattern]] `INFERRED`
- [[MetricStructureTableBuilder]] `INFERRED`
- [[ViewBuilderBasedModel]] `INFERRED`
- [[TimeGranularity]] `INFERRED`
- [[CatalogsTaxonomyValidator]] `INFERRED`
- [[AggregationPatternList]] `INFERRED`
- [[TimeAggregator]] `INFERRED`
- [[Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.]] `INFERRED`
- [[TermsAggregator]] `INFERRED`
- [[AggregationProcessor]] `INFERRED`
- [[Union of the patterns' location filters, or None if any pattern keeps every loca]] `INFERRED`
- [[Runs every aggregation pattern of a view config on one metric.      Each distinc]] `INFERRED`
- [[Granular metric-view parquet (output of the terms aggregation step).]] `INFERRED`
- [[(component, output) pairs this metric reads from the simulation table.]] `INFERRED`
- [[Union of (component, output) pairs read by every metric of every view config.]] `INFERRED`
- [[Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, br]] `INFERRED`
- [[Aggregate a terms-aggregated metric view to ``time_granularity``; return the ela]] `INFERRED`
- [[ExtraLocation]] `INFERRED`
- [[Location]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*