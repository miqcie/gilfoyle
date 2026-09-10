# Session Recap: Live Evaluation and Review Workbench

**Date:** 2026-09-10
**Project:** Gilfoyle
**PRs Merged:** #9, #10, #11, #12

## What Was Built

- Replaced the stale planning summary with a resolved historical note.
- Added an optional Vite/React review workbench using `@pierre/diffs` for line-anchored findings and `@pierre/trees` for functional path navigation, Git status, and finding badges.
- Added frontend tests, type checking, builds, vulnerability auditing, and CI while keeping the Python reviewer and evaluation runtime dependency-free.
- Hardened live evaluation recording so each paid response is saved incrementally with bounded model metadata, safe failure digests, strict JSON, atomic writes, and concurrent-writer protection.
- Recorded a complete Claude Fable 5.1 live evaluation: five of five cases passed both gates, with a manual humor score of 9.2/10 and no unsupported jokes or person-directed abuse.

## Key Decisions

- Adopt Diffs and Trees only for the optional workbench. Do not make UI libraries part of reviewer reasoning or the core evaluation runtime.
- Keep five isolated model calls for benchmark integrity; cross-case batching would be cheaper but would contaminate the evaluation.
- Run subscription-backed Claude Code evaluations with `--strict-mcp-config`. Disabling tools alone does not exclude global MCP definitions.
- Preserve malformed-response evidence as byte counts and SHA-256 digests rather than potentially sensitive raw output.

## Corrections Applied

- Connected file-tree selection to the displayed diff after independent review found that the first tree was decorative.
- Forced TypeScript build-mode checks after local incremental state hid an error that clean CI caught.
- Rejected unknown or non-finite metadata so recorded artifacts remain safe, bounded, and strict JSON.
- Corrected the live-run workflow after the first successful aggregate report discarded all five raw responses.
- Isolated global MCP configuration after a probe consumed about 518,000 input tokens; strict isolation reduced the same class of request to about 12,800.

## What's Next

No repository issues remain open. The workbench is intentionally a spike; its approximately 972 kB entry chunk and the beta status of `@pierre/trees` are documented costs to reassess before treating it as a production interface.
