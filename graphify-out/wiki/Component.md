# Component

> God node · 39 connections · [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/component/component.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/component/component.py#L15)

## Call Trace Diagram

```mermaid
sequenceDiagram
    participant P0 as Component
    participant P1 as MetricStructureTableBuilder
    participant P2 as ViewConfig
    participant P3 as Metric
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
    participant P41 as test_breakdown_missing_property_keys_use_none_literal()
    participant P42 as MetricStructureTable
    participant P43 as Term
    participant P44 as build()
    participant P45 as test_none_location_port_resolves_to_the_component_itself()
    participant P46 as collect_needed_pairs()
    participant P47 as test_single_port_multiple_peers_of_other_categories_are_skipped_not_raised()
    participant P48 as test_located_component_emits_primary_and_extra_locations()
    participant P49 as test_no_extra_locations_keeps_primary_only()
    participant P50 as test_missing_extra_properties_keeps_primary_only()
    participant P51 as test_partial_extra_locations_emits_only_present_ones()
    participant P52 as create_view_building_input()
    participant P53 as ConnectionsThroughPort
    participant P54 as PropertySchema
    participant P55 as build_components_by_taxonomy_category()
    participant P56 as test_location_none_returns_own_component()
    participant P57 as make_component()
    participant P58 as make_component()
    participant P59 as test_match()
    participant P60 as test_match_extra_locations_reads_own_properties()
    participant P61 as test_supply_components_with_taxon()
    participant P62 as test_group_components_by_taxonomy_category()
    participant P63 as create_components()
    participant P64 as gas_1 declares technology then company; gas_2 declares company then technology.
    participant P65 as Per scenario, the (gas, rhonepower) view bucket must equal the sum of gas_1 and
    participant P66 as gen_company_only declares company only; country and technology are absent.     B
    participant P67 as Peer components connected to a component on a given port.
    P0->>+ P1: uses
    P1-->>- P0: return
    P1->>+ P2: uses
    P2-->>- P1: return
    P2->>+ P3: uses
    P3-->>- P2: return
    P2->>+ P1: uses
    P1-->>- P2: return
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
    P1->>+ P41: calls
    P41-->>- P1: return
    P1->>+ P42: uses
    P42-->>- P1: return
    P1->>+ P43: uses
    P43-->>- P1: return
    P1->>+ P44: calls
    P44-->>- P1: return
    P1->>+ P14: uses
    P14-->>- P1: return
    P1->>+ P18: uses
    P18-->>- P1: return
    P1->>+ P45: calls
    P45-->>- P1: return
    P1->>+ P46: calls
    P46-->>- P1: return
    P1->>+ P24: uses
    P24-->>- P1: return
    P1->>+ P25: uses
    P25-->>- P1: return
    P1->>+ P26: uses
    P26-->>- P1: return
    P1->>+ P27: uses
    P27-->>- P1: return
    P1->>+ P28: uses
    P28-->>- P1: return
    P1->>+ P47: calls
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
    P0->>+ P41: calls
    P41-->>- P0: return
    P0->>+ P53: uses
    P53-->>- P0: return
    P0->>+ P54: uses
    P54-->>- P0: return
    P0->>+ P14: uses
    P14-->>- P0: return
    P0->>+ P55: calls
    P55-->>- P0: return
    P0->>+ P18: uses
    P18-->>- P0: return
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
    P0->>+ P29: uses
    P29-->>- P0: return
    P0->>+ P30: uses
    P30-->>- P0: return
    P0->>+ P56: calls
    P56-->>- P0: return
    P0->>+ P57: calls
    P57-->>- P0: return
    P0->>+ P58: calls
    P58-->>- P0: return
    P0->>+ P31: uses
    P31-->>- P0: return
    P0->>+ P32: uses
    P32-->>- P0: return
    P0->>+ P33: uses
    P33-->>- P0: return
    P0->>+ P34: uses
    P34-->>- P0: return
    P0->>+ P35: uses
    P35-->>- P0: return
    P0->>+ P59: calls
    P59-->>- P0: return
    P0->>+ P60: calls
    P60-->>- P0: return
    P0->>+ P61: calls
    P61-->>- P0: return
    P0->>+ P62: calls
    P62-->>- P0: return
    P0->>+ P63: calls
    P63-->>- P0: return
    P0->>+ P64: uses
    P64-->>- P0: return
    P0->>+ P65: uses
    P65-->>- P0: return
    P0->>+ P66: uses
    P66-->>- P0: return
    P0->>+ P67: uses
    P67-->>- P0: return
```

## Connections by Relation

### calls
- [[test_breakdown_missing_property_keys_use_none_literal()]] `INFERRED`
- [[build_components_by_taxonomy_category()]] `INFERRED`
- [[test_location_none_returns_own_component()]] `INFERRED`
- [[make_component()]] `INFERRED`
- [[make_component()]] `INFERRED`
- [[test_match()]] `INFERRED`
- [[test_match_extra_locations_reads_own_properties()]] `INFERRED`
- [[test_supply_components_with_taxon()]] `INFERRED`
- [[test_group_components_by_taxonomy_category()]] `INFERRED`
- [[create_components()]] `INFERRED`

### contains
- [[component.py]] `EXTRACTED`

### method
- [[.format_breakdown_properties()]] `EXTRACTED`
- [[.location()]] `EXTRACTED`
- [[.match_extra_locations()]] `EXTRACTED`
- [[.is_located_at()]] `EXTRACTED`
- [[.match()]] `EXTRACTED`
- [[.set_taxonomy_category()]] `EXTRACTED`

### rationale_for
- [[Each component hold raw data from real component used for building additional fi]] `EXTRACTED`

### uses
- [[MetricStructureTableBuilder]] `INFERRED`
- [[ConnectionsThroughPort]] `INFERRED`
- [[PropertySchema]] `INFERRED`
- [[ViewBuildingInput]] `INFERRED`
- [[Inputs of the view-building algorithm for one view config.]] `INFERRED`
- [[Match the filter clause against component properties.]] `INFERRED`
- [[A port wired to several peers is only ambiguous when more than one of them belon]] `INFERRED`
- [[Two peers on the same port both belonging to the term's taxonomy category is an]] `INFERRED`
- [[A location_port resolves to its connected peer component.]] `INFERRED`
- [[A term with location_port=None means the component is its own location.      Sel]] `INFERRED`
- [[(component, output) pairs this metric reads from the simulation table.]] `INFERRED`
- [[Union of (component, output) pairs read by every metric of every view config.]] `INFERRED`
- [[Attach taxonomy categories and port connections to components.]] `INFERRED`
- [[Group components by taxonomy category. Requires ``supply_components_with_taxon``]] `INFERRED`
- [[Return (component_id, port_id) for side `idx` in {1,2}, handling both:     - par]] `INFERRED`
- [[One time build which will be used to save information inside component object.]] `INFERRED`
- [[Precompute each component's metric locations from catalog terms.      Must run a]] `INFERRED`
- [[gas_1 declares technology then company; gas_2 declares company then technology.]] `INFERRED`
- [[Per scenario, the (gas, rhonepower) view bucket must equal the sum of gas_1 and]] `INFERRED`
- [[gen_company_only declares company only; country and technology are absent.     B]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*