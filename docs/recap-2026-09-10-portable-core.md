# Session Recap: Portable Gilfoyle Core

**Date:** 2026-09-10
**Project:** Gilfoyle (miqcie/gilfoyle)
**PRs Merged:** #11, #12, #14, #15, #16, #17

## What Was Built

- Closed issue #6: two evidence-loss bugs in the live recorder fixed, the five-case Fable 5.1 suite recorded (5/5, $1.20), humor scored manually at 9.2/10.
- `SKILL.md` at the repository root is the single reviewer text in the Agent Skills format. `scripts/build_integrations.py` generates the Claude Code plugin agent and skill plus Hermes, Codex, and Cursor integrations; CI fails on drift.
- `gilfoyle review` CLI, stdlib only: reviews a git diff, a patch file (no git needed), or paths. Exit code is the verdict. Evidence quotes are verified against the files sent to the reviewer, with a narrow allowance for removed lines that exist only in the patch.
- Backends are commands on stdin/stdout. Claude Code is the default; a Codex adapter ships alongside. Both isolate from the user's global config.
- `pyproject.toml` so `uvx --from git+https://github.com/miqcie/gilfoyle gilfoyle review` works; the skill and schema ship inside the package.
- Reusable GitHub Actions workflow that comments the review on PRs and fails on a non-ship verdict, skipping cleanly when no API key is set. `docs/run-in-ci.md` covers Actions, the Latchkey CLI, and a pre-push hook; the Latchkey recipe was verified on a real runner up to the model call.

## Key Decisions

| Decision | Rationale |
|---|---|
| SKILL.md canonical, wrappers generated | Four hand copies had already drifted; the skill format is read by every harness |
| Agent body inlined by the generator | Subagents do not auto-load skills; the wrapper must be self-contained |
| Backend = any command on stdin/stdout | The eval harness already defined the contract; no provider abstraction needed |
| `--strict-mcp-config` and `--ignore-user-config` mandatory | A one-word `claude -p` probe cost 518K tokens with global MCP config; Codex inherited a model the CLI could not run |
| Runner reviews need a dedicated API key | Subscription auth exists only where a login happened; the local hook is the free path |
| `pipx run` on Latchkey, not `uv` | The runner image has pipx but no uv, and pip is externally managed |

## Corrections Applied

- Gilfoyle reviewed its own CLI twice. Round one found three majors (cwd-relative reads, unverified evidence, Codex metadata labeled as Claude Code); round two only minors. All fixed.
- Bugbot ran nine further rounds on the evidence checker, each narrowing it: exact diff-header matching, quoted-name boundaries, removed-lines-only fallback, hunk-scoped collection.
- The Latchkey docs were corrected after a real run: `gh` is on the image, `uv` is not, `pip install` is blocked.

## What's Next

- #18: run the suite across Fable, Sonnet, Opus, and Codex to decide whether Fable earns its cost.
- #19: create a dedicated Anthropic API key with a spend cap and set it as the repo secret so the workflow and the Latchkey recipe reach the model.
- #20: have `--diff` verify the patch matches the working tree.
- Rotate the Latchkey key that was pasted into chat during setup.
