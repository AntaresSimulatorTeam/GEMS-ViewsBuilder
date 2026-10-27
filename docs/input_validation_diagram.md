# Input Validation Diagram

Nodes are input files loaded by the pipeline. Edges are the cross-file
checks performed between them, labeled with the checks themselves.

```mermaid
graph LR
    catalog_1(("catalog_1.yml"))
    catalog_dots["⋮"]
    catalog_n(("catalog_N.yml"))
    catalog_join((" "))
    taxonomy(("taxonomy.yml"))
    view_config(("view_config.yml"))
    library_1(("library_1.yml"))
    library_dots["⋮"]
    library_n(("library_N.yml"))
    library_join((" "))
    system(("system.yml"))
    simulation_table_1(("simulation_table_1.parquet/csv"))
    simulation_table_dots["⋮"]
    simulation_table_n(("simulation_table_N.parquet/csv"))
    simulation_table_join((" "))
    calendar(("calendar.csv"))

    catalog_1 -.- catalog_join
    catalog_dots -.- catalog_join
    catalog_n -.- catalog_join
    catalog_join -- "• taxonomy id matches<br/>• taxonomy category exists<br/>• output id declared<br/>• location ports declared" --- taxonomy
    view_config -- "• taxonomy id matches<br/>• location taxonomy category exists" --- taxonomy
    view_config -- "• taxonomy id matches<br/>• location taxonomy category matches" --- catalog_join
    view_config -- "• selected metrics exist in catalogs<br/>(resolved while loading)" --- catalog_join

    library_1 -.- library_join
    library_dots -.- library_join
    library_n -.- library_join
    library_join -. "checked by gemspy" .- system

    simulation_table_1 -.- simulation_table_join
    simulation_table_dots -.- simulation_table_join
    simulation_table_n -.- simulation_table_join
    view_config -.- calendar

    classDef unvalidated stroke-dasharray: 4 4;
    classDef plain stroke: none, fill: none;
    class library_1,library_n,simulation_table_1,simulation_table_n,system,calendar unvalidated;
    class library_dots,library_join,catalog_dots,catalog_join,simulation_table_dots,simulation_table_join plain;
```

Solid edges = content is cross-validated. Dashed edges = files are read
together / referenced by the study layout, but have no dedicated
cross-file validator yet (see [`StudyLayoutValidator`](../gems_views_builder/validation/study_layout_validator.py),
which only checks that these files are *present*, not their contents).

## Edge details

### `catalog.yml` → `taxonomy.yml`
[`CatalogsTaxonomyValidator`](../gems_views_builder/validation/catalogs_taxonomy_validator.py)

| Check | Rule |
|---|---|
| Taxonomy id match | `catalog.taxonomy == taxonomy.id` |
| Taxonomy category exists | every term's `taxonomy-category` is a category defined in `taxonomy.yml` |
| Output id declared | every term's `output-id` is declared as a `variable` or `extra-output` on that category |
| Location port declared | every term's `location-port` is declared as a `port` on that category |

### `view_config.yml` → `taxonomy.yml`
[`ViewConfigTaxonomyValidator`](../gems_views_builder/validation/view_config_taxonomy.py)

| Check | Rule |
|---|---|
| Taxonomy id match | `view_config.taxonomy_id == taxonomy.id` |
| Location taxonomy category exists | `view_config.location_taxonomy_category` is a category defined in `taxonomy.yml` |

### `catalog.yml` ↔ `view_config.yml`
[`ViewConfigCatalogsValidator`](../gems_views_builder/validation/catalogs_view_config_validator.py)

| Check | Rule |
|---|---|
| Taxonomy id match | `catalog.taxonomy == view_config.taxonomy_id` |
| Location taxonomy category match | `catalog.location_taxonomy_category == view_config.location_taxonomy_category` |

Selected metrics are resolved while loading, in [`ViewConfig.populate_with_metrics`](../gems_views_builder/input/view_config.py). Every `<catalog_id>.<metric_id>` must name a loaded catalog and a metric in that catalog.

## Orchestration

[`InputConsistencyValidator`](../gems_views_builder/validation/input_consistency_validator.py)
runs the validators above, in this order:

1. `CatalogsTaxonomyValidator` (catalog ↔ taxonomy)
2. `ViewConfigTaxonomyValidator` (view_config ↔ taxonomy)
3. `ViewConfigCatalogsValidator` (catalog ↔ view_config)