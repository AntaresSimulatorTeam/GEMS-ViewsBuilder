# GEMS-ViewsBuilder

This repository is a prototype for the GEMS BusinessViews builder. According to the GEMS logic, a View is an aggregated perspective on a SimulationTable.

## Inputs

The *main inputs* are
- *GEMS System*
- *GEMS Library* 
- *GEMS Taxonomy* 
- One or several *Simulation Tables* *consistent* with the *GEMS System*
- One or several *Catalogs* defining *Metrics*
- One or several *View Configurations*
- *Calendar*

## Outputs

The main outputs are Views.

## Example

[examples/antares_legacy](examples/antares_legacy) holds a complete set of inputs, built from a small Antares legacy study, and the CLI call that builds its views.
