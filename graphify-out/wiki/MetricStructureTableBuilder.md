# MetricStructureTableBuilder

> God node · 26 connections · [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/metrics_structure_builder.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/metrics_structure_builder.py#L15)

## Call Trace Diagram

```mermaid
sequenceDiagram
    participant P0 as MetricStructureTableBuilder
    participant P1 as ViewConfig
    participant P2 as Metric
    participant P3 as AggregationPattern
    participant P4 as ViewBuilderBasedModel
    participant P5 as TimeGranularity
    participant P6 as CatalogsTaxonomyValidator
    participant P7 as AggregationPatternList
    participant P8 as TimeAggregator
    participant P9 as Terms-aggregated view: 3 locations x 3 scenarios x 48 hours.
    participant P10 as TermsAggregator
    participant P11 as AggregationProcessor
    participant P12 as test_supply_components_with_locations_raises_on_genuine_ambiguity()
    participant P13 as test_none_location_port_resolves_to_the_component_itself()
    participant P14 as Union of the patterns' location filters, or None if any pattern keeps every loca
    participant P15 as Runs every aggregation pattern of a view config on one metric.      Each distinc
    participant P16 as make_metric()
    participant P17 as test_terms_aggregation_sum()
    participant P18 as test_terms_aggregation_avg()
    participant P19 as Granular metric-view parquet (output of the terms aggregation step).
    participant P20 as (component, output) pairs this metric reads from the simulation table.
    participant P21 as Union of (component, output) pairs read by every metric of every view config.
    participant P22 as Step 2.C from POC[temporal aggregation]: Group by metric_id, metric_location, br
    participant P23 as Aggregate a terms-aggregated metric view to time_granularity; return the ela
    participant P24 as test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()
    participant P25 as make_catalog()
    participant P26 as ExtraLocation
    participant P27 as Location
    participant P28 as Scope
    participant P29 as MetricId
    participant P30 as RawViewConfig
    participant P31 as make_catalog()
    participant P32 as make_metrics()
    participant P33 as to_metric()
    participant P34 as make_metric()
    participant P35 as make_metrics()
    participant P36 as Catalog
    participant P37 as load_view_config()
    participant P38 as RawInputData
    participant P39 as ViewConfigMetricsAgainstCatalogsValidator
    participant P40 as InputConsistencyValidator
    participant P41 as ViewConfigCatalogsValidator
    participant P42 as ViewBuildingInput
    participant P43 as Constructor should not read yaml or parquet.     Multi-file inputs are resolved
    participant P44 as ViewConfigTaxonomyValidator
    participant P45 as ViewBuilder
    participant P46 as Inputs of the view-building algorithm for one view config.
    participant P47 as Build a real RawInputData, skipping only the disk-reading Loader.load() step:
    participant P48 as Study inputs as loaded from disk, before view-building transformations.
    participant P49 as make_view_config()
    participant P50 as Match the filter clause against component properties.
    participant P51 as A port wired to several peers is only ambiguous when more than one of them belon
    participant P52 as Two peers on the same port both belonging to the term's taxonomy category is an
    participant P53 as A location_port resolves to its connected peer component.
    participant P54 as A term with location_port=None means the component is its own location.      Sel
    participant P55 as Attach taxonomy categories and port connections to components.
    participant P56 as Group components by taxonomy category. Requires supply_components_with_taxon
    participant P57 as Return (component_id, port_id) for side idx in {1,2}, handling both:     - par
    participant P58 as One time build which will be used to save information inside component object.
    participant P59 as Precompute each component's metric locations from catalog terms.      Must run a
    participant P60 as make_view_config()
    participant P61 as make_view_config()
    participant P62 as make_view_config()
    participant P63 as make_view_config()
    participant P64 as make_view_config()
    participant P65 as Component
    participant P66 as test_breakdown_missing_property_keys_use_none_literal()
    participant P67 as MetricStructureTable
    participant P68 as Term
    participant P69 as build()
    participant P70 as collect_needed_pairs()
    participant P71 as test_located_component_emits_primary_and_extra_locations()
    participant P72 as test_no_extra_locations_keeps_primary_only()
    participant P73 as test_missing_extra_properties_keeps_primary_only()
    participant P74 as test_partial_extra_locations_emits_only_present_ones()
    participant P75 as create_view_building_input()
    P0->>+ P1: uses
    P1-->>- P0: return
    P1->>+ P2: uses
    P2-->>- P1: return
    P2->>+ P1: uses
    P1-->>- P2: return
    P2->>+ P3: uses
    P3-->>- P2: return
    P2->>+ P0: uses
    P0-->>- P2: return
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
    P2->>+ P12: calls
    P12-->>- P2: return
    P2->>+ P13: calls
    P13-->>- P2: return
    P2->>+ P14: uses
    P14-->>- P2: return
    P2->>+ P15: uses
    P15-->>- P2: return
    P2->>+ P16: calls
    P16-->>- P2: return
    P2->>+ P17: calls
    P17-->>- P2: return
    P2->>+ P18: calls
    P18-->>- P2: return
    P2->>+ P19: uses
    P19-->>- P2: return
    P2->>+ P20: uses
    P20-->>- P2: return
    P2->>+ P21: uses
    P21-->>- P2: return
    P2->>+ P22: uses
    P22-->>- P2: return
    P2->>+ P23: uses
    P23-->>- P2: return
    P2->>+ P24: calls
    P24-->>- P2: return
    P2->>+ P25: calls
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
    P2->>+ P31: calls
    P31-->>- P2: return
    P2->>+ P32: calls
    P32-->>- P2: return
    P2->>+ P33: calls
    P33-->>- P2: return
    P2->>+ P34: calls
    P34-->>- P2: return
    P2->>+ P35: calls
    P35-->>- P2: return
    P1->>+ P0: uses
    P0-->>- P1: return
    P1->>+ P36: uses
    P36-->>- P1: return
    P1->>+ P37: calls
    P37-->>- P1: return
    P1->>+ P38: uses
    P38-->>- P1: return
    P1->>+ P4: uses
    P4-->>- P1: return
    P1->>+ P7: uses
    P7-->>- P1: return
    P1->>+ P9: uses
    P9-->>- P1: return
    P1->>+ P11: uses
    P11-->>- P1: return
    P1->>+ P39: uses
    P39-->>- P1: return
    P1->>+ P40: uses
    P40-->>- P1: return
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
    P1->>+ P14: uses
    P14-->>- P1: return
    P1->>+ P15: uses
    P15-->>- P1: return
    P1->>+ P48: uses
    P48-->>- P1: return
    P1->>+ P49: calls
    P49-->>- P1: return
    P1->>+ P50: uses
    P50-->>- P1: return
    P1->>+ P51: uses
    P51-->>- P1: return
    P1->>+ P52: uses
    P52-->>- P1: return
    P1->>+ P53: uses
    P53-->>- P1: return
    P1->>+ P54: uses
    P54-->>- P1: return
    P1->>+ P20: uses
    P20-->>- P1: return
    P1->>+ P21: uses
    P21-->>- P1: return
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
    P0->>+ P65: uses
    P65-->>- P0: return
    P0->>+ P2: uses
    P2-->>- P0: return
    P0->>+ P66: calls
    P66-->>- P0: return
    P0->>+ P67: uses
    P67-->>- P0: return
    P0->>+ P68: uses
    P68-->>- P0: return
    P0->>+ P69: calls
    P69-->>- P0: return
    P0->>+ P42: uses
    P42-->>- P0: return
    P0->>+ P46: uses
    P46-->>- P0: return
    P0->>+ P13: calls
    P13-->>- P0: return
    P0->>+ P70: calls
    P70-->>- P0: return
    P0->>+ P50: uses
    P50-->>- P0: return
    P0->>+ P51: uses
    P51-->>- P0: return
    P0->>+ P52: uses
    P52-->>- P0: return
    P0->>+ P53: uses
    P53-->>- P0: return
    P0->>+ P54: uses
    P54-->>- P0: return
    P0->>+ P24: calls
    P24-->>- P0: return
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
- [[test_breakdown_missing_property_keys_use_none_literal()]] `INFERRED`
- [[build()]] `INFERRED`
- [[test_none_location_port_resolves_to_the_component_itself()]] `INFERRED`
- [[collect_needed_pairs()]] `EXTRACTED`
- [[test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()]] `INFERRED`
- [[test_located_component_emits_primary_and_extra_locations()]] `INFERRED`
- [[test_no_extra_locations_keeps_primary_only()]] `INFERRED`
- [[test_missing_extra_properties_keeps_primary_only()]] `INFERRED`
- [[test_partial_extra_locations_emits_only_present_ones()]] `INFERRED`
- [[create_view_building_input()]] `INFERRED`

### contains
- [[metrics_structure_builder.py]] `EXTRACTED`

### method
- [[.build()]] `EXTRACTED`
- [[.matching_components()]] `EXTRACTED`
- [[.needed_pairs()]] `EXTRACTED`

### uses
- [[ViewConfig]] `INFERRED`
- [[Component]] `INFERRED`
- [[Metric]] `INFERRED`
- [[MetricStructureTable]] `INFERRED`
- [[Term]] `INFERRED`
- [[ViewBuildingInput]] `INFERRED`
- [[Inputs of the view-building algorithm for one view config.]] `INFERRED`
- [[Match the filter clause against component properties.]] `INFERRED`
- [[A port wired to several peers is only ambiguous when more than one of them belon]] `INFERRED`
- [[Two peers on the same port both belonging to the term's taxonomy category is an]] `INFERRED`
- [[A location_port resolves to its connected peer component.]] `INFERRED`
- [[A term with location_port=None means the component is its own location.      Sel]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*