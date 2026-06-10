# Input Files Reference

## File citation graph

Which files reference which other files:

```
view_config.yml ──[catalog ids → filename]──────► catalogs/<id>.yml  (×N)
view_config.yml ──[calendar id → filename]───────► calendar*.csv
view_config.yml ──[taxonomy-category]────────────► taxonomy.yml  (scope check, not yet validated)
# TODO(#57): view_config.yml ──[taxonomy field, planned]──► taxonomy.yml  (id must match, not yet implemented)

catalog.yml     ──[taxonomy field]───────────────► taxonomy.yml  (id must match)
catalog.yml     ──[term.taxonomy-category]────────► taxonomy.yml  (category must exist)
catalog.yml     ──[term.location-ports]──────────► taxonomy.yml  (port must exist on category)
catalog.yml     ──[term.output-id]───────────────► taxonomy.yml   (output must exist on category, as variable, port-field or extra-output)

library.yml     ──[model.taxonomy-category]──────► taxonomy.yml  (not validated by ViewsBuilder)
system.yml      ──[component.model]──────────────► library.yml   (resolved at load time)
simulation_table.parquet ──[component col]───────► system.yml    (component ids)
simulation_table.parquet ──[output col]──────────► library.yml   (output-ids)
```

`taxonomy.yml` has no outbound references — it is the root vocabulary.

---

## Data entity diagram

```
Taxonomy        ||--o{ TaxonomyCategory    : "categories"
TaxonomyCategory}o--o| TaxonomyCategory   : "parent-category (hierarchy)"
TaxonomyCategory||--o{ TaxonomyItem       : "ports / variables / extra-outputs / properties"

ModelLibrary    ||--o{ ModelSchema        : "models"
ModelSchema     }|--|| TaxonomyCategory  : "taxonomy-category (1:1)"
ModelSchema     ||--o{ PortSchema        : "ports"
ModelSchema     ||--o{ ExtraOutputSchema : "extra-outputs"
ModelSchema     ||--o{ VariableSchema    : "variables"

InputSystem     ||--o{ Component         : "components"
Component       }|--|| ModelSchema       : "model (1:1, qualified ref)"
Component       ||--o{ Property         : "properties (0..N)"
InputSystem     ||--o{ PortsConnection  : "connections"

Catalog         ||--o{ Metric           : "metrics-definition"
Catalog         }|--|| TaxonomyCategory : "location.taxonomy-category"
Metric          ||--|{ Term             : "terms (1..N)"
Term            }|--|| TaxonomyCategory : "taxonomy-category"
Term            }|--|| PortSchema       : "location-ports (0..N)"
Term            }|--|| VariableSchema|ExtraOutputSchema|PortFieldSchema : "output-id"
Term            }|--|| VariableSchema|ExtraOutputSchema|PortFieldSchema : "weight-output-id"
Metric          |o--o| PropertySchema  : "filter"
Metric          ||--o{ PropertyKeySchema  : "breakdown (0..N, key only)"

ViewConfig      }|--|| TaxonomyCategory : "scope.taxonomy-category"
ViewConfig      ||--|{ Catalog          : "catalog refs (1..N)"
%% TODO(#57): ViewConfig should carry a `taxonomy` field pointing to Taxonomy.id,
%%             and cross-checks view_config.taxonomy==catalog.taxonomy and
%%             view_config.scope.taxonomy-category==catalog.location.taxonomy-category.
%%             See ADR-008.
ViewConfig      ||--|{ Metric           : "metric refs (1..N)"
ViewConfig      }|--|| Calendar         : "calendar ref (1:1)"

SimulationTable }|--o{ Component                                            : "component column"
SimulationTable }|--o{ VariableSchema|ExtraOutputSchema|PortFieldSchema     : "output column (output-id)"
```

---

## `taxonomy.yml`

```yaml
taxonomy:
  id: <str>
  description: <str>          # optional
  categories:
    - id: <str>
      parent-category: <str>  # optional; enables subcategory walk (ADR-006)
      ports:         [{ id: <str> }, ...]
      variables:     [{ id: <str> }, ...]
      parameters:    [{ id: <str> }, ...]
      extra-outputs: [{ id: <str> }, ...]
      properties:    [{ id: <str> }, ...]
      constraints:   [{ id: <str> }, ...]
      binding-constraints:   [{ id: <str> }, ...]
```

**Example** (from `resources/tests/test_inputs/test_3/taxonomy.yml`):

```yaml
taxonomy:
  id: my_taxonomy
  categories:
    - id: balance
      ports:
        - id: p_balance_port
        - id: q_balance_port
    - id: production
      ports:
        - id: p_balance_port
    - id: link
      ports:
        - id: p0_port
        - id: p1_port
```

