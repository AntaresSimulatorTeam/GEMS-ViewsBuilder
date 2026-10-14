#!/usr/bin/env bash
# Build the area and link views of this example into output/area and output/link.
set -euo pipefail
cd "$(dirname "$0")"

for view in area link; do
  mkdir -p "output/$view"
  gems-views-builder \
    --system system.yml \
    --libraries-dir libraries \
    --taxonomy antares_legacy_taxonomy_flattened.yml \
    --catalogs-dir catalogs \
    --calendar calendar.csv \
    --simulation-tables "simulation_tables/simulation-table-*-optim-nb-2.parquet" \
    --view-config "view_config_$view.yml" \
    --output "output/$view" \
    --output-format csv
done
