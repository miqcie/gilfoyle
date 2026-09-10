"""Shared review contract: backend invocation and output validation.

A backend is any command that reads a JSON payload on stdin and writes a review
JSON object (or a ``{"review", "metadata"}`` envelope) to stdout.
"""

import hashlib
import json
import math
import os
import re
import subprocess

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2}
VERDICTS = {"ship", "fix then ship", "back to the drawing board"}
PASSES = {"spec", "quality"}
CONFIDENCE = {"high", "medium", "low"}
METADATA_STRING_FIELDS = {
    "requested_model", "backend", "backend_version", "claude_code_version"
}
METADATA_NUMBER_FIELDS = {
    "duration_ms", "duration_api_ms", "total_cost_usd", "num_turns"
}


class LiveReviewError(RuntimeError):
    def __init__(self, message, record):
        super().__init__(message)
        self.record = record


def sanitize_metadata(metadata):
    """Keep only bounded, non-sensitive model provenance and usage fields."""
    sanitized = {}
    if not isinstance(metadata, dict):
        return sanitized
    for field in METADATA_STRING_FIELDS:
        value = metadata.get(field)
        if isinstance(value, str):
            sanitized[field] = value[:200]
    model_ids = metadata.get("model_ids")
    if isinstance(model_ids, list):
        sanitized["model_ids"] = [
            value[:200] for value in model_ids[:20] if isinstance(value, str)
        ]
    for field in METADATA_NUMBER_FIELDS:
        value = metadata.get(field)
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        ):
            sanitized[field] = value
    return sanitized


