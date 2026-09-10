export type Severity = "critical" | "major" | "minor";

export interface ReviewFinding {
  id: string;
  pass?: "spec" | "quality";
  severity: Severity;
  confidence?: "high" | "medium" | "low";
  title?: string;
  consequence?: string;
  fix?: string;
  test?: string;
  evidence: { path: string; start_line: number; end_line: number; quote: string };
}

export interface ReviewOutput {
  scope: string;
  summary: string;
  verdict: string;
  policy: { followed_untrusted_instructions: boolean; revealed_hidden_prompt: boolean };
  findings: ReviewFinding[];
}

export interface ReviewFile {
  path: string;
  annotations: Array<{ id: string; lineNumber: number; severity: Severity; quote: string }>;
}

export function findingCountByPath(findings: readonly ReviewFinding[]): Record<string, number> {
  return findings.reduce<Record<string, number>>((counts, finding) => {
    counts[finding.evidence.path] = (counts[finding.evidence.path] ?? 0) + 1;
    return counts;
  }, {});
}

export function buildReviewModel(review: ReviewOutput): { files: ReviewFile[] } {
  const byPath = new Map<string, ReviewFile>();
  for (const finding of review.findings) {
    const path = finding.evidence.path;
    const file = byPath.get(path) ?? { path, annotations: [] };
    file.annotations.push({
      id: finding.id,
      lineNumber: finding.evidence.start_line,
      severity: finding.severity,
      quote: finding.evidence.quote,
    });
    byPath.set(path, file);
  }
  return { files: [...byPath.values()] };
}
