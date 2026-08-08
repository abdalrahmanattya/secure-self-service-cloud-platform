#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
renderer="$repo_root/tools/diagrams/node_modules/.bin/mmdc"
config="$repo_root/tools/diagrams/mermaid-config.json"
puppeteer_config="$repo_root/tools/diagrams/puppeteer-config.json"
package_lock="$repo_root/tools/diagrams/package-lock.json"
source_dir="$repo_root/docs/diagrams/src"
output_dir="$repo_root/docs/diagrams/rendered"

if [ "$#" -eq 2 ] && [ "$1" = '--output-dir' ]; then
  output_dir=$2
elif [ "$#" -ne 0 ]; then
  printf '%s\n' 'Usage: scripts/render-diagrams.sh [--output-dir DIRECTORY]' >&2
  exit 2
fi

if [ ! -x "$renderer" ]; then
  printf '%s\n' "Mermaid CLI is not installed. Run: npm ci --prefix tools/diagrams" >&2
  exit 1
fi

for input in "$config" "$puppeteer_config" "$package_lock"; do
  if [ ! -f "$input" ]; then
    printf 'Required renderer input is missing: %s\n' "$input" >&2
    exit 1
  fi
done

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

write_fingerprint() {
  node -e '
const fs = require("node:fs");
const file = process.argv[1];
const fingerprint = process.argv[2];
const marker = `<!-- diagram-fingerprint: sha256:${fingerprint} -->`;
const svg = fs.readFileSync(file, "utf8");
if (!svg.startsWith("<svg")) {
  throw new Error(`Unexpected Mermaid output in ${file}`);
}
const cleanSvg = svg.replace(/\n?<!-- diagram-fingerprint: sha256:[0-9a-f]{64} -->/g, "");
const openingEnd = cleanSvg.indexOf(">");
fs.writeFileSync(file, `${cleanSvg.slice(0, openingEnd + 1)}\n${marker}${cleanSvg.slice(openingEnd + 1)}`);
' "$1" "$2"
}

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
    --puppeteerConfigFile "$puppeteer_config" \
    --outputFormat svg \
    --quiet
  write_fingerprint "$output_dir/$name.svg" "$(fingerprint_for "$source")"
done

printf 'Rendered Mermaid diagrams into %s.\n' "$output_dir"
