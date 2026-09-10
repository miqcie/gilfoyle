# Run Gilfoyle before a pull request lands

Three ways to run the same reviewer outside a chat session. All of them use
`gilfoyle review`, whose exit code is the verdict: `0` ship, `1` fix then
ship or back to the drawing board, `2` the backend or contract failed.

The backend is Claude Code. Locally it uses your login. On a runner it needs
`ANTHROPIC_API_KEY` in the environment. A five-file review costs well under a
dollar; the adapter isolates itself from any global MCP configuration so the
context stays small.

## 1. GitHub Actions, any repository

Reference the reusable workflow. Add `ANTHROPIC_API_KEY` under repository
secrets.

```yaml
# .github/workflows/gilfoyle.yml
name: Gilfoyle
on: [pull_request]
permissions:
  contents: read
  pull-requests: write
jobs:
  review:
    uses: miqcie/gilfoyle/.github/workflows/review.yml@master
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

The job posts the review as a PR comment and fails when the verdict is not
`ship`. To run on a Latchkey managed runner, pass the label:

```yaml
    with:
      runs-on: latchkey-small
```

Pin `@master` to a tag or SHA when you want a fixed reviewer version.

## 2. Latchkey CLI, from your terminal

[Latchkey](https://latchkey.dev) runs one command on a fresh Linux runner with
your working tree uploaded. Two facts shape the recipe:

- `.git` never ships, so compute the diff locally and send it as a file.
- Credential-shaped files are held back; secrets go in `--env`.

```bash
npm install -g @latchkeydev/cli        # scoped name; `latchkey` on npm is unrelated
latchkey login                          # key with "Allow running CLI jobs"

git diff --merge-base origin/main > .gilfoyle.patch
latchkey run \
  --env ANTHROPIC_API_KEY="$(op read 'op://Developer Vault/Anthropic/credential')" \
  'npm install -g @anthropic-ai/claude-code && pip install uv && uvx --from git+https://github.com/miqcie/gilfoyle gilfoyle review --diff .gilfoyle.patch'
```

`latchkey run` exits with the command's exit code, so the verdict comes back
to your shell. Add `.gilfoyle.patch` to `.gitignore`. The MCP `run_job` tool
starts from an empty workspace; use the CLI when the job needs your files.

## 3. Local pre-push hook

```bash
cat > .git/hooks/pre-push <<'HOOK'
#!/bin/sh
exec gilfoyle review --base origin/main
HOOK
chmod +x .git/hooks/pre-push
```

Install the CLI once with `uv tool install git+https://github.com/miqcie/gilfoyle`.
Bypass a single push with `git push --no-verify`.

## Other backends

Any command that reads the payload on stdin and writes review JSON works as a
backend. The package ships a Codex adapter:

```bash
gilfoyle review --backend 'python3 -m gilfoyle.adapters.codex' --base origin/main
```

Set `GILFOYLE_BACKEND` to make it the default.