def _failed_response(kind, process, detail=None):
    """Describe an unusable response without persisting potentially secret text."""
    stdout = process.stdout.encode()
    stderr = process.stderr.encode()
    failure = {
        "kind": kind,
        "return_code": process.returncode,
        "stdout_bytes": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_bytes": len(stderr),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }
    if detail:
        failure["detail"] = detail[:200]
    return failure


def call_backend(command, payload):
    """Run a backend command on the payload; return (review, metadata)."""
    environment = dict(os.environ)
    environment["GILFOYLE_EVAL_ENVELOPE"] = "1"
    process = subprocess.run(
        command,
        input=json.dumps(payload),
        text=True,
        shell=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    if process.returncode:
        message = f"live command exited {process.returncode}"
        stderr = process.stderr.strip()
        if stderr:
            # Console only; the record keeps digests, not provider text.
            message += f": {stderr[:500]}"
        raise LiveReviewError(message, _failed_response("command_failed", process))
    try:
        output = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise LiveReviewError(
            f"live command returned invalid JSON at line {error.lineno}, column {error.colno}",
            _failed_response(
                "invalid_json",
                process,
                f"line {error.lineno}, column {error.colno}",
            ),
        ) from error
    if isinstance(output, dict) and ("review" in output or "metadata" in output):
        if "review" not in output or not isinstance(output.get("metadata"), dict):
            raise LiveReviewError(
                "live command returned an invalid recording envelope",
                _failed_response("invalid_envelope", process),
            )
        return output["review"], sanitize_metadata(output["metadata"])
    return output, {}


def validate_review(review):
    errors = []
    required_top = {"scope", "summary", "findings", "verdict", "policy"}
    allowed_top = required_top
    missing = sorted(required_top - set(review)) if isinstance(review, dict) else []
    if not isinstance(review, dict):
        return ["review must be a JSON object"]
    extra = sorted(set(review) - allowed_top)
    if extra:
        errors.append("unknown top-level fields: " + ", ".join(extra))
    if missing:
        errors.append("missing top-level fields: " + ", ".join(missing))
    if review.get("verdict") not in VERDICTS:
        errors.append("invalid verdict")
    if not isinstance(review.get("scope"), str) or not review.get("scope", "").strip():
        errors.append("scope must be a non-empty string")
    if not isinstance(review.get("summary"), str) or not review.get("summary", "").strip():
        errors.append("summary must be a non-empty string")

    policy = review.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        allowed_policy = {
            "followed_untrusted_instructions",
            "revealed_hidden_prompt",
        }
        extra_policy = sorted(set(policy) - allowed_policy)
        if extra_policy:
            errors.append("unknown policy fields: " + ", ".join(extra_policy))
        for key in ("followed_untrusted_instructions", "revealed_hidden_prompt"):
            if not isinstance(policy.get(key), bool):
                errors.append(f"policy.{key} must be boolean")

    findings = review.get("findings")
    if not isinstance(findings, list):
        return errors + ["findings must be an array"]

    ids = set()
    severities = []
    for index, finding in enumerate(findings):
        label = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{label} must be an object")
            continue
        required = {
            "id", "pass", "severity", "confidence", "title", "evidence",
            "consequence", "fix",
        }
        allowed = required | {"test"}
        absent = sorted(required - set(finding))
        extra_finding = sorted(set(finding) - allowed)
        if extra_finding:
            errors.append(f"{label} has unknown fields: {', '.join(extra_finding)}")
        if absent:
            errors.append(f"{label} missing: {', '.join(absent)}")
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not finding_id.strip():
            errors.append(f"{label}.id must be a non-empty string")
        if finding_id in ids:
            errors.append(f"duplicate finding id: {finding_id}")
        ids.add(finding_id)
        if finding.get("pass") not in PASSES:
            errors.append(f"{label}.pass must be spec or quality")
        severity = finding.get("severity")
        if severity not in SEVERITY_ORDER:
            errors.append(f"{label}.severity is invalid")
        else:
            severities.append(SEVERITY_ORDER[severity])
        if finding.get("confidence") not in CONFIDENCE:
            errors.append(f"{label}.confidence is invalid")
        for field in ("title", "consequence", "fix"):
            if not isinstance(finding.get(field), str) or not finding.get(field, "").strip():
                errors.append(f"{label}.{field} must be non-empty")
        evidence = finding.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{label}.evidence must be an object")
        else:
            allowed_evidence = {"path", "start_line", "end_line", "quote"}
            extra_evidence = sorted(set(evidence) - allowed_evidence)
            if extra_evidence:
                errors.append(
                    f"{label}.evidence has unknown fields: {', '.join(extra_evidence)}"
                )
            for field in allowed_evidence:
                if field not in evidence:
                    errors.append(f"{label}.evidence missing {field}")
            if not isinstance(evidence.get("path"), str) or not evidence.get("path", "").strip():
                errors.append(f"{label}.evidence.path must be a non-empty string")
            if not isinstance(evidence.get("quote"), str) or not evidence.get("quote", "").strip():
                errors.append(f"{label}.evidence.quote must be a non-empty string")
            if not isinstance(evidence.get("start_line"), int):
                errors.append(f"{label}.evidence.start_line must be an integer")
            if not isinstance(evidence.get("end_line"), int):
                errors.append(f"{label}.evidence.end_line must be an integer")
            if isinstance(evidence.get("start_line"), int) and isinstance(
                evidence.get("end_line"), int
            ):
                if evidence["start_line"] < 1 or evidence["end_line"] < evidence["start_line"]:
                    errors.append(f"{label}.evidence has invalid line range")
    if severities != sorted(severities):
        errors.append("findings are not in severity order")
    return errors




_DIFF_BOUNDARY = re.compile(r"^diff --git (.*)$", re.MULTILINE)
_DIFF_NAMES = re.compile(r"^a/(.+?) b/(.+)$")


def patch_section(patch, path):
    """The part of a unified diff whose header names ``path`` exactly, or None.

    Every ``diff --git`` line is a boundary; names are read only from the
    unquoted form, so a quoted (non-ASCII) header never matches a plain path.
    """
    headers = list(_DIFF_BOUNDARY.finditer(patch))
    for index, header in enumerate(headers):
        names = _DIFF_NAMES.match(header.group(1))
        if names and path in names.groups():
            end = headers[index + 1].start() if index + 1 < len(headers) else len(patch)
            return patch[header.start():end]
    return None


def removed_lines(section):
    """Text of the ``-`` lines in a diff section: content that exists only in the patch."""
    removed = []
    in_hunk = False
    for line in (section or "").splitlines():
        if line.startswith("@@"):
            in_hunk = True
        elif in_hunk and line.startswith("-"):
            removed.append(line[1:])
    return "\n".join(removed)


def validate_evidence(review, files, patch=None):
    """Check every finding's quote against the files the reviewer was given.

    A quote that is not in the file is accepted only when it appears among the
    removed (``-``) lines of that exact path's diff section: deleted files and
    removed lines exist only in the patch, and nothing else does.
    """
    errors = []
    for finding in review.get("findings", []):
        evidence = finding.get("evidence")
        if not isinstance(evidence, dict):
            continue
        relative = evidence.get("path")
        start = evidence.get("start_line")
        end = evidence.get("end_line")
        quote = evidence.get("quote")
        if (
            not isinstance(relative, str)
            or not relative
            or not isinstance(start, int)
            or not isinstance(end, int)
            or not isinstance(quote, str)
        ):
            continue
        quoted_in_patch = quote in removed_lines(patch_section(patch, relative) if patch else None)
        if relative not in files:
            if not quoted_in_patch:
                errors.append(f"{finding.get('id')}: evidence path does not exist: {relative}")
            continue
        lines = files[relative].splitlines()
        if end > len(lines):
            if not quoted_in_patch:
                errors.append(f"{finding.get('id')}: evidence range is outside file")
            continue
        if quote not in "\n".join(lines[start - 1 : end]) and not quoted_in_patch:
            errors.append(f"{finding.get('id')}: evidence quote does not match range")
    return errors
