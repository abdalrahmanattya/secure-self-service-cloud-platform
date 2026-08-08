# Architecture diagrams

Architecture diagrams are maintained as text source so changes remain
reviewable. Mermaid source and rendered accessible SVG output will be added
with the component each diagram explains.

Every diagram must include surrounding prose that states:

- its purpose;
- actors and responsibilities;
- trust boundaries and data flow;
- relevant security assumptions; and
- provider-specific differences.

The planned catalogue includes product context, C4 views, request and
deployment sequences, provider-selection state, AWS and Azure topologies,
identity, Terraform state, policy, logging, threat paths, and incident
timelines.

## Available rendered diagrams

| View | Purpose and accessible alternative text | Source | Rendered output |
| --- | --- | --- | --- |
| System context | People submit requests or configure the platform; GitHub reviews the deterministic proposal; exactly one optional cloud destination receives an approved deployment. | [`system-context.mmd`](src/system-context.mmd) | [`system-context.svg`](rendered/system-context.svg) |
| Provider selection | An installation moves from unconfigured to a selected provider and mode, then locks the provider after activation; mismatched requests are rejected. | [`provider-selection.mmd`](src/provider-selection.mmd) | [`provider-selection.svg`](rendered/provider-selection.svg) |

The SVG links above are the accessible, committed renderings for readers who
do not have Mermaid installed. The source comments and surrounding prose state
the same relationships in text for readers using a screen reader or a
text-only environment.

## Local rendering

From the repository root, install the pinned renderer and render every source:

```sh
npm ci --prefix tools/diagrams
scripts/render-diagrams.sh
scripts/check-rendered-diagrams.sh
```

With no argument, the renderer refreshes the committed output directory. To
render into another directory, use the explicit output option:

```sh
temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT
scripts/render-diagrams.sh --output-dir "$temporary_dir"
scripts/check-rendered-diagrams.sh --rendered-dir "$temporary_dir"
```

To verify deterministic output, render twice and compare checksums:

```sh
scripts/render-diagrams.sh
first=$(shasum docs/diagrams/rendered/*.svg)
scripts/render-diagrams.sh
test "$first" = "$(shasum docs/diagrams/rendered/*.svg)"
```

Every SVG receives a deterministic content-only SHA-256 fingerprint tied to
its `.mmd` source, Mermaid configuration, Puppeteer configuration, and package
lock. The checker verifies matching source/output basenames, missing and orphan
files, and the expected fingerprint in both the temporary and committed
outputs.

CI runs Mermaid on `ubuntu-24.04` into a clean temporary directory, proving
that every current source renders without overwriting committed SVGs. It then
runs the freshness checker. The workflow intentionally does not compare SVG
bytes across operating systems; browser and layout bytes can vary by platform.
