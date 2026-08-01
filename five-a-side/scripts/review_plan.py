#!/usr/bin/env python3
"""Build a deterministic, repo-specific five-a-side review plan.

The pack frontmatter is the single source of truth for path matching, lane,
reviewers, and human-acknowledgement requirements. Both Claude and CI can run
this script instead of maintaining separate risk regular expressions.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROLES = ("standards", "spec", "adversary", "operator", "prover", "steward")
LANE_RANK = {"exempt": 0, "standard": 1, "critical": 2}
LANE_BUDGETS = {
    "exempt": {"mutation_budget": 0, "adjudicator_batches": 0},
    "standard": {"mutation_budget": 3, "adjudicator_batches": 1},
    "critical": {"mutation_budget": 6, "adjudicator_batches": 2},
}


class PlanError(ValueError):
    """Raised when pack policy or CLI input is invalid."""


@dataclass(frozen=True)
class Pack:
    domain: str
    lane: str
    reviewers: tuple[str, ...]
    paths: tuple[str, ...]
    human_ack: tuple[str, ...]
    file: Path


def _inline_list(value: str, *, field: str, file: Path) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PlanError(f"{file}: {field} must be a JSON-compatible inline list") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) and item for item in parsed):
        raise PlanError(f"{file}: {field} must be a list of non-empty strings")
    return parsed


def parse_pack(file: Path) -> Pack:
    text = file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise PlanError(f"{file}: missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise PlanError(f"{file}: missing closing frontmatter delimiter") from exc

    scalar: dict[str, str] = {}
    paths: list[str] = []
    active_list: str | None = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("  - "):
            if active_list != "paths":
                raise PlanError(f"{file}: list item outside paths")
            item = stripped[2:].strip().strip('"').strip("'")
            if not item:
                raise PlanError(f"{file}: empty path glob")
            paths.append(item)
            continue
        if ":" not in stripped:
            raise PlanError(f"{file}: invalid frontmatter line: {raw}")
        key, value = stripped.split(":", 1)
        key, value = key.strip(), value.strip()
        active_list = key if not value else None
        if value:
            scalar[key] = value.strip('"').strip("'")

    required = {"domain", "lane", "reviewers"}
    missing = sorted(required - scalar.keys())
    if missing:
        raise PlanError(f"{file}: missing {', '.join(missing)}")
    if scalar["domain"] != file.stem:
        raise PlanError(f"{file}: domain must match filename stem {file.stem!r}")
    lane = scalar["lane"]
    if lane not in {"standard", "critical"}:
        raise PlanError(f"{file}: lane must be standard or critical")
    reviewers = _inline_list(scalar["reviewers"], field="reviewers", file=file)
    unknown = sorted(set(reviewers) - set(ROLES))
    if unknown:
        raise PlanError(f"{file}: unknown reviewers: {', '.join(unknown)}")
    if not reviewers:
        raise PlanError(f"{file}: reviewers cannot be empty")
    sections = set(
        re.findall(
            r"^## (standards|spec|adversary|operator|prover|steward)\s*$",
            text,
            re.MULTILINE,
        )
    )
    missing_sections = sorted(set(reviewers) - sections)
    extra_sections = sorted(sections - set(reviewers))
    if missing_sections:
        raise PlanError(f"{file}: reviewers without sections: {', '.join(missing_sections)}")
    if extra_sections:
        raise PlanError(f"{file}: role sections absent from reviewers: {', '.join(extra_sections)}")
    if not paths:
        raise PlanError(f"{file}: paths cannot be empty")
    human_ack = _inline_list(scalar.get("human_ack", "[]"), field="human_ack", file=file)
    return Pack(
        domain=scalar["domain"],
        lane=lane,
        reviewers=tuple(reviewers),
        paths=tuple(paths),
        human_ack=tuple(human_ack),
        file=file,
    )


def load_packs(directory: Path) -> list[Pack]:
    if not directory.is_dir():
        raise PlanError(f"packs directory does not exist: {directory}")
    files = sorted(directory.glob("*.md"))
    if not files:
        raise PlanError(f"packs directory contains no .md files: {directory}")
    packs = [parse_pack(file) for file in files]
    domains = [pack.domain for pack in packs]
    if len(domains) != len(set(domains)):
        raise PlanError("pack domains must be unique")
    return packs


def _matches(path: str, pattern: str) -> bool:
    candidates = {pattern}
    # Treat **/ as zero-or-more directories. fnmatch alone requires at least one.
    pending = [pattern]
    while pending:
        candidate = pending.pop()
        if "**/" not in candidate:
            continue
        collapsed = candidate.replace("**/", "", 1)
        if collapsed not in candidates:
            candidates.add(collapsed)
            pending.append(collapsed)
    return any(fnmatch.fnmatchcase(path, candidate) for candidate in candidates)


def build_plan(packs: list[Pack], paths: list[str], signals: list[str]) -> dict[str, Any]:
    clean_paths: list[str] = []
    for raw_path in paths:
        path = raw_path.strip()
        if not path:
            continue
        while path.startswith("./"):
            path = path[2:]
        clean_paths.append(path)
    clean_paths = sorted(set(clean_paths))
    matched = [pack for pack in packs if any(_matches(path, glob) for path in clean_paths for glob in pack.paths)]
    matched_paths = sorted(
        {path for path in clean_paths if any(_matches(path, glob) for pack in matched for glob in pack.paths)}
    )

    lane = "exempt"
    reviewers: set[str] = set()
    human_ack: set[str] = set()
    for pack in matched:
        if LANE_RANK[pack.lane] > LANE_RANK[lane]:
            lane = pack.lane
        reviewers.update(pack.reviewers)
        human_ack.update(pack.human_ack)

    unknown_signals = sorted(set(signals) - {"hotfix", "duty-of-care", "full"})
    if unknown_signals:
        raise PlanError(f"unknown signals: {', '.join(unknown_signals)}")

    if "full" in signals:
        lane = "critical"
        reviewers.update(ROLES)
    if matched and "hotfix" in signals:
        lane = "critical"
        reviewers.update(ROLES)
        human_ack.add("risk-path hotfix")
    if matched and "duty-of-care" in signals:
        lane = max((lane, "standard"), key=LANE_RANK.get)
        reviewers.add("steward")

    ordered_reviewers = [role for role in ROLES if role in reviewers]
    return {
        "version": 1,
        "lane": lane,
        "depth": "deep" if lane == "critical" else lane,
        "paths": clean_paths,
        "matched_paths": matched_paths,
        "matched_packs": [pack.domain for pack in matched],
        "reviewers": ordered_reviewers,
        "human_ack": sorted(human_ack),
        "signals": sorted(set(signals)),
        **LANE_BUDGETS[lane],
    }


def git_paths(base: str, head: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise PlanError(completed.stderr.strip() or "git diff failed")
    return completed.stdout.splitlines()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packs-dir", type=Path, required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--paths-file", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--signal", action="append", default=[])
    parser.add_argument("--validate", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        packs = load_packs(args.packs_dir)
        if args.validate:
            print(json.dumps({"valid": True, "packs": [pack.domain for pack in packs]}, indent=2))
            return 0

        paths = list(args.path)
        if args.paths_file:
            paths.extend(args.paths_file.read_text(encoding="utf-8").splitlines())
        if args.base:
            paths.extend(git_paths(args.base, args.head))
        if not paths:
            raise PlanError("provide --path, --paths-file, or --base")
        print(json.dumps(build_plan(packs, paths, args.signal), indent=2, sort_keys=True))
        return 0
    except (OSError, PlanError) as exc:
        print(f"review-plan: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
