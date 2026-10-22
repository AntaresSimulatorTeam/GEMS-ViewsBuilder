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
    view_config_1(("view_config_1.yml"))
    view_config_dots["⋮"]
    view_config_n(("view_config_N.yml"))
    view_config_join((" "))
    library_1(("library_1.yml"))
    library_dots["⋮"]
    library_n(("library_N.yml"))
    library_join((" "))
    system(("system.yml"))
    simulation_table(("simulation_table.parquet/csv"))
    calendar(("calendar.csv"))

    catalog -- "• taxonomy id matches<br/>• taxonomy category exists<br/>• output id is a variable or extra-output<br/>• location ports declared" --- taxonomy
    view_config_1 -.- view_config_join
    view_config_dots -.- view_config_join
    view_config_n -.- view_config_join
    view_config_join -- "• taxonomy id matches<br/>• location taxonomy category exists" --- taxonomy
    view_config_join -- "• taxonomy id matches<br/>• location taxonomy category matches" --- catalog
    view_config_join -- "• selected metrics exist in catalogs" --- catalog

    library_1 -.- library_join
    library_dots -.- library_join
    library_n -.- library_join
    library_join -- "• each model matches its taxonomy category" --- taxonomy
    library_join -. "checked by gemspy" .- system
    view_config_join -.- calendar

    classDef unvalidated stroke-dasharray: 4 4;
    classDef plain stroke: none, fill: none;
    class system,simulation_table,calendar unvalidated;
    class library_dots,library_join,view_config_dots,view_config_join plain;
```
[Input validation](docs/input_validation_diagram.md) for the detailed rules behind each check.

