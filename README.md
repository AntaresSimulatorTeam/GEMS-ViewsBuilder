# GEMS-ViewsBuilder

This repository is a prototype for the GEMS BusinessViews builder. According to the GEMS logic, a View is an aggregated perspective on a SimulationTable.

## Inputs

The main inputs are
- A GEMS System
- A GEMS Library 
- A GEMS Taxonomy 
- A SimulationTable consistent with the GEMS System
- One or several Catalog(s) defining Metrics
- Configurations of Views

## Outputs

The main outputs are Views.

## Input validation diagram
```mermaid
graph LR
    catalog(("catalog.yml<br/>(one or more)"))
    taxonomy(("taxonomy.yml"))
    view_config(("view_config.yml"))
    library_1(("library_1.yml"))
    library_dots["⋮"]
    library_n(("library_N.yml"))
    library_join((" "))
    system(("system.yml"))
    simulation_table(("simulation_table.parquet/csv"))
    calendar(("calendar.csv"))

    catalog -- "• taxonomy id matches<br/>• taxonomy category exists<br/>• output id declared<br/>• location ports declared" --- taxonomy
    view_config -- "• taxonomy id matches<br/>• location taxonomy category exists" --- taxonomy
    view_config -- "• taxonomy id matches<br/>• location taxonomy category matches" --- catalog
    view_config -- "• selected metrics exist in catalogs" --- catalog

    library_1 -.- library_join
    library_dots -.- library_join
    library_n -.- library_join
    library_join -. "checked by gemspy" .- system
    view_config -.- calendar

    classDef unvalidated stroke-dasharray: 4 4;
    classDef plain stroke: none, fill: none;
    class library_1,library_n,system,simulation_table,calendar unvalidated;
    class library_dots,library_join plain;
```
[Input validation](docs/input_validation_diagram.md) for the detailed rules behind each check.

