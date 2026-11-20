# SimulationTable

> God node · 23 connections · [/home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/simulation_table.py](file:///home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/simulation_table.py#L51)

## Call Trace Diagram

```mermaid
sequenceDiagram
    participant P0 as SimulationTable
    participant P1 as RawInputData
    participant P2 as ViewConfig
    participant P3 as Metric
    participant P4 as MetricStructureTableBuilder
    participant P5 as Catalog
    participant P6 as load_view_config()
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
    participant P41 as Calendar
    participant P42 as .load()
    participant P43 as Loader
    participant P44 as Library
    participant P45 as System
    participant P46 as build_raw_input_data()
    participant P47 as Perform all input data I/O and return the loaded raw input data.
    participant P48 as MetricStructureTable
    participant P49 as load_simulation_table()
    participant P50 as test_filter_simulation_table_keeps_calendar_matching_rows_from_every_table()
    participant P51 as test_validate_simulation_tables_consistency_fails_when_there_are_missing_columns()
    participant P52 as make_simulation_table()
    participant P53 as test_concat_simulation_tables_combines_rows_from_every_table()
    participant P54 as test_validate_simulation_tables_consistency_pass()
    participant P55 as When a non-parquet, non-csv file is provided, an error is raised.
    participant P56 as Rows with a null component or output can never be needed by a metric.
    participant P57 as Replace (component, output) by their pair_id, like the filtered table does.
    participant P58 as Filtered result must satisfy: every row (absolute_time_index, block) in calendar
    participant P59 as Rows whose block does not match the calendar's block for a given absolute_time_i
    participant P60 as The filtered table is written to parquet with expected content.
    P0->>+ P1: uses
    P1-->>- P0: return
    P1->>+ P2: uses
    P2-->>- P1: return
    P2->>+ P3: uses
    P3-->>- P2: return
    P2->>+ P4: uses
    P4-->>- P2: return
    P2->>+ P5: uses
    P5-->>- P2: return
    P2->>+ P6: calls
    P6-->>- P2: return
    P2->>+ P1: uses
    P1-->>- P2: return
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
    P1->>+ P5: uses
    P5-->>- P1: return
    P1->>+ P0: uses
    P0-->>- P1: return
    P1->>+ P41: uses
    P41-->>- P1: return
    P1->>+ P42: calls
    P42-->>- P1: return
    P1->>+ P12: uses
    P12-->>- P1: return
    P1->>+ P14: uses
    P14-->>- P1: return
    P1->>+ P15: uses
    P15-->>- P1: return
    P1->>+ P43: uses
    P43-->>- P1: return
    P1->>+ P44: uses
    P44-->>- P1: return
    P1->>+ P18: uses
    P18-->>- P1: return
    P1->>+ P19: uses
    P19-->>- P1: return
    P1->>+ P45: uses
    P45-->>- P1: return
    P1->>+ P46: calls
    P46-->>- P1: return
    P1->>+ P31: uses
    P31-->>- P1: return
    P1->>+ P32: uses
    P32-->>- P1: return
    P1->>+ P33: uses
    P33-->>- P1: return
    P1->>+ P34: uses
    P34-->>- P1: return
    P1->>+ P35: uses
    P35-->>- P1: return
    P1->>+ P47: uses
    P47-->>- P1: return
    P0->>+ P41: uses
    P41-->>- P0: return
    P0->>+ P48: uses
    P48-->>- P0: return
    P0->>+ P14: uses
    P14-->>- P0: return
    P0->>+ P15: uses
    P15-->>- P0: return
    P0->>+ P49: calls
    P49-->>- P0: return
    P0->>+ P18: uses
    P18-->>- P0: return
    P0->>+ P19: uses
    P19-->>- P0: return
    P0->>+ P22: uses
    P22-->>- P0: return
    P0->>+ P50: calls
    P50-->>- P0: return
    P0->>+ P51: calls
    P51-->>- P0: return
    P0->>+ P52: calls
    P52-->>- P0: return
    P0->>+ P53: calls
    P53-->>- P0: return
    P0->>+ P54: calls
    P54-->>- P0: return
    P0->>+ P55: uses
    P55-->>- P0: return
    P0->>+ P56: uses
    P56-->>- P0: return
    P0->>+ P57: uses
    P57-->>- P0: return
    P0->>+ P58: uses
    P58-->>- P0: return
    P0->>+ P59: uses
    P59-->>- P0: return
    P0->>+ P60: uses
    P60-->>- P0: return
```

## Connections by Relation

### calls
- [[load_simulation_table()]] `EXTRACTED`
- [[test_filter_simulation_table_keeps_calendar_matching_rows_from_every_table()]] `INFERRED`
- [[test_validate_simulation_tables_consistency_fails_when_there_are_missing_columns()]] `INFERRED`
- [[make_simulation_table()]] `INFERRED`
- [[test_concat_simulation_tables_combines_rows_from_every_table()]] `INFERRED`
- [[test_validate_simulation_tables_consistency_pass()]] `INFERRED`

### contains
- [[simulation_table.py]] `EXTRACTED`

### inherits
- [[PersistentSimulationTable]] `EXTRACTED`

### rationale_for
- [[Lazy representation of the SIMULATION_TABLE parquet file.]] `EXTRACTED`

### uses
- [[RawInputData]] `INFERRED`
- [[Calendar]] `INFERRED`
- [[MetricStructureTable]] `INFERRED`
- [[ViewBuildingInput]] `INFERRED`
- [[Constructor should not read yaml or parquet.     Multi-file inputs are resolved]] `INFERRED`
- [[Inputs of the view-building algorithm for one view config.]] `INFERRED`
- [[Build a real RawInputData, skipping only the disk-reading Loader.load() step:]] `INFERRED`
- [[Study inputs as loaded from disk, before view-building transformations.]] `INFERRED`
- [[When a non-parquet, non-csv file is provided, an error is raised.]] `INFERRED`
- [[Rows with a null component or output can never be needed by a metric.]] `INFERRED`
- [[Replace (component, output) by their pair_id, like the filtered table does.]] `INFERRED`
- [[Filtered result must satisfy: every row (absolute_time_index, block) in calendar]] `INFERRED`
- [[Rows whose block does not match the calendar's block for a given absolute_time_i]] `INFERRED`
- [[The filtered table is written to parquet with expected content.]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*