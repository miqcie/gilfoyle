# Review workbench spike

A standalone Vite/React spike for displaying a review result compatible with
[`../evals/contracts/review-output.schema.json`](../evals/contracts/review-output.schema.json).
It deliberately has its own `package.json`; the Python reviewer and evaluation
runtime do not install or import its browser dependencies.

## Run

```bash
cd workbench
npm install
npm run dev
```

Open the URL Vite prints. `src/fixture.ts` supplies a two-file patch and a
schema-compatible review result. `src/App.tsx` maps each finding's
`evidence.path` and `start_line` to a Diffs additions-side line annotation.
The rendered annotation contains the finding ID, severity, and evidence quote.

The path-first navigation is a `@pierre/trees` `FileTree`: changed paths are
its canonical IDs, `gitStatus` marks each as modified, and
`renderRowDecoration` supplies a per-path finding-count badge. Selecting a path
shows its annotated diff. Both packages are used through their React entry
points, and a DOM interaction test verifies the selection-to-diff behavior.

## Verification

```bash
npm test
npm run typecheck
npm run build
npm audit
```

## Decision: ADOPT

**Demonstrated utility:** the executable fixture renders two independent file
diffs using `@pierre/diffs` and places the SQL and performance findings on their
specified additions lines. It also renders a searchable, path-first tree with
Git `modified` status and per-file finding counts. The small mapping layer uses
only the established review contract, so it does not couple the reviewer to a
UI transport.

**Maintenance cost:** retain the workbench as an optional, isolated frontend.
The libraries add a significant syntax-highlighting build payload (Vite reports
a 971 kB uncompressed entry chunk) and `@pierre/trees` is beta (`1.0.0-beta.6`),
so a production rollout should pin versions, add browser interaction tests, and
track bundle size/API compatibility. That cost is contained because core Python
evaluation and reviewer dependencies remain unchanged.
