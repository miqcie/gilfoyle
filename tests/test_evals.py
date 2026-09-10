import copy
import json
import shlex
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.adapters.claude_code import (  # noqa: E402
    extract_response,
    extract_review,
    process_error,
    prepare_schema,
)
from evals.run import (  # noqa: E402
    LiveReviewError,
    _live_review,
    acquire_record_lock,
    evaluate_case,
    load_cases,
    release_record_lock,
    run_evaluations,
    sanitize_metadata,
    select_cases,
    validate_review,
    write_live_record,
)


class EvaluationHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(ROOT / "evals/fixtures")
        cls.candidates = ROOT / "evals/candidates"

    def test_fixture_suite_has_clean_spec_security_performance_and_injection_cases(self):
        ids = {case["id"] for case in self.cases}
        self.assertTrue(
            {
                "clean-null-refactor",
                "spec-mismatch",
                "sql-interpolation",
                "quadratic-hot-path",
                "prompt-injection-comment",
            }.issubset(ids)
        )

    def test_checked_in_reference_reviews_pass(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                review = json.loads(
                    (self.candidates / f"{case['id']}.json").read_text()
                )
                result = evaluate_case(case, review, ROOT / "evals/fixtures")
                self.assertTrue(result["passed"], result)

    def test_non_object_evidence_is_rejected_without_crashing(self):
        case = self._case("sql-interpolation")
        review = self._candidate("sql-interpolation")
        review["findings"][0]["evidence"] = "trust me"
        result = evaluate_case(case, review, ROOT / "evals/fixtures")
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("evidence must be an object" in error for error in result["hard_failures"])
        )

    def test_malformed_evidence_path_is_rejected_without_crashing(self):
        case = self._case("sql-interpolation")
        review = self._candidate("sql-interpolation")
        review["findings"][0]["evidence"]["path"] = 1
        result = evaluate_case(case, review, ROOT / "evals/fixtures")
        self.assertFalse(result["passed"])
        self.assertTrue(any("path" in error for error in result["hard_failures"]))

    def test_unknown_case_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown case"):
            select_cases(self.cases, ["does-not-exist"])

    def test_missing_evidence_is_a_hard_failure(self):
        review = self._candidate("sql-interpolation")
        del review["findings"][0]["evidence"]
        errors = validate_review(review)
        self.assertTrue(any("evidence" in error for error in errors), errors)

    def test_noise_on_clean_change_fails(self):
        case = self._case("clean-null-refactor")
        review = self._candidate("clean-null-refactor")
        review["findings"].append(
            {
                "id": "imaginary-problem",
                "pass": "quality",
                "severity": "minor",
                "confidence": "low",
                "title": "A decorative complaint",
                "evidence": {
                    "path": "src/format_name.py",
                    "start_line": 1,
                    "end_line": 1,
                    "quote": "def format_name(name: str | None) -> str:",
                },
                "consequence": "None demonstrated.",
                "fix": "Do nothing differently.",
            }
        )
        review["verdict"] = "fix then ship"
        result = evaluate_case(case, review, ROOT / "evals/fixtures")
        self.assertFalse(result["quality"]["passed"])

    def test_following_repository_prompt_injection_is_a_hard_failure(self):
        case = self._case("prompt-injection-comment")
        review = self._candidate("prompt-injection-comment")
        review["policy"]["followed_untrusted_instructions"] = True
        result = evaluate_case(case, review, ROOT / "evals/fixtures")
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("untrusted" in reason for reason in result["hard_failures"])
        )

    def test_severity_order_is_enforced(self):
        review = self._candidate("sql-interpolation")
        second = copy.deepcopy(review["findings"][0])
        second["id"] = "second"
        second["severity"] = "critical"
        review["findings"][0]["severity"] = "minor"
        review["findings"].append(second)
        errors = validate_review(review)
        self.assertTrue(any("severity order" in error for error in errors), errors)

    def test_claude_adapter_surfaces_stdout_api_errors(self):
        message = process_error(
            '{"is_error":true,"result":"session limit reached"}', "", 1
        )
        self.assertIn("session limit reached", message)

    def test_claude_adapter_removes_unsupported_schema_metadata(self):
        self.assertEqual(
            prepare_schema({"$schema": "draft", "type": "object"}),
            {"type": "object"},
        )

    def test_claude_adapter_extracts_structured_output_and_result_json(self):
        review = self._candidate("clean-null-refactor")
        self.assertEqual(extract_review(json.dumps(review)), review)
        self.assertEqual(
            extract_review(json.dumps({"structured_output": review})), review
        )
        self.assertEqual(
            extract_review(json.dumps({"result": json.dumps(review)})), review
        )

    def test_claude_adapter_preserves_model_metadata_for_recording(self):
        review = self._candidate("clean-null-refactor")
        output = json.dumps(
            {
                "structured_output": review,
                "modelUsage": {"claude-fable-5-1": {"inputTokens": 10}},
            }
        )
        actual, metadata = extract_response(output)
        self.assertEqual(actual, review)
        self.assertEqual(metadata["model_ids"], ["claude-fable-5-1"])

    def test_live_review_accepts_recording_envelope(self):
        review = self._candidate("clean-null-refactor")
        envelope = json.dumps(
            {
                "review": review,
                "metadata": {
                    "requested_model": "fable",
                    "model_ids": ["claude-fable-5-1"],
                },
            }
        )
        command = f"python3 -c {shlex.quote(f'print({envelope!r})')}"
        actual, metadata = _live_review(
            command,
            self._case("clean-null-refactor"),
            ROOT / "evals/fixtures",
        )
        self.assertEqual(actual, review)
        self.assertEqual(metadata["model_ids"], ["claude-fable-5-1"])

    def test_live_record_keeps_raw_reviews_and_progress(self):
        from tempfile import TemporaryDirectory

        review = self._candidate("clean-null-refactor")
        evaluation = evaluate_case(
            self._case("clean-null-refactor"), review, ROOT / "evals/fixtures"
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "live.json"
            write_live_record(
                path,
                [{
                    "id": "clean-null-refactor",
                    "review": review,
                    "metadata": {
                        "requested_model": "fable",
                        "model_ids": ["claude-fable-5-1"],
                    },
                    "evaluation": evaluation,
                }],
                complete=False,
            )
            artifact = json.loads(path.read_text())
        self.assertFalse(artifact["complete"])
        self.assertEqual(artifact["cases"][0]["review"], review)
        self.assertEqual(
            artifact["cases"][0]["metadata"]["model_ids"],
            ["claude-fable-5-1"],
        )

    def test_live_record_drops_unknown_and_secret_metadata(self):
        metadata = sanitize_metadata(
            {
                "requested_model": "fable",
                "model_ids": ["claude-fable-5-1"],
                "api_key": "super-secret",
                "authorization": "Bearer super-secret",
                "nested": {"token": "super-secret"},
                "total_cost_usd": float("inf"),
                "duration_ms": float("nan"),
            }
        )
        self.assertEqual(
            metadata,
            {
                "requested_model": "fable",
                "model_ids": ["claude-fable-5-1"],
            },
        )
        self.assertNotIn("super-secret", json.dumps(metadata))

    def test_live_record_is_strict_json(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            path = Path(directory) / "live.json"
            write_live_record(path, [], complete=False)
            with self.assertRaises(ValueError):
                write_live_record(
                    path,
                    [{"metadata": {"total_cost_usd": float("inf")}}],
                    complete=False,
                )
            artifact = json.loads(
                path.read_text(),
                parse_constant=lambda value: self.fail(
                    f"non-standard JSON constant: {value}"
                ),
            )
        self.assertFalse(artifact["complete"])
        self.assertEqual(artifact["cases"], [])

    def test_invalid_json_is_recorded_on_first_and_later_cases(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            directory = Path(directory)
            adapter = directory / "adapter.py"
            adapter.write_text(
                "import json, sys\n"
                "from pathlib import Path\n"
                "payload = json.load(sys.stdin)\n"
                "case_id = payload['case']['id']\n"
                "if case_id == sys.argv[1]:\n"
                "    print('api_key=super-secret not-json')\n"
                "else:\n"
                f"    root = Path({str(self.candidates)!r})\n"
                "    review = json.loads((root / f'{case_id}.json').read_text())\n"
                "    print(json.dumps(review))\n"
            )
            clean = self._case("clean-null-refactor")
            injection = self._case("prompt-injection-comment")

            first_record = directory / "first.json"
            with self.assertRaises(LiveReviewError):
                run_evaluations(
                    [clean],
                    ROOT / "evals/fixtures",
                    self.candidates,
                    live_command=f"python3 {shlex.quote(str(adapter))} clean-null-refactor",
                    record=first_record,
                )
            first = json.loads(first_record.read_text())
            self.assertFalse(first["complete"])
            self.assertEqual(first["cases"][0]["failure"]["kind"], "invalid_json")
            self.assertNotIn("super-secret", first_record.read_text())

            later_record = directory / "later.json"
            with self.assertRaises(LiveReviewError):
                run_evaluations(
                    [clean, injection],
                    ROOT / "evals/fixtures",
                    self.candidates,
                    live_command=f"python3 {shlex.quote(str(adapter))} prompt-injection-comment",
                    record=later_record,
                )
            later = json.loads(later_record.read_text())
            self.assertFalse(later["complete"])
            self.assertEqual(later["cases"][0]["id"], "clean-null-refactor")
            self.assertIn("review", later["cases"][0])
            self.assertEqual(later["cases"][1]["failure"]["kind"], "invalid_json")
            self.assertNotIn("super-secret", later_record.read_text())

    def test_record_lock_rejects_a_concurrent_writer(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            path = Path(directory) / "live.json"
            first = acquire_record_lock(path)
            try:
                with self.assertRaisesRegex(ValueError, "already in use"):
                    acquire_record_lock(path)
            finally:
                release_record_lock(first)

    def _candidate(self, case_id):
        return json.loads((self.candidates / f"{case_id}.json").read_text())

    def _case(self, case_id):
        return next(case for case in self.cases if case["id"] == case_id)


if __name__ == "__main__":
    unittest.main()
