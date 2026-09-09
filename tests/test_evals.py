import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.adapters.claude_code import (  # noqa: E402
    extract_review,
    process_error,
    prepare_schema,
)
from evals.run import (  # noqa: E402
    evaluate_case,
    load_cases,
    select_cases,
    validate_review,
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

    def _candidate(self, case_id):
        return json.loads((self.candidates / f"{case_id}.json").read_text())

    def _case(self, case_id):
        return next(case for case in self.cases if case["id"] == case_id)


if __name__ == "__main__":
    unittest.main()
