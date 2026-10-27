# Papercuts

- 2026-09-09: passing a standards-compliant `$schema` URI to Claude Code `--json-schema` → the CLI rejected the draft URI, so the adapter must strip schema metadata before invocation.
- 2026-09-09: Claude Code returned provider/session-limit failures as JSON on stdout with exit 1 and empty stderr → the adapter must inspect both streams to preserve the useful error.
- 2026-09-09: `hermes skills inspect gilfoyle` failed immediately after a successful URL install while `hermes skills list` and the installed `SKILL.md` showed it enabled → use list plus the installed file as verification until resolver behavior is clarified.
- 2026-09-10: a successful five-case live evaluation emitted only aggregate scores → raw paid responses were discarded and the attempted rerun exhausted the Fable allowance; incremental recording now writes each case immediately.
- 2026-09-10: `--tools ""` still let Claude Code load the global MCP configuration into a live evaluation → one probe consumed 518K input tokens instead of 12.8K; the adapter now requires `--strict-mcp-config`.
- 2026-09-10: local TypeScript incremental state reported the workbench clean while fresh CI found a type error → workbench typecheck and build now pass `tsc -b --force`.
- 2026-09-10: `codex exec` adapter inherited the user's whole Codex config (MCP servers, hooks, a pinned model the installed CLI could not run) → `--ignore-user-config`, the Codex twin of `--strict-mcp-config`.
- 2026-09-10: OpenAI strict output schema rejected the optional `test` finding field → the Codex adapter rewrites the schema (every property required, `test` nullable) and strips nulls on the way back.
- 2026-09-10: running `latchkey login` via the Claude Code `!` prefix → no TTY for the hidden prompt; needs a real terminal or `--token "$(op read ...)"`.
- 2026-09-10: Latchkey smoke job `which uv` (absent on the image) → job reported failed with exit 1 under the bash wrapper; runner `pip install` is externally managed, so `pipx run --spec git+...` is the install path.
- 2026-09-10: `echo ==label==` as a shell separator in zsh → equals-expansion error aborted the compound command; quote separators.
- 2026-09-11: `claude plugin eval init` run from `~` (no `.claude-plugin/plugin.json` there) → the interview started anyway instead of failing fast on a missing manifest, costing a round trip to discover there was no plugin at that path.
- 2026-09-11: `/wrap-up` step 4 (Notion sync) expects `mcp__notionApi__API-post-page` → not connected in this session, so the wrap-up ritual can't complete that step from a session without the Notion MCP attached.
