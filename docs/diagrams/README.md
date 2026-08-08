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
```

To verify deterministic output, render twice and compare checksums:

```sh
scripts/render-diagrams.sh
first=$(shasum docs/diagrams/rendered/*.svg)
scripts/render-diagrams.sh
test "$first" = "$(shasum docs/diagrams/rendered/*.svg)"
```

CI runs the same render command and fails when the generated SVG differs from
the committed output. The Mermaid configuration fixes IDs, typography, theme,
and layout settings so the result is reviewable and reproducible.
