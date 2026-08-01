#!/usr/bin/env python3
"""Record review metrics and enforce one automated remediation per run."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class StateError(ValueError):
    """Raised when review state cannot advance safely."""


def now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StateError(f"{path} must contain a JSON object")
    return value


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def init_state(plan_file: Path, state_file: Path) -> None:
    if state_file.exists():
        raise StateError(f"state already exists: {state_file}")
    plan = read_json(plan_file)
    if plan.get("lane") not in {"exempt", "standard", "critical"}:
        raise StateError("plan has no valid lane")
    write_atomic(
        state_file,
        {
            "version": 1,
            "created_at": now(),
            "plan": plan,
            "automated_remediations": 0,
            "events": [],
            "totals": {
                "agent_calls": 0,
                "duration_seconds": 0.0,
                "blocks": 0,
                "notes": 0,
                "refuted": 0,
                "mutations": 0,
            },
        },
    )


def authorize_remediation(state_file: Path) -> None:
    state = read_json(state_file)
    count = int(state.get("automated_remediations", 0))
    if count >= 1:
        raise StateError("automated remediation budget exhausted; hand the remaining block to a human")
    state["automated_remediations"] = count + 1
    state.setdefault("events", []).append({"stage": "remediation-authorized", "at": now()})
    write_atomic(state_file, state)


def record_event(state_file: Path, args: argparse.Namespace) -> None:
    state = read_json(state_file)
    metrics = {
        "agent_calls": args.agent_calls,
        "duration_seconds": args.duration_seconds,
        "blocks": args.blocks,
        "notes": args.notes,
        "refuted": args.refuted,
        "mutations": args.mutations,
    }
    if any(value < 0 for value in metrics.values()):
        raise StateError("metrics cannot be negative")
    event = {"stage": args.stage, "at": now(), "decision": args.decision, **metrics}
    state.setdefault("events", []).append(event)
    totals = state.setdefault("totals", {})
    for key, value in metrics.items():
        totals[key] = totals.get(key, 0) + value
    write_atomic(state_file, state)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--plan-file", type=Path, required=True)
    init.add_argument("--state-file", type=Path, required=True)

    authorize = commands.add_parser("authorize-remediation")
    authorize.add_argument("--state-file", type=Path, required=True)

    record = commands.add_parser("record")
    record.add_argument("--state-file", type=Path, required=True)
    record.add_argument(
        "--stage",
        choices=["review", "adjudication", "remediation", "verification"],
        required=True,
    )
    record.add_argument("--decision", required=True)
    record.add_argument("--agent-calls", type=int, default=0)
    record.add_argument("--duration-seconds", type=float, default=0)
    record.add_argument("--blocks", type=int, default=0)
    record.add_argument("--notes", type=int, default=0)
    record.add_argument("--refuted", type=int, default=0)
    record.add_argument("--mutations", type=int, default=0)

    summary = commands.add_parser("summary")
    summary.add_argument("--state-file", type=Path, required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            init_state(args.plan_file, args.state_file)
        elif args.command == "authorize-remediation":
            authorize_remediation(args.state_file)
        elif args.command == "record":
            record_event(args.state_file, args)
        else:
            print(json.dumps(read_json(args.state_file), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, StateError) as exc:
        print(f"review-state: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
