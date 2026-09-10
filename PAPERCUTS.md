# Papercuts

- 2026-09-09: passing a standards-compliant `$schema` URI to Claude Code `--json-schema` → the CLI rejected the draft URI, so the adapter must strip schema metadata before invocation.
- 2026-09-09: Claude Code returned provider/session-limit failures as JSON on stdout with exit 1 and empty stderr → the adapter must inspect both streams to preserve the useful error.
- 2026-09-09: `hermes skills inspect gilfoyle` failed immediately after a successful URL install while `hermes skills list` and the installed `SKILL.md` showed it enabled → use list plus the installed file as verification until resolver behavior is clarified.
- 2026-09-10: a successful five-case live evaluation emitted only aggregate scores → raw paid responses were discarded and the attempted rerun exhausted the Fable allowance; incremental recording now writes each case immediately.
- 2026-09-10: `--tools ""` still let Claude Code load the global MCP configuration into a live evaluation → one probe consumed 518K input tokens instead of 12.8K; the adapter now requires `--strict-mcp-config`.
- 2026-09-10: local TypeScript incremental state reported the workbench clean while fresh CI found a type error → workbench typecheck and build now pass `tsc -b --force`.
