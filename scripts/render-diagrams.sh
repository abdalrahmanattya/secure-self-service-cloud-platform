#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
renderer="$repo_root/tools/diagrams/node_modules/.bin/mmdc"
config="$repo_root/tools/diagrams/mermaid-config.json"
source_dir="$repo_root/docs/diagrams/src"
output_dir="$repo_root/docs/diagrams/rendered"

if [ ! -x "$renderer" ]; then
  printf '%s\n' "Mermaid CLI is not installed. Run: npm ci --prefix tools/diagrams" >&2
  exit 1
fi

mkdir -p "$output_dir"

for rendered in "$output_dir"/*.svg; do
  [ -f "$rendered" ] || continue
  rm -f "$rendered"
done

for source in "$source_dir"/*.mmd; do
  name=$(basename "$source" .mmd)
  "$renderer" \
    --input "$source" \
    --output "$output_dir/$name.svg" \
    --configFile "$config" \
    --outputFormat svg \
    --quiet
done

printf '%s\n' "Rendered Mermaid diagrams into docs/diagrams/rendered/."
