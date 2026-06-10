# Concepts Glossary

All domain terms used across the documentation, in dependency order (foundations first).

---

## Taxonomy

A shared vocabulary file (`taxonomy.yml`) that defines the **categories** of model types,
their ports, variables, and output types. All other config files reference it.

### Taxonomy category

A named class of model (`id`), optionally with a `parent-category` that places it in a
hierarchy. Example: `production`, `consumption`, `balance`, `link`.


---

## Model library

A `library.yml` file defining **model schemas**: what variables, parameters, ports,
port-field-definitions, and extra-outputs a component type has.

### Model

A component type definition (e.g. `generator`, `load`, `bus`). Each model belongs to
exactly one taxonomy category.

### Variable

An optimization decision variable defined on a model (e.g. `p`, `p_nom`). Valid source
for `output-id` in a catalog term.

### Port

A typed connection endpoint declared on a taxonomy category. Generators have a
`p_balance_port`; links have `p0_port` and `p1_port`. Used in `system.yml` connections.

### Port-field-definition

An output derived from a port field (e.g. `p_balance_port.flow`). Identified by
`<port>.<field>` in the simulation table. Valid source for `output-id`.

### Extra-output

A named expression output defined on a model (e.g. `active_load`, `effective_load`).
Valid source for `output-id`.

### output-id

The identifier used in a catalog term to select which simulation row to read.
Must be the `id` of a **variable**, a **port-field-definition id**, or an **extra-output id**
from models in the referenced taxonomy category.

---

## System

A `system.yml` file defining the **component instances** of a study and their port
connections.

### Component

An instance of one model (e.g. `generator_A1` is an instance of `pypsa_models.generator`).
Has `parameters` (numeric values) and `properties` (string key-value pairs used for
filtering and breakdown).

### Connection

A port-level link between two components. Example: `busA.p_balance_port ↔ generator_A1.p_balance_port`.

### Property

A string `(key, value)` pair on a component (e.g. `technology=nuclear`). Source for
`filter` and `breakdown` in metric definitions.

---

## Metric building

### Location component

The spatial unit for a metric result. Defined by the taxonomy category specified in
`catalog.location.taxonomy-category` (typically `balance` — a bus or area component).

### Location port (`location-ports`)

The port on a contributing component through which its location is resolved.
- `null` → the component itself is the location (self-location)
- `"port_name"` → the peer component connected through that port is the location
- `["p0_port", "p1_port"]` → one location per port (multi-port, produces multiple rows)

### LOCATING_FUNCTION

The function that resolves a `(component, location_port)` pair to a location component id.
If no connection exists for the named port, a `ValueError` is raised. If multiple peers
exist, they are all included in the `metric_location` (no uniqueness constraint today, but intended 
changes on the topic to enforce uniqueness, see [ADR-003](../adr/003-get-location-ownership.md)).

### Filter

A single `(key, value)` property constraint that restricts which components contribute
to a metric. A component contributes only if `properties[key] == value`.
Cardinality: 0 or 1 per metric (see [ADR-002](../adr/002-filter-cardinality.md)).

### Breakdown

A list of property keys that split metric output into sub-groups. All distinct values
found on contributing components are emitted. Components missing a key emit `None` for
that key.

### Metric

A business indicator combining one or more **terms** into a single aggregated value per
`(location, breakdown, date, scenario)`.

### Term

One contribution to a metric: specifies which component outputs to read (`taxonomy-category`
+ `output-id`) and how to locate them (`location-ports`).

---

## Time and scenarios

### Simulation block

A time window in a simulation run. Rolling-horizon simulations produce multiple
overlapping blocks for the same absolute timestep; the calendar identifies the reference
block.

### absolute_time_index

Integer index of a global simulation timestep, starting at 0, contiguous.

### Calendar

A CSV file mapping each `absolute_time_index` to a `(block, granular_date)` pair.
Two roles: (1) selects the reference block per timestep; (2) provides the date for
temporal aggregation.

### Scenario

A Monte-Carlo scenario index (`scenario_index` in the simulation table).

---

## Output

### View

The output parquet file. One row per unique `(metric_id, metric_location,
breakdown_properties, view_date, scenario)`. Schema: [`pipeline/03-output-schema.md`](../pipeline/03-output-schema.md).

### view_date

The date assigned to each output row, derived from `granular_date` in the calendar.
The `view_config.yml` `time` aggregation field specifies the intended truncation
granularity (`hour|day|week|month|year`), though date truncation is not yet applied in
the current implementation (see [ADR-007](../adr/007-consistency-check-strategy.md)).
