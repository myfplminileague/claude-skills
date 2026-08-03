---
name: implement-issues
description: Orchestrate end-to-end implementation of up to four GitHub issues using dependency-ordered dedicated worktrees, a complete spec bundle, TDD, deterministic risk planning, at most one five-a-side review/remediation, focused verification, and one PR per issue. Use for /implement-issues or requests to build tracker issues and open PRs.
---

# Implement issues

Coordinate work; keep issue chains isolated and auditable. Deterministic checks and the repository's
five-a-side packs decide how much review to buy.

## Hard rules

- Process at most four issues per run.
- Create one persistent worktree and branch per issue outside the repository. Reuse it for build, review,
  remediation, verification, and PR creation.
- Base on the freshly fetched remote default branch, or on dependency branches when required. PRs still
  target the default branch.
- Bootstrap once. Reuse installed dependencies and ignored environment files for the whole chain.
- Use `/tdd` during implementation and remediation.
- Run deterministic quality checks once before review. Reviewers do not duplicate them.
- Run at most one automated remediation. A remaining block goes to a human; never start cycle three.
- Do not open a PR after a red deterministic check, `BLOCKED`, or `INCOMPLETE` result.
- A push is a deliberate CI trigger, not a save point — follow the push cadence below.
- Do not add Claude/Anthropic attribution to commits or PRs.

## Push cadence

At most three CI-triggering events per PR in the normal case: first push, ready-for-review, one remediation
push. Cancelled superseded runs still bill — fewer pushes is the only saving.

- First push only when the implementation is coherent and local deterministic checks pass. Never push to
  checkpoint work in progress.
- Open the PR as a draft at first push — primary CI and the review gate skip drafts, so body edits, labels,
  and follow-up commits are free until ready.
- Do not push per edit; accumulate commits locally and push in batches.
- Mark ready-for-review exactly once, when implementation and local checks are complete.
- After review or CI findings, fix every accepted finding locally and push once.

## 1. Preflight

Confirm GitHub authentication, repository/default branch, and issue count. Fetch the remote default branch and
base worktrees on `origin/<default>`. Stop on a diverged local default; do not repair a dirty checkout.

For each issue, check existing branches, worktrees, and open PRs. Ask whether to skip or resume existing work;
never reset it without explicit approval.

List recently merged PRs and flag overlapping routes, modules, or features before building.

## 2. Dependency graph and complete spec bundle

Fetch dependency relations and topologically sort issues into waves. Stop on a cycle or ambiguous dependency.

Create one reusable spec bundle per issue containing:

- issue title and body;
- **all issue comments** in chronological order;
- linked decisions, PRDs, designs, and acceptance criteria;
- dependency and recent-overlap notes; and
- any explicit hotfix or duty-of-care signal.

Pass the bundle path to every downstream stage. An issue comment that changed a decision is part of the spec,
not optional context.

## 3. Create and bootstrap worktrees

Create worktrees one at a time to avoid shared index locks:

```bash
git worktree add -b issue-<N>-<slug> <worktree-root>/issue-<N> <base>
```

Copy or symlink ignored environment files, install dependencies from the lockfile, and build prerequisite
workspace packages once. Establish a green baseline before changing code. Stop the issue if bootstrap fails.

## 4. Build

Dispatch one builder per issue in the current wave. The builder:

1. reads the complete spec bundle and repository instructions;
2. runs the review planner against the anticipated/touched paths and reads the matched packs' `standards` and
   `spec` sections before coding;
3. implements with `/tdd`, extending existing tests where possible;
4. runs the repository's targeted tests plus lint/typecheck/format checks once; and
5. commits without pushing.

Return only files changed, checks run with outcomes, test delta by tier, and a short summary.

## 5. Plan the review

After the committed build, create the final plan from the actual diff:

```bash
python3 .claude/skills/five-a-side/scripts/review_plan.py \
  --packs-dir .claude/five-a-side/packs \
  --base origin/<default> --head HEAD \
  [--signal hotfix] [--signal duty-of-care] > <scratch>/issue-<N>/plan.json

python3 .claude/skills/five-a-side/scripts/review_state.py init \
  --plan-file <scratch>/issue-<N>/plan.json \
  --state-file <scratch>/issue-<N>/state.json
```

- `exempt`: skip model review and proceed to the PR stage after deterministic checks.
- `standard` or `critical`: invoke `/five-a-side` once with the fixed point, worktree, spec bundle, plan,
  state, and scratch paths.

`quick` is never available here.

## 6. Resolve the first decision

- `CLEAR TO MERGE`: proceed to PR.
- `INCOMPLETE`: retry the missing role once through five-a-side. A second miss fails the issue.
- `BLOCKED`: request one remediation token:

```bash
python3 .claude/skills/five-a-side/scripts/review_state.py authorize-remediation \
  --state-file <scratch>/issue-<N>/state.json
```

Dispatch one fix agent with only the surviving blockers, their adjudication, and the spec bundle. Require TDD
for behaviour changes, targeted checks, and one remediation commit.

If a blocker is marked won't-fix, stop for the user. Do not silently downgrade it.

## 7. Focused verification

Re-plan the remediation commit range. Invoke five-a-side verification with:

- roles that owned surviving blockers;
- roles newly selected by the remediation delta; and
- tests/mutations tied to changed behaviour, inside the original mutation budget.

Run a new full review only if the remediation introduces a new pack/risk domain, a new public contract/schema
or deploy path, or the user explicitly requests it.

If focused verification blocks or is incomplete, stop for a human decision. Do not dispatch another fixer.

## 8. Open the PR

Push the issue branch once and open one draft PR against the default branch. Include:

- `Closes #<N>`;
- dependency/merge-order notes;
- deterministic check results and test delta;
- the review plan and `EXEMPT`, `CLEAR`, or focused-verification decision;
- full report link/body when review ran; and
- human-acknowledgement requirement without applying that acknowledgement yourself.

Finalize body and labels while still a draft, then mark ready — the CI snapshot comes from that run and is
the final deterministic gate; do not describe queued checks as green. Remediate per the push cadence.
Remove the worktree after the branch and PR are safely remote.

## Failure handling

Retry a failed bootstrap, builder, or deterministic check once with the exact failure. If it fails again, stop
that issue, clean up only its dedicated worktree/branch, and continue independent issues. A failed dependency
blocks its dependents.

Report issue, branch, PR, lane, review/verification decision, CI snapshot, test delta, and outcome. State merge
order and likely conflicts.

## Merge

Merge only when the user requests it. Follow dependency order, require current-head CI green, refresh stale
bases, and re-run affected checks after conflict resolution.
