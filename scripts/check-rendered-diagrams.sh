#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$repo_root/docs/diagrams/src"
rendered_dir="$repo_root/docs/diagrams/rendered"
committed_dir="$rendered_dir"

usage() {
  printf '%s\n' 'Usage: scripts/check-rendered-diagrams.sh [options]' >&2
  printf '%s\n' '  --source-dir DIRECTORY      Mermaid source directory' >&2
  printf '%s\n' '  --rendered-dir DIRECTORY    Current render output directory' >&2
  printf '%s\n' '  --committed-dir DIRECTORY   Committed SVG directory' >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --source-dir)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      source_dir=$2
      shift 2
      ;;
    --rendered-dir)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      rendered_dir=$2
      shift 2
      ;;
    --committed-dir)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      committed_dir=$2
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

config="$repo_root/tools/diagrams/mermaid-config.json"
puppeteer_config="$repo_root/tools/diagrams/puppeteer-config.json"
package_lock="$repo_root/tools/diagrams/package-lock.json"
failures=0
source_count=0

report_failure() {
  printf 'Rendered diagram check: %s\n' "$*" >&2
  failures=1
}

fingerprint_for() {
  node -e '
const crypto = require("node:crypto");
const fs = require("node:fs");
const inputs = [
  ["source", process.argv[1]],
  ["mermaid-config", process.argv[2]],
  ["puppeteer-config", process.argv[3]],
  ["package-lock", process.argv[4]],
];
const hash = crypto.createHash("sha256");
hash.update("secure-self-service-cloud-platform-diagram-fingerprint-v1\0");
for (const [label, file] of inputs) {
  hash.update(label + "\0");
  hash.update(fs.readFileSync(file));
  hash.update("\0");
}
process.stdout.write(hash.digest("hex"));
' "$1" "$config" "$puppeteer_config" "$package_lock"
}

check_directory() {
  label=$1
  directory=$2

  if [ ! -d "$directory" ]; then
    report_failure "$label output directory is missing: $directory"
    return
  fi

  for output in "$directory"/*.svg; do
    [ -f "$output" ] || continue
    basename=$(basename "$output" .svg)
    if [ ! -f "$source_dir/$basename.mmd" ]; then
      report_failure "$label orphan SVG has no matching source: $output"
    fi
  done
}

if [ ! -d "$source_dir" ]; then
  report_failure "source directory is missing: $source_dir"
else
  for source in "$source_dir"/*.mmd; do
    [ -f "$source" ] || continue
    source_count=$((source_count + 1))
    basename=$(basename "$source" .mmd)
    expected=$(fingerprint_for "$source")
    marker="<!-- diagram-fingerprint: sha256:$expected -->"

    for output_spec in \
      "temporary:$rendered_dir/$basename.svg" \
      "committed:$committed_dir/$basename.svg"; do
      label=${output_spec%%:*}
      output=${output_spec#*:}
      if [ ! -f "$output" ]; then
        report_failure "$label SVG is missing for source $source: $output"
      elif ! grep -F "$marker" "$output" >/dev/null 2>&1; then
        report_failure "$label SVG has stale or missing fingerprint: $output (expected $expected)"
      fi
    done
  done
fi

if [ "$source_count" -eq 0 ]; then
  report_failure "no Mermaid .mmd sources found in: $source_dir"
fi

check_directory 'temporary' "$rendered_dir"
if [ "$committed_dir" != "$rendered_dir" ]; then
  check_directory 'committed' "$committed_dir"
fi

if [ "$failures" -ne 0 ]; then
  printf '%s\n' 'Rendered diagram freshness failed.' >&2
  exit 1
fi

printf 'Rendered diagram freshness passed for %s source(s).\n' "$source_count"