Python type: `Taxonomy` (`taxonomy.py`).

---

## `library.yml`

Fields read by ViewsBuilder (GemsPy parses the full schema):

```yaml
library:
  id: <str>
  port-types:
    - id: <str>
      fields: [{ id: <str> }, ...]
  models:
    - id: <str>
      taxonomy-category: <str>       # must match a taxonomy category id
      variables:            [{ id: <str> }, ...]
      parameters:           [{ id: <str> }, ...]
      ports:                [{ id: <str>, type: <str> }, ...]
      port-field-definitions:
        - port: <str>
          field: <str>               # output-id = "<port>.<field>"
          definition: <expression>
      extra-outputs:
        - id: <str>                  # valid output-id
          expression: <expression>
```

**Valid `output-id` sources** for a given `taxonomy-category`:
- `variable.id` (e.g. `p`, `p_nom`)
- `"<port>.<field>"` from port-field-definitions (e.g. `p_balance_port.flow`)
- `extra-output.id` (e.g. `active_load`, `effective_load`)

Python type: `ModelLibrary` (`library.py`) — wraps GemsPy `LibrarySchema`.

---

## `system.yml`

```yaml
system:
  id: <str>
  components:
    - id: <str>
      model: <library_id>.<model_id>    # qualified reference
      parameters: [{ id: <str>, value: <str>, ... }, ...]
      properties:  [{ id: <str>, value: <str> }, ...]   # used by filter/breakdown
  connections:
    - component1: <str>
      port1: <str>
      component2: <str>
      port2: <str>
```

**Key points:**
- `model` uses qualified form `<library_id>.<model_id>` (e.g. `pypsa_models.generator`).
- `properties` are string `(id, value)` pairs — the source for `filter` and `breakdown` in metrics.
- A component without a `properties` entry contributes with `(key, None)` for any breakdown key.

**Example** (two-bus system):

```yaml
system:
  id: two_bus_example
  components:
    - id: generator_A1
      model: pypsa_models.generator
      parameters: [...]
    - id: busA
      model: pypsa_models.bus
      parameters: [...]
  connections:
    - component1: busA
      port1: p_balance_port
      component2: generator_A1
      port2: p_balance_port
```

Python type: `InputSystem` (`system.py`) — wraps GemsPy resolved `System`.

---

## `calendar*.csv`

Exactly one file matching `calendar*.csv` in the study directory.

**Required columns (in this exact order):**

| Column | Type | Description |
|---|---|---|
| `absolute_time_index` | int | Global timestep index, contiguous from 0 |
| `block` | int / str | Simulation block identifier |
| `granular_date` | datetime | ISO format, equally spaced |

**Validation rules** (enforced in `calendar.py:_check_calendar_columns`):
- Column names and order must match exactly.
- `absolute_time_index` must be contiguous integers `0, 1, 2, …, N-1`.
- Spacing between consecutive `granular_date` values must be constant.

**Dual role:**
1. **Block selector**: in Step 1, only rows where `block == calendar[absolute_time_index].block` are kept, discarding overlapping blocks from rolling-horizon simulations.
2. **Timestamper**: provides `granular_date` for each retained row, used as `view_date` in output.

**Example:**

| absolute_time_index | block | granular_date |
|---|---|---|
| 0 | 0 | 2025-01-01T00:00:00 |
| 1 | 0 | 2025-01-01T01:00:00 |
| 2 | 1 | 2025-01-01T02:00:00 |
| 8759 | 167 | 2025-12-31T23:00:00 |

Python type: `Calendar` (`calendar.py`).

---

## `simulation_table*.parquet`

Exactly one file matching `simulation_table*.parquet` in the study directory.

**Required columns** (exact set; order not required):

| Column | Type | Nullable | Description |
|---|---|---|---|
| `block` | string | no | Time block identifier |
| `component` | string | no | Component instance id |
| `output` | string | no | output-id (variable, port-field-def, or extra-output) |
| `absolute_time_index` | int64 | **yes** | null for non-time-dependent outputs |
| `block_time_index` | int64 | yes | Timestep within the block |
| `scenario_index` | int64 | yes | Scenario index; null if scenario-independent |
| `value` | float64 | no | Numeric value |
| `basis_status` | string | no | Optimization basis status |

Rows where `absolute_time_index IS NULL` are **non-time-dependent** outputs. These rows are
preserved through the pipeline with `granular_date = null` (see `simulation_table.py:filter_simulation_table`).

Python type: `SimulationTable` (`simulation_table.py`).
