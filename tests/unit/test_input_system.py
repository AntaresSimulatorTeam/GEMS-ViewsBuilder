# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from gems_views_builder.input.library import load_yml_libs
from gems_views_builder.input.system import load_system

LIBRARY_YML = """
library:
  id: lib
  port-types:
    - id: flow
      fields:
        - id: flow
  models:
    - id: node
      taxonomy-category: balance
      parameters:
        - id: cost
          time-dependent: false
          scenario-dependent: false
      variables:
        - id: p
          lower-bound: "0"
          upper-bound: "1"
      ports:
        - id: balance_port
          type: flow
      port-field-definitions:
        - port: balance_port
          field: flow
          definition: p
    - id: peer
      taxonomy-category: balance
      ports:
        - id: balance_port
          type: flow
"""

SYSTEM_YML = """
system:
  id: tiny
  components:
    - id: node_a
      model: lib.node
      parameters:
        - id: cost
          time-dependent: false
          scenario-dependent: false
          value: 1
    - id: node_b
      model: lib.peer
  connections:
    - component1: node_a
      port1: balance_port
      component2: node_b
      port2: balance_port
"""


def test_load_system(tmp_path: Path) -> None:
    library_dir = tmp_path / "libraries"
    library_dir.mkdir()
    (library_dir / "library.yml").write_text(LIBRARY_YML)
    yml_libs = load_yml_libs(library_dir)

    system_path = tmp_path / "system.yml"
    system_path.write_text(SYSTEM_YML)
    system = load_system(system_path, yml_libs)

    assert {c.id for c in system.components} == {"node_a", "node_b"}
    assert len(system.connections) == 1
