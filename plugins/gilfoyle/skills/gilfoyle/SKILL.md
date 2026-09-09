---
name: gilfoyle
description: Review code and designs with evidence and dry wit.
argument-hint: <target>
---

Dispatch the `gilfoyle:gilfoyle-tech-reviewer` agent to review: $ARGUMENTS

If no target is supplied, review the current diff. Require the agent to inspect surrounding context and run relevant checks. Do not authorize mutations or external comments unless the user explicitly requested them.
