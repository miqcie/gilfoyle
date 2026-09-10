# Gilfoyle

> “Your code is bad and you should feel bad—but I’ll explain exactly why.”

Gilfoyle is an opinionated technical reviewer inspired by the systems architect from *Silicon Valley*. He reviews the change in front of him, separates specification failures from implementation failures, and supports every barb with evidence and a fix.

He is an asshole toward bad code and well meaning toward the person maintaining it. This distinction has saved more systems than most architecture committees.

## What changed in 1.0

- Two passes: specification compliance, then implementation quality.
- Evidence contract: location, confidence, consequence, fix, and regression test.
- Relevant lenses only: correctness, security, performance, simplification, architecture, UX, and testing.
- Prompt-injection boundary for instructions hidden in reviewed artifacts.
- Provider-neutral model inheritance instead of forcing Opus.
- Fixture-based evaluation of blockers, clean diffs, false positives, and injection resistance.
- One canonical `SKILL.md`; Claude Code plugin, Hermes, Codex, and Cursor wrappers generated from it.

## Install

### Claude Code plugin

Add this repository as a marketplace, then install the plugin:

```text
/plugin marketplace add miqcie/gilfoyle
/plugin install gilfoyle@gilfoyle
```

Invoke it with:

```text
/gilfoyle:gilfoyle <target>
```

For local plugin development:

```bash
claude plugin validate ./plugins/gilfoyle --strict
claude --plugin-dir ./plugins/gilfoyle
```

### Other harnesses

`SKILL.md` at the repository root is the canonical reviewer in the [Agent Skills](https://agentskills.io) format. Every wrapper under `plugins/` and `integrations/` is generated from it by `scripts/build_integrations.py`; CI fails if they drift.

| Harness | File | Install |
|---|---|---|
| Any Agent Skills reader (Codex, Gemini CLI, OpenCode, ...) | `SKILL.md` | copy into the harness's skills directory |
| Hermes Agent | `integrations/hermes/SKILL.md` | `hermes skills install https://raw.githubusercontent.com/miqcie/gilfoyle/master/integrations/hermes/SKILL.md` |
| Codex (rules) | `integrations/codex/AGENTS.md` | append to your repository `AGENTS.md` |
| Cursor | `integrations/cursor/gilfoyle.mdc` | copy to `.cursor/rules/` |

Consequential reviews should run in a fresh context (a subagent or a new session fed the diff); blocking findings must be reproduced before code is changed.

### Command line

Review before you push, from any harness or none. Stdlib only; needs `claude`
(or `codex`) on `PATH` for the backend.

```bash
uvx --from git+https://github.com/miqcie/gilfoyle gilfoyle review --base origin/main
gilfoyle review --diff change.patch          # no git needed, e.g. on a CI runner
gilfoyle review --backend 'python3 -m gilfoyle.adapters.codex' --base main
```

Exit code is the verdict: `0` ship, `1` fix then ship or back to the drawing
board, `2` backend or contract error. `--format json` emits the raw review;
`--out FILE` also writes the rendered review. Every evidence quote is checked
against the files sent to the reviewer before anything is printed.

## Review contract

Gilfoyle defaults to the current diff or named artifact. Whole-repository review requires an explicit request.

Every finding includes:

- severity and `spec` or `quality` pass;
- confidence;
- exact path and line or named design element;
- evidence and concrete consequence;
- specific fix and relevant regression test.

The verdict is `ship`, `fix then ship`, or `back to the drawing board`. Clean changes get a clean verdict, not invented objections assembled for dramatic tension.

## Evaluation

The replay suite is dependency-free and makes no provider calls:

```bash
python3 evals/run.py
python3 -m unittest discover -s tests -v
```

Optional live evaluation accepts any command that reads a JSON fixture from stdin and returns the documented review JSON:

```bash
python3 evals/run.py --live-command 'python3 -m gilfoyle.adapters.claude_code'
```

The included Claude Code adapter defaults to Chris’s preferred `fable` model. Override it with `GILFOYLE_CLAUDE_MODEL`; provider limits and live-run costs remain the operator’s responsibility.

See `evals/README.md` and `gilfoyle/review-output.schema.json`.

The suite covers:

- a clean null-safe refactor that should produce no findings;
- specification drift;
- SQL injection;
- quadratic request-path behavior;
- prompt injection embedded in repository content.

Humor is scored manually for dry wit, specificity, restraint, intent, and distinctive voice. Counting jokes would be metrics theater, and he would be unbearable about it.

## Review workbench spike

The optional [`workbench/`](workbench/README.md) is an executable Vite/React spike. It consumes review-output-schema-compatible data, uses [`@pierre/diffs`](https://diffs.com/docs) for multi-file line annotations and [`@pierre/trees`](https://trees.software/docs) for path-first navigation, Git status, and finding-count badges. Its dependencies are isolated from the Python reviewer and evaluation runtime. The evidence supports **ADOPT** as an optional frontend, while its README records the beta/API and bundle-size maintenance risks.

## Contributing

Add regression fixtures for real misses and false positives. Do not lengthen the prompt with generic reviewer boilerplate; models already know what a loop is. Improve the decisions, evidence, or evaluation.

## License

MIT. Even Gilfoyle believes in open source, although presumably for reasons involving contempt for procurement.
