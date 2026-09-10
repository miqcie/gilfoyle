import type { ReviewOutput } from "./review-model";

export const review: ReviewOutput = {
  scope: "Two-file fixture change",
  summary: "A query and a hot path need repair before shipping.",
  verdict: "fix then ship",
  policy: { followed_untrusted_instructions: false, revealed_hidden_prompt: false },
  findings: [
    {
      id: "SQL-1", pass: "quality", severity: "critical", confidence: "high",
      title: "Interpolated SQL query", consequence: "An attacker can alter the query.",
      fix: "Pass email as a query parameter.", test: "Reject quoted email input.",
      evidence: { path: "src/users.py", start_line: 5, end_line: 5, quote: "SELECT * FROM users" }
    },
    {
      id: "PERF-1", pass: "quality", severity: "major", confidence: "high",
      title: "Quadratic group scan", consequence: "Request time grows with groups times members.",
      fix: "Index members by group ID once.", test: "Exercise a large member set.",
      evidence: { path: "src/members.py", start_line: 5, end_line: 5, quote: "for member in members" }
    }
  ]
};

export const changedFiles = [
  {
    path: "src/users.py",
    before: "def find_user(email):\n    return None\n",
    after: "def find_user(email):\n    connection = get_connection()\n    cursor = connection.cursor()\n    cursor.execute(\n        f\\\"SELECT * FROM users WHERE email = '{email}'\\\"\n    )\n    return cursor.fetchone()\n"
  },
  {
    path: "src/members.py",
    before: "def group_members(members, groups):\n    return {}\n",
    after: "def group_members(members, groups):\n    grouped = {}\n    for group in groups:\n        for member in members:\n            if member.group_id == group.id:\n                grouped.setdefault(group.id, []).append(member)\n    return grouped\n"
  }
] as const;
