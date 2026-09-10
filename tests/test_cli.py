import io
import json
import shlex
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gilfoyle.adapters.codex import build_command, read_review, strict_schema  # noqa: E402
from gilfoyle.cli import (  # noqa: E402
    DEFAULT_BACKEND,
    build_payload,
    main,
    paths_in_patch,
    render_markdown,
)

PATCH = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
 x = 1
+y = 2
diff --git a/gone.py b/gone.py
--- a/gone.py
+++ /dev/null
"""

REVIEW = {
    "scope": "app.py",
    "summary": "One line, one problem.",
    "verdict": "fix then ship",
    "policy": {"followed_untrusted_instructions": False, "revealed_hidden_prompt": False},
    "findings": [
        {
            "id": "unused",
            "pass": "quality",
            "severity": "minor",
            "confidence": "high",
            "title": "y is never read",
            "evidence": {"path": "app.py", "start_line": 2, "end_line": 2, "quote": "y = 2"},
            "consequence": "Dead state that the next reader has to prove dead again.",
            "fix": "Delete it.",
        }
    ],
}


class CliTests(unittest.TestCase):
    def test_patch_paths_skip_deletions_and_strip_prefix(self):
        self.assertEqual(paths_in_patch(PATCH), ["app.py"])

    def test_payload_from_patch_file_needs_no_git(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "app.py").write_text("x = 1\ny = 2\n")
            patch = directory / "change.patch"
            patch.write_text(PATCH)
            cwd = Path.cwd()
            try:
                import os

                os.chdir(directory)
                payload = build_payload(diff=str(patch), spec="Keep it small.")
            finally:
                os.chdir(cwd)
        self.assertEqual(payload["diff"], PATCH)
        self.assertEqual(list(payload["repository_files"]), ["app.py"])
        self.assertEqual(payload["case"]["trusted_requirements"], ["Keep it small."])

    def test_markdown_render_and_blocking_exit_code(self):
        rendered = render_markdown(REVIEW)
        self.assertIn("Scope: app.py", rendered)
        self.assertIn("`app.py:2` — [quality, high] y is never read", rendered)
        self.assertTrue(rendered.endswith("Verdict: fix then ship\n"))

        with TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "app.py").write_text("x = 1\ny = 2\n")
            canned = directory / "review.json"
            canned.write_text(json.dumps(REVIEW))
            patch = directory / "change.patch"
            patch.write_text(PATCH)
            out = directory / "out.md"
            backend = f"cat {shlex.quote(str(canned))}"
            import os

            cwd = Path.cwd()
            try:
                os.chdir(directory)
                with redirect_stdout(io.StringIO()) as stdout:
                    code = main(
                        ["review", "--diff", str(patch), "--backend", backend, "--out", str(out)]
                    )
            finally:
                os.chdir(cwd)
            self.assertEqual(code, 1)
            self.assertEqual(stdout.getvalue(), out.read_text())

    def test_invalid_backend_output_is_exit_2(self):
        with TemporaryDirectory() as directory:
            patch = Path(directory) / "change.patch"
            patch.write_text(PATCH)
            with redirect_stdout(io.StringIO()):
                code = main(["review", "--diff", str(patch), "--backend", "echo '{}'"])
        self.assertEqual(code, 2)

    def test_git_mode_reads_files_from_repo_root_in_a_subdirectory(self):
        import os
        import subprocess

        with TemporaryDirectory() as directory:
            directory = Path(directory)
            run = lambda *args: subprocess.run(  # noqa: E731
                ["git", "-C", str(directory), *args], check=True, capture_output=True
            )
            run("init", "-q")
            run("config", "user.email", "t@example.com")
            run("config", "user.name", "t")
            (directory / "sub").mkdir()
            (directory / "sub/app.py").write_text("x = 1\n")
            run("add", ".")
            run("commit", "-q", "-m", "init")
            (directory / "sub/app.py").write_text("x = 1\ny = 2\n")
            cwd = Path.cwd()
            try:
                os.chdir(directory / "sub")
                payload = build_payload(base="HEAD")
                self.assertEqual(payload["repository_files"], {"sub/app.py": "x = 1\ny = 2\n"})
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["review", "--base", "nope"]), 2)
            finally:
                os.chdir(cwd)

    def test_unverifiable_evidence_is_exit_2(self):
        bad = json.loads(json.dumps(REVIEW))
        bad["findings"][0]["evidence"]["quote"] = "not in the file"
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "app.py").write_text("x = 1\ny = 2\n")
            canned = directory / "review.json"
            canned.write_text(json.dumps(bad))
            patch = directory / "change.patch"
            patch.write_text(PATCH)
            import os

            cwd = Path.cwd()
            try:
                os.chdir(directory)
                with redirect_stdout(io.StringIO()):
                    code = main(["review", "--diff", str(patch), "--backend", f"cat {shlex.quote(str(canned))}"])
            finally:
                os.chdir(cwd)
        self.assertEqual(code, 2)

    def test_missing_path_and_mixed_scope_flags_fail_loudly(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["review", "does-not-exist.py", "--backend", "true"]), 2)
        with self.assertRaises(SystemExit) as raised:
            main(["review", "x.py", "--base", "main"])
        self.assertEqual(raised.exception.code, 2)

    def test_strict_schema_and_null_test_stripping(self):
        schema = json.loads((ROOT / "gilfoyle/review-output.schema.json").read_text())
        strict = strict_schema(schema)
        finding = strict["properties"]["findings"]["items"]
        self.assertEqual(finding["required"], sorted(finding["properties"]))
        self.assertEqual(finding["properties"]["test"], {"type": ["string", "null"]})
        with TemporaryDirectory() as directory:
            out = Path(directory) / "review.json"
            review = json.loads(json.dumps(REVIEW))
            review["findings"][0]["test"] = None
            out.write_text(json.dumps(review))
            self.assertNotIn("test", read_review(out)["findings"][0])
            review["findings"][0]["test"] = "assert_raises"
            out.write_text(json.dumps(review))
            self.assertEqual(read_review(out)["findings"][0]["test"], "assert_raises")

    def test_directory_scope_skips_dotdirs_and_git_ignored_files(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "src").mkdir()
            (directory / "src/app.py").write_text("x = 1\n")
            (directory / ".env").write_text("SECRET=1\n")
            (directory / "node_modules").mkdir()
            (directory / "node_modules/x.js").write_text("1\n")
            payload = build_payload(paths=[str(directory)])
            self.assertEqual(list(payload["repository_files"]), [str(directory / "src/app.py")])

    def test_quote_from_deleted_file_is_accepted_via_patch(self):
        from gilfoyle.contract import validate_evidence

        review = json.loads(json.dumps(REVIEW))
        review["findings"][0]["evidence"] = {
            "path": "gone.py", "start_line": 1, "end_line": 1, "quote": "+++ /dev/null"
        }
        self.assertEqual(validate_evidence(review, {}, PATCH), [])
        self.assertEqual(len(validate_evidence(review, {}, None)), 1)
        from gilfoyle.contract import patch_section

        nested = "diff --git a/src/a/gone.py b/src/a/gone.py\n--- a/src/a/gone.py\n+++ /dev/null\n-nested\n" + PATCH
        self.assertIn("+++ /dev/null\n", patch_section(nested, "gone.py"))
        self.assertNotIn("nested", patch_section(nested, "gone.py"))
        self.assertIsNone(patch_section(nested, "one.py"))
        review["findings"][0]["evidence"]["path"] = "made-up.py"
        self.assertEqual(len(validate_evidence(review, {}, PATCH)), 1)
        review["findings"][0]["evidence"] = {
            "path": "app.py", "start_line": 1, "end_line": 1, "quote": "+++ /dev/null"
        }
        self.assertEqual(len(validate_evidence(review, {}, PATCH)), 1)

    def test_default_backend_quotes_the_interpreter(self):
        self.assertEqual(shlex.split(DEFAULT_BACKEND)[0], sys.executable)

    def test_codex_command_shape(self):
        command = build_command("/w", "/w/s.json", "/w/o.json")
        self.assertEqual(command[-1], "-")
        self.assertIn("--ignore-user-config", command)
        self.assertNotIn("-m", command)
        self.assertIn("-m", build_command("/w", "/w/s.json", "/w/o.json", model="x"))


if __name__ == "__main__":
    unittest.main()
