# Graph Report - /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder  (2026-11-15)

## Corpus Check
- 85 files · ~28,338 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 621 nodes · 1547 edges · 22 communities detected
- Extraction: 53% EXTRACTED · 47% INFERRED · 0% AMBIGUOUS · INFERRED: 734 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `ViewConfig` - 42 edges
2. `Component` - 39 edges
3. `Metric` - 36 edges
4. `InputPathsValidator` - 28 edges
5. `AggregationPattern` - 27 edges
6. `MetricStructureTableBuilder` - 26 edges
7. `Catalog` - 24 edges
8. `SimulationTable` - 23 edges
9. `TemporalMetricView` - 22 edges
10. `RawInputData` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_view_config_parses_extra_locations()` --calls--> `load_view_config()`  [INFERRED]
  /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_extra_locations.py → /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py
- `test_view_config_extra_locations_defaults_to_empty_list()` --calls--> `load_view_config()`  [INFERRED]
  /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/unit/test_extra_locations.py → /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py
- `test_yaml_time_aggregation_drives_full_pipeline()` --calls--> `fetch_view()`  [INFERRED]
  /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/e2e/test_time_aggregation_e2e.py → /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/e2e/utils.py
- `test_yaml_missing_aggregation_key_fails_to_parse()` --calls--> `load_view_config()`  [INFERRED]
  /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/e2e/test_time_aggregation_e2e.py → /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py
- `test_yaml_missing_scenario_aggregation_completely_fails_to_parse()` --calls--> `load_view_config()`  [INFERRED]
  /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/tests/e2e/test_time_aggregation_e2e.py → /home/rtei-beg-see-dp/GEMS-DEVELOPMENT/GEMS-ViewsBuilder/gems_views_builder/input/view_config.py

## Communities

### Community 0 - "Community 0"
_It computes aggregated metrics, applies location filters, manages execution concurrency, and stores results as Parquet files._
Cohesion: 0.05
Nodes (67): AggregOperatorType, sink_to_parquet(), Enum, Executor, apply_location_filter(), LocationFilter, MetricView, View for a single computed metric, stored as a parquet file. (+59 more)

### Community 1 - "Community 1"

Cohesion: 0.05
Nodes (71): AggregationProcessor, Calendar, _check_calendar_columns(), _check_dates_conformity(), _check_for_missing_columns(), _check_for_unexpected_columns(), _check_time_indices_conformity(), load_calendar() (+63 more)

### Community 2 - "Community 2"

Cohesion: 0.05
Nodes (47): ABC, accumulate_on_disk(), accumulate_views(), group_views(), Group metric views by view config and aggregation pattern., configure_logging(), make_log_file(), peak_rss_gib() (+39 more)

### Community 3 - "Community 3"

Cohesion: 0.06
Nodes (38): validate_catalog_metrics_are_unique(), validate_catalogs(), validate_catalogs_are_unique(), associated_catalogs(), InputConsistencyValidator, input_data_direct_validation(), validate_input_data(), make_catalog() (+30 more)

### Community 4 - "Community 4"

Cohesion: 0.08
Nodes (38): PropertySchema, Reference to a system/taxonomy property by key; value is required only for metri, Component, build_component_port_connections(), create_components(), endpoint(), enrich_components(), group_components_by_taxon() (+30 more)

### Community 5 - "Community 5"

Cohesion: 0.09
Nodes (36): Term, MetricStructureTable, On-disk metric structure table, ready for lazy scanning., with_pair_id(), collect_needed_pairs(), log_term_processing(), make_row(), MetricStructureTableBuilder (+28 more)

### Community 6 - "Community 6"

Cohesion: 0.1
Nodes (33): build_input(), fetch_result_files(), make_catalogs(), make_metrics(), make_system(), make_view_config(), result_name(), test_run_view_building_leads_to_generate_one_view_per_aggregation_pattern() (+25 more)

### Community 7 - "Community 7"

Cohesion: 0.13
Nodes (26): load_catalogs(), ViewConfigCatalogsValidator, InputPathsValidator, Validates InputPaths shapes (extensions / expected contents).      Existence of, require_suffix(), test_passes_for_loaded_catalogs(), test_rejects_invalid_references(), test_passes_for_loaded_catalogs() (+18 more)

### Community 8 - "Community 8"

Cohesion: 0.1
Nodes (23): create_lib_from_yml(), load_lib_file(), load_yml_libs(), collect_files(), collect_yml_from_dir(), Recommended pattern simulation tables: fake_path/output-xxx/st-x-mc-*.parquet, load_system(), Resolve a system like GemsPy's resolve_system, minus the parameter completeness (+15 more)

### Community 9 - "Community 9"

Cohesion: 0.14
Nodes (28): ViewBuilderBasedModel, BaseModel, Catalog, CatalogData, CatalogLocationData, load_catalog(), load_catalog_file(), Metric (+20 more)

### Community 10 - "Community 10"

Cohesion: 0.17
Nodes (19): _assert_totals_close(), _at(), _expected_generation_total_by_scenario(), NUCLEAR_PRODUCTION is filtered (technology=nuclear), so it must equal the     PR, For each (location, date, scenario), PRODUCTION must equal the sum across the, Per scenario, PRODUCTION_BY_TECH nuclear / gas totals match raw ``generation`` s, Per scenario, company breakdown totals match simulation sums for that company., Each (technology, company) bucket is a single generator in this dataset;     per (+11 more)

### Community 11 - "Community 11"

Cohesion: 0.24
Nodes (9): add_multiple_file_path_options(), add_path_options(), build_parser(), check_multiple_file_path_options(), check_options(), check_paths_options(), Option, PathOption (+1 more)

### Community 12 - "Community 12"

Cohesion: 0.3
Nodes (11): copy_study_in_tmp(), metric_at(), test_3_study(), test_build_view__balance_at_bus_a__matches_link_outflow(), test_build_view__balance_at_bus_b__matches_link_inflow(), test_build_view__load_at_bus_a__returns_constant_100(), test_build_view__load_at_bus_b__has_no_rows(), test_build_view__prod_at_bus_a__returns_24_hourly_rows() (+3 more)

### Community 13 - "Community 13"

Cohesion: 0.31
Nodes (2): allowed_output(), CatalogsTaxonomyValidator

### Community 14 - "Community 14"
_Unable to determine domain due to missing code entities._
Cohesion: 0.4
Nodes (0): 

### Community 15 - "Community 15"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
_Unable to determine domain due to missing code entities._
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **22 isolated node(s):** `Copy ``filtering_and_breakdown``, run ``ViewBuilder``, return ``(dataset_dir, vi`, `PRODUCTION_BY_TECH should include two breakdown buckets: nuclear and gas.`, `NUCLEAR_PRODUCTION is filtered (technology=nuclear), so it must equal the     PR`, `For each (location, date, scenario), PRODUCTION must equal the sum across the`, `Per scenario, PRODUCTION_BY_TECH nuclear / gas totals match raw ``generation`` s` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 15`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.