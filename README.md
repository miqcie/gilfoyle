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
- First-class Claude Code plugin and native Hermes skill packaging.

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

### Hermes Agent skill

```bash
hermes skills install https://raw.githubusercontent.com/miqcie/gilfoyle/master/skills/gilfoyle/SKILL.md
```

Ask Hermes for a Gilfoyle review or explicitly load `gilfoyle`. Consequential reviews should run in an independent subagent; blocking findings must still be reproduced before code is changed.

### Legacy Claude Code copy

Existing copy-based installations remain supported:

```bash
mkdir -p ~/.claude/agents ~/.claude/commands
cp gilfoyle-tech-reviewer.md ~/.claude/agents/
cp gilfoyle.md ~/.claude/commands/
```

The plugin is preferred because copied files quietly become archaeological artifacts.

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
python3 evals/run.py --live-command 'python3 evals/adapters/claude_code.py'
```

The included Claude Code adapter defaults to Chris’s preferred `fable` model. Override it with `GILFOYLE_CLAUDE_MODEL`; provider limits and live-run costs remain the operator’s responsibility.

See `evals/README.md` and `evals/contracts/review-output.schema.json`.

The suite covers:

- a clean null-safe refactor that should produce no findings;
- specification drift;
- SQL injection;
- quadratic request-path behavior;
- prompt injection embedded in repository content.

Humor is scored manually for dry wit, specificity, restraint, intent, and distinctive voice. Counting jokes would be metrics theater, and he would be unbearable about it.

## Possible review workbench

[`@pierre/diffs`](https://diffs.com/docs) is a strong fit for rendered patches and inline findings. [`@pierre/trees`](https://trees.software/docs) is a strong fit for path-first repository navigation, Git status, and finding badges. The evaluation contract is UI-neutral so those can power a future workbench without becoming dependencies of the reviewer itself.

## Contributing

Add regression fixtures for real misses and false positives. Do not lengthen the prompt with generic reviewer boilerplate; models already know what a loop is. Improve the decisions, evidence, or evaluation.

## License

MIT. Even Gilfoyle believes in open source, although presumably for reasons involving contempt for procurement.
