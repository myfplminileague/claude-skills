#!/usr/bin/env python3
"""Enforce a recorded five-a-side decision for a deterministic review plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DECISION_RE = re.compile(
    r"^\s*(?:\*\*)?(CLEAR TO MERGE|BLOCKED|INCOMPLETE)(?:\s*(?:—|–|-{1,2}|:)?\s*.*)?(?:\*\*)?\s*$",
    re.MULTILINE,
)
OVERRIDE_RE = re.compile(r"^\s*(?:\*\*)?OVERRIDE REASON\s*:\s*\S.+$", re.MULTILINE)
BOT_RE = re.compile(r"(?:bot|\[bot\]|dependabot|release-please)", re.IGNORECASE)


class GateError(ValueError):
    """Raised for invalid plan input."""


def read_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read review plan {path}: {exc}") from exc
    if plan.get("lane") not in {"exempt", "standard", "critical"}:
        raise GateError("review plan has no valid lane")
    for key in ("matched_paths", "human_ack"):
        if not isinstance(plan.get(key), list):
            raise GateError(f"review plan field {key!r} must be a list")
    return plan


def labels(value: str) -> set[str]:
    return {label.strip() for label in value.split(",") if label.strip()}


def decision(body: str) -> str | None:
    match = DECISION_RE.search(body)
    return match.group(1) if match else None


def evaluate(
    plan: dict[str, Any],
    *,
    event: str,
    base: str,
    head_ref: str,
    actor: str,
    label_text: str,
    body: str,
    merged_pr: str,
) -> tuple[bool, str]:
    if base == "main" and head_ref == "staging":
        return (
            True,
            "Promotion staging -> main: exempt; its commits were reviewed before promotion.",
        )
    if BOT_RE.search(actor):
        return (
            True,
            f"Automated PR by {actor}: exempt; dedicated dependency and secret checks still apply.",
        )

    applied_labels = labels(label_text)
    if "review:override" in applied_labels:
        if not OVERRIDE_RE.search(body):
            return (
                False,
                "The review:override label needs a reason in an OVERRIDE REASON: line in the PR body.",
            )
        return True, "Review overridden deliberately with a recorded reason."

    lane = plan["lane"]
    if lane == "exempt":
        return (
            True,
            "No review-pack paths matched - no five-a-side model review is required.",
        )

    path_lines = "\n".join(str(path) for path in plan["matched_paths"])
    if event == "push":
        if merged_pr:
            return (
                True,
                f"Arrived on {base} via pull request #{merged_pr}; the PR gate already judged it.",
            )
        return False, (
            f"Direct push to {base} touched {lane}-lane paths without a pull request:\n{path_lines}\n"
            "Run /five-a-side over the pushed range and record the result retrospectively."
        )

    verdict = decision(body)
    if "reviewed:five-a-side" not in applied_labels or verdict is None:
        return False, (
            f"This change requires a {lane} five-a-side review and has no recorded five-a-side review decision:\n{path_lines}\n"
            "Run /five-a-side, add its report to the PR body, and add the reviewed:five-a-side label. "
            "For a deliberate bypass, add review:override and an OVERRIDE REASON: line."
        )
    if verdict == "INCOMPLETE":
        return (
            False,
            "Review was INCOMPLETE. Re-run the missing reviewer before merging.",
        )
    if verdict == "BLOCKED":
        return (
            False,
            "Review is BLOCKED. Resolve blocking findings or record a deliberate override.",
        )
    if plan["human_ack"] and "human-ack:confirmed" not in applied_labels:
        reasons = "; ".join(str(reason) for reason in plan["human_ack"])
        return (
            False,
            f"Human acknowledgement is required for: {reasons}. Add human-ack:confirmed after reading the change.",
        )
    return True, f"Recorded {lane} five-a-side review is clear."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-file", type=Path, required=True)
    parser.add_argument("--event", default="pull_request")
    parser.add_argument("--base", default="main")
    parser.add_argument("--head-ref", default="")
    parser.add_argument("--actor", default="")
    parser.add_argument("--labels", default="")
    parser.add_argument("--body", default="")
    parser.add_argument("--merged-pr", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = read_plan(args.plan_file)
        passed, message = evaluate(
            plan,
            event=args.event,
            base=args.base,
            head_ref=args.head_ref,
            actor=args.actor,
            label_text=args.labels,
            body=args.body,
            merged_pr=args.merged_pr,
        )
    except GateError as exc:
        print(f"review-gate: {exc}", file=sys.stderr)
        return 2
    if passed:
        print(message)
        return 0
    print(f"::error::{message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
