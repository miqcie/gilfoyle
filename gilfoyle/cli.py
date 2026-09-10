#!/usr/bin/env python3
"""`gilfoyle review`: run the reviewer on a diff, a patch file, or paths."""

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from gilfoyle.contract import (
    LiveReviewError,
    call_backend,
    validate_evidence,
    validate_review,
)

DEFAULT_BACKEND = f"{shlex.quote(sys.executable)} -m gilfoyle.adapters.claude_code"
BLOCKING_VERDICTS = {"fix then ship", "back to the drawing board"}


class ScopeError(RuntimeError):
    pass


def _git(*args):
    process = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if process.returncode:
        raise ScopeError(f"git {args[0]} failed: {process.stderr.strip()}")
    return process.stdout


def _read_text(path):
    try:
        return Path(path).read_text()
    except (UnicodeDecodeError, OSError):
        return None


def _repo_root():
    try:
        return Path(_git("rev-parse", "--show-toplevel").strip())
    except ScopeError:
        return None


def paths_in_patch(patch):
    """Return the post-image paths named by unified-diff headers."""
    paths = []
    for line in patch.splitlines():
        if line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            name = line[4:].split("\t")[0]
            paths.append(name[2:] if name.startswith("b/") else name)
    return paths


def build_payload(base=None, diff=None, paths=(), request=None, spec=None):
    """Build the backend payload: trusted intent, changed files, and the patch."""
    patch = None
    if diff:
        patch = Path(diff).read_text()
        root = _repo_root() or Path.cwd()
        names = [(name, root / name) for name in paths_in_patch(patch)]
    elif paths:
        names = []
        for path in paths:
            path = Path(path)
            if path.is_dir():
                names.extend((str(p), p) for p in sorted(path.rglob("*")) if p.is_file())
            elif path.is_file():
                names.append((str(path), path))
            else:
                raise ScopeError(f"no such file or directory: {path}")
    else:
        base = base or "HEAD"
        root = _repo_root()
        if root is None:
            raise ScopeError("not a git repository; use --diff or name paths")
        patch = _git("diff", "--merge-base", base)
        names = [
            (name, root / name)
            for name in _git("diff", "-z", "--name-only", "--merge-base", base).split("\0")
            if name
        ]
    files = {}
    for display, path in names:
        text = _read_text(path)
        if text is not None:
            files[display] = text
    case = {
        "id": "cli",
        "request": request or "Review this change.",
        "trusted_requirements": [spec] if spec else [],
    }
    payload = {"case": case, "repository_files": files}
    if patch is not None:
        payload["diff"] = patch
    return payload


def render_markdown(review):
    lines = [f"Scope: {review['scope']}", "", review["summary"], ""]
    for severity in ("critical", "major", "minor"):
        group = [f for f in review["findings"] if f["severity"] == severity]
        if not group:
            continue
        lines.append(f"## {severity.capitalize()}")
        for finding in group:
            evidence = finding["evidence"]
            span = f"{evidence['path']}:{evidence['start_line']}"
            if evidence["end_line"] != evidence["start_line"]:
                span += f"-{evidence['end_line']}"
            lines.append(
                f"- `{span}` — [{finding['pass']}, {finding['confidence']}] "
                f"{finding['title']} — {finding['consequence']} — {finding['fix']}"
            )
            if finding.get("test"):
                lines.append(f"  - test: {finding['test']}")
        lines.append("")
    lines.append(f"Verdict: {review['verdict']}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gilfoyle")
    sub = parser.add_subparsers(dest="command", required=True)
    review = sub.add_parser("review", help="review a diff, patch file, or paths")
    review.add_argument("paths", nargs="*", help="files or directories to review whole")
    review.add_argument("--base", help="git ref to diff against (default: HEAD)")
    review.add_argument("--diff", help="unified diff file to review instead of git")
    review.add_argument("--request", help="what the change was supposed to do")
    review.add_argument("--spec", help="one trusted requirement the change must meet")
    review.add_argument(
        "--backend",
        default=os.getenv("GILFOYLE_BACKEND", DEFAULT_BACKEND),
        help="command that reads the payload on stdin and writes review JSON",
    )
    review.add_argument("--format", choices=("md", "json"), default="md")
    review.add_argument("--out", help="write the rendered review here as well as stdout")
    args = parser.parse_args(argv)
    if args.paths and (args.base or args.diff):
        parser.error("paths cannot be combined with --base or --diff")
    if args.base and args.diff:
        parser.error("--base and --diff are mutually exclusive")

    try:
        payload = build_payload(args.base, args.diff, args.paths, args.request, args.spec)
    except (ScopeError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if not payload["repository_files"] and not payload.get("diff"):
        print("nothing to review", file=sys.stderr)
        return 0
    try:
        result, _ = call_backend(args.backend, payload)
    except LiveReviewError as error:
        print(str(error), file=sys.stderr)
        return 2
    errors = validate_review(result)
    if not errors:
        errors = validate_evidence(result, payload["repository_files"])
    if errors:
        print("backend returned an invalid review:", *errors, sep="\n  ", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2) + "\n" if args.format == "json" else render_markdown(result)
    sys.stdout.write(text)
    if args.out:
        Path(args.out).write_text(text)
    policy = result["policy"]
    if policy["followed_untrusted_instructions"] or policy["revealed_hidden_prompt"]:
        print("policy violation reported by the reviewer", file=sys.stderr)
        return 1
    return 1 if result["verdict"] in BLOCKING_VERDICTS else 0


if __name__ == "__main__":
    raise SystemExit(main())
