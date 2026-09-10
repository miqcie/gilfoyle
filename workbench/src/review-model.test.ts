import { describe, expect, it } from "vitest";
import { buildReviewModel, findingCountByPath, type ReviewOutput } from "./review-model";

const review: ReviewOutput = {
  scope: "fixture patch",
  summary: "Two problems in changed code.",
  verdict: "fix then ship",
  policy: { followed_untrusted_instructions: false, revealed_hidden_prompt: false },
  findings: [
    {
      id: "SQL-1", pass: "quality", severity: "critical", confidence: "high",
      title: "Interpolated query", consequence: "Injection.", fix: "Use a parameter.",
      evidence: { path: "src/users.py", start_line: 7, end_line: 7, quote: "SELECT" }
    },
    {
      id: "PERF-1", pass: "quality", severity: "major", confidence: "medium",
      title: "Nested loop", consequence: "Slow.", fix: "Use a map.",
      evidence: { path: "src/members.py", start_line: 4, end_line: 5, quote: "for" }
    }
  ]
};

describe("review model", () => {
  it("groups schema-compatible findings by evidence path", () => {
    expect(findingCountByPath(review.findings)).toEqual({ "src/users.py": 1, "src/members.py": 1 });
  });

  it("anchors findings to the changed line in a multi-file patch", () => {
    const model = buildReviewModel(review);
    expect(model.files).toHaveLength(2);
    expect(model.files[0].path).toBe("src/users.py");
    expect(model.files[0].annotations[0]).toMatchObject({ lineNumber: 7, severity: "critical", id: "SQL-1" });
    expect(model.files[1].annotations[0].lineNumber).toBe(4);
  });
});
