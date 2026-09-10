#!/usr/bin/env python3
"""Generate every harness wrapper from the canonical SKILL.md.

Run with no arguments to write the files; `--check` exits 1 if any committed
wrapper differs from what SKILL.md would generate.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"


def split_frontmatter(text):
    _, frontmatter, body = text.split("---\n", 2)
    fields = dict(line.split(": ", 1) for line in frontmatter.strip().splitlines())
    return fields, body.lstrip("\n")


def render(skill_text):
    fields, body = split_frontmatter(skill_text)
    description = fields["description"]
    header = "<!-- Generated from SKILL.md by scripts/build_integrations.py. Edit SKILL.md. -->\n"
    return {
        "plugins/gilfoyle/skills/gilfoyle/SKILL.md": skill_text,
        "plugins/gilfoyle/agents/gilfoyle-tech-reviewer.md": (
            "---\n"
            "name: gilfoyle-tech-reviewer\n"
            f"description: {description}\n"
            "model: inherit\n"
            "color: yellow\n"
            "---\n"
            f"{header}\n{body}"
        ),
        "integrations/hermes/SKILL.md": (
            "---\n"
            "name: gilfoyle\n"
            f"description: {description}\n"
            "version: 1.1.0\n"
            "author: Chris McConnell (miqcie)\n"
            "license: MIT\n"
            "platforms: [linux, macos, windows]\n"
            "metadata:\n"
            "  hermes:\n"
            "    tags: [code-review, security, architecture, ux, persona]\n"
            "---\n"
            f"{header}\n{body}"
        ),
        "integrations/codex/AGENTS.md": (
            f"{header}<!-- Append to your repository AGENTS.md, or place in ~/.codex/AGENTS.md. -->\n\n{body}"
        ),
        "integrations/cursor/gilfoyle.mdc": (
            "---\n"
            f"description: {description}\n"
            "alwaysApply: false\n"
            "---\n"
            f"{header}\n{body}"
        ),
    }


def main():
    outputs = render(SKILL.read_text())
    stale = []
    for relative, content in outputs.items():
        path = ROOT / relative
        if "--check" in sys.argv:
            if not path.exists() or path.read_text() != content:
                stale.append(relative)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    if stale:
        print("stale, run scripts/build_integrations.py:", *stale, sep="\n  ")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
