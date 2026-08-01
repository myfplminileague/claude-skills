from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Dataclasses resolve annotations through sys.modules while the module loads.
    import sys

    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


plan = load_module("review_plan", ROOT / "five-a-side/scripts/review_plan.py")
state = load_module("review_state", ROOT / "five-a-side/scripts/review_state.py")
gate = load_module("review_gate", ROOT / "five-a-side/scripts/review_gate.py")


def write_pack(
    directory: Path,
    name: str,
    *,
    lane: str,
    reviewers: list[str],
    paths: list[str],
    ack=None,
):
    lines = [
        "---",
        f"domain: {name}",
        f"lane: {lane}",
        f"reviewers: {json.dumps(reviewers)}",
        f"human_ack: {json.dumps(ack or [])}",
        "paths:",
        *[f'  - "{path}"' for path in paths],
        "---",
        f"# {name}",
        *[f"\n## {reviewer}\n- Test rule." for reviewer in reviewers],
    ]
    (directory / f"{name}.md").write_text("\n".join(lines) + "\n")


class ReviewPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.packs = Path(self.temp.name)
        write_pack(
            self.packs,
            "ui",
            lane="standard",
            reviewers=["standards", "spec", "prover"],
            paths=["src/app/**/*.tsx"],
        )
        write_pack(
            self.packs,
            "consent",
            lane="critical",
            reviewers=["adversary", "operator", "steward"],
            paths=["src/app/api/**", "src/lib/consent*"],
            ack=["consent or personal-data handling"],
        )
        write_pack(
            self.packs,
            "automation",
            lane="critical",
            reviewers=["operator"],
            paths=[".github/workflows/**"],
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_no_match_is_exempt(self):
        result = plan.build_plan(plan.load_packs(self.packs), ["README.md"], [])
        self.assertEqual(result["lane"], "exempt")
        self.assertEqual(result["reviewers"], [])
        self.assertEqual(result["matched_paths"], [])
        self.assertEqual(result["mutation_budget"], 0)

    def test_double_star_matches_zero_or_more_directories(self):
        result = plan.build_plan(plan.load_packs(self.packs), ["src/app/page.tsx"], [])
        self.assertEqual(result["lane"], "standard")
        self.assertEqual(result["matched_packs"], ["ui"])

    def test_dot_prefixed_path_is_not_stripped(self):
        result = plan.build_plan(
            plan.load_packs(self.packs), ["./.github/workflows/review.yml"], []
        )
        self.assertEqual(result["lane"], "critical")
        self.assertEqual(result["matched_packs"], ["automation"])
        self.assertEqual(result["matched_paths"], [".github/workflows/review.yml"])

    def test_overlapping_packs_union_roles_and_raise_lane(self):
        result = plan.build_plan(
            plan.load_packs(self.packs),
            ["src/app/settings/page.tsx", "src/app/api/profile/route.ts"],
            [],
        )
        self.assertEqual(result["lane"], "critical")
        self.assertEqual(
            result["reviewers"],
            ["standards", "spec", "adversary", "operator", "prover", "steward"],
        )
        self.assertEqual(result["adjudicator_batches"], 2)
        self.assertEqual(result["human_ack"], ["consent or personal-data handling"])
        self.assertEqual(
            result["matched_paths"],
            ["src/app/api/profile/route.ts", "src/app/settings/page.tsx"],
        )

    def test_hotfix_without_risk_match_remains_exempt(self):
        result = plan.build_plan(plan.load_packs(self.packs), ["README.md"], ["hotfix"])
        self.assertEqual(result["lane"], "exempt")

    def test_hotfix_with_match_plays_every_role(self):
        result = plan.build_plan(
            plan.load_packs(self.packs), ["src/app/page.tsx"], ["hotfix"]
        )
        self.assertEqual(result["lane"], "critical")
        self.assertEqual(result["reviewers"], list(plan.ROLES))

    def test_full_is_explicit_even_without_a_pack(self):
        result = plan.build_plan(plan.load_packs(self.packs), ["README.md"], ["full"])
        self.assertEqual(result["lane"], "critical")
        self.assertEqual(result["reviewers"], list(plan.ROLES))

    def test_invalid_role_fails_validation(self):
        write_pack(
            self.packs,
            "broken",
            lane="standard",
            reviewers=["goalkeeper"],
            paths=["broken/**"],
        )
        with self.assertRaisesRegex(plan.PlanError, "unknown reviewers"):
            plan.load_packs(self.packs)


class ReviewGateTests(unittest.TestCase):
    def plan(self, *, lane="standard", ack=None):
        return {
            "lane": lane,
            "matched_paths": []
            if lane == "exempt"
            else ["src/app/api/profile/route.ts"],
            "human_ack": ack or [],
        }

    def evaluate(self, plan_value=None, **overrides):
        values = {
            "event": "pull_request",
            "base": "staging",
            "head_ref": "feature/profile",
            "actor": "developer",
            "label_text": "",
            "body": "",
            "merged_pr": "",
        }
        values.update(overrides)
        return gate.evaluate(plan_value or self.plan(), **values)

    def test_exempt_plan_needs_no_review(self):
        passed, message = self.evaluate(self.plan(lane="exempt"))
        self.assertTrue(passed)
        self.assertIn("no five-a-side", message)

    def test_clear_recorded_review_passes(self):
        passed, _ = self.evaluate(
            label_text="reviewed:five-a-side",
            body="## Decision\nCLEAR TO MERGE",
        )
        self.assertTrue(passed)

    def test_blocked_verdict_cannot_hide_in_separator_variants(self):
        for line in (
            "BLOCKED — 2 findings",
            "BLOCKED - 2 findings",
            "**BLOCKED: 2 findings**",
        ):
            with self.subTest(line=line):
                passed, message = self.evaluate(
                    label_text="reviewed:five-a-side", body=f"## Decision\n{line}"
                )
                self.assertFalse(passed)
                self.assertIn("BLOCKED", message)

    def test_prose_is_not_a_verdict(self):
        passed, _ = self.evaluate(
            label_text="reviewed:five-a-side",
            body="## Decision\nCLEAR TO MERGE\n\n- A genuinely BLOCKED report must fail.",
        )
        self.assertTrue(passed)

    def test_human_ack_comes_from_plan(self):
        ack_plan = self.plan(ack=["published legal policy"])
        passed, message = self.evaluate(
            ack_plan,
            label_text="reviewed:five-a-side",
            body="CLEAR TO MERGE",
        )
        self.assertFalse(passed)
        self.assertIn("published legal policy", message)
        passed, _ = self.evaluate(
            ack_plan,
            label_text="reviewed:five-a-side,human-ack:confirmed",
            body="CLEAR TO MERGE",
        )
        self.assertTrue(passed)

    def test_override_is_never_silent(self):
        passed, _ = self.evaluate(label_text="review:override", body="lgtm")
        self.assertFalse(passed)
        passed, _ = self.evaluate(
            label_text="review:override", body="OVERRIDE REASON: emergency rollback"
        )
        self.assertTrue(passed)

    def test_push_from_merged_pr_is_not_a_direct_push(self):
        passed, message = self.evaluate(event="push", base="main", merged_pr="42")
        self.assertTrue(passed)
        self.assertIn("#42", message)


class ReviewStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.plan_file = root / "plan.json"
        self.state_file = root / "state.json"
        self.plan_file.write_text(
            json.dumps({"lane": "standard", "reviewers": ["spec"]})
        )
        state.init_state(self.plan_file, self.state_file)

    def tearDown(self):
        self.temp.cleanup()

    def test_only_one_automated_remediation_is_authorized(self):
        state.authorize_remediation(self.state_file)
        with self.assertRaisesRegex(state.StateError, "budget exhausted"):
            state.authorize_remediation(self.state_file)
        saved = state.read_json(self.state_file)
        self.assertEqual(saved["automated_remediations"], 1)

    def test_metrics_accumulate(self):
        args = type(
            "Args",
            (),
            {
                "stage": "review",
                "decision": "BLOCKED",
                "agent_calls": 4,
                "duration_seconds": 12.5,
                "blocks": 2,
                "notes": 1,
                "refuted": 1,
                "mutations": 3,
            },
        )()
        state.record_event(self.state_file, args)
        saved = state.read_json(self.state_file)
        self.assertEqual(saved["totals"]["agent_calls"], 4)
        self.assertEqual(saved["totals"]["mutations"], 3)


class SkillShapeTests(unittest.TestCase):
    def test_skill_is_progressively_disclosed(self):
        words = (ROOT / "five-a-side/SKILL.md").read_text().split()
        self.assertLess(len(words), 5000)

    def test_skill_frontmatter_is_minimal(self):
        lines = (ROOT / "five-a-side/SKILL.md").read_text().splitlines()
        end = lines.index("---", 1)
        keys = {line.split(":", 1)[0] for line in lines[1:end] if ":" in line}
        self.assertEqual(keys, {"name", "description"})


if __name__ == "__main__":
    unittest.main()
