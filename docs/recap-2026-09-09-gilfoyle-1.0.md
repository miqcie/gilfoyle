# Gilfoyle 1.0 session recap

Date: 2026-09-09
Status: Shipped in PR #5

## Outcome

Gilfoyle moved from a Claude-only prompt into an evaluated reviewer distributed as both a Claude Code plugin and a native Hermes skill. The review method now separates specification compliance from implementation quality and requires evidence, confidence, consequence, a fix, and relevant regression coverage for every finding.

## Quality model

The dependency-free evaluation harness covers a clean change, specification drift, SQL injection, quadratic request-path work, and prompt injection embedded in repository content. Replay candidates prove the harness and fixture oracles agree; optional live adapters measure actual models without coupling the suite to a provider.

The voice remains intentionally sardonic. The governing rule is: every insult needs evidence, every finding needs a fix, and every joke should make the technical point harder to forget. The artifact gets roasted; the engineer gets protected.

## Distribution

- Claude Code marketplace: `miqcie/gilfoyle`, plugin `gilfoyle@gilfoyle`
- Claude invocation: `/gilfoyle:gilfoyle <target>`
- Hermes source: `skills/gilfoyle/SKILL.md`
- Hermes installation: direct raw GitHub `SKILL.md` URL documented in README

## Diffs and Trees decision

`@pierre/diffs` and `@pierre/trees` would help a future visual review workbench, not reviewer reasoning. They remain outside the core runtime. Issue #7 captures a bounded prototype using the existing UI-neutral review JSON contract.

## Verification

- 17 unit and contract tests passed before merge.
- Five of five replay evaluation cases passed.
- Claude plugin strict validation passed.
- Independent Gilfoyle review returned `ship` after two fix cycles.
- Pull-request and post-merge GitHub Actions passed.
- Claude marketplace/plugin and Hermes URL installations were verified after merge.

## Follow-ups

- #6: run and record the live Fable evaluation after the provider session limit resets.
- #7: prototype a Diffs/Trees review workbench.
- #8: replace the stale `SESSION_SUMMARY.md` with an accurate history note.
