---
name: implement-issues
description: Orchestrate end-to-end implementation of up to four GitHub issues — dependency-ordered dedicated worktrees, complete spec bundles, TDD, deterministic checks, and one PR per issue. Use for implement-issues (Claude /implement-issues; Codex $implement-issues or by name) or requests to build tracker issues and open PRs.
---

# Implement issues

Coordinate work; keep issue chains isolated and auditable. Deterministic checks establish the delivery
baseline. Five-a-side is an optional manual review available only when the user asks for it.

## Hard rules

- Process at most four issues per run.
- One persistent worktree and branch per issue, outside the repository, reused for build, verification and
  PR creation.
- Base on the freshly fetched remote default branch (or dependency branches when required); PRs still
  target the default branch.
- Bootstrap once; reuse installed dependencies and ignored environment files for the whole chain.
- Use the organisation `tdd` skill during implementation and any user-requested remediation.
- Run deterministic quality checks once before opening the PR.
- Do not invoke five-a-side, remediation or adjudication unless the user explicitly requests it.
- No PR after a red deterministic check.
- A push is a deliberate CI trigger, not a save point — follow the push cadence below.
- No AI-agent attribution on commits or PRs.

## Push cadence

At most two CI-triggering events per PR in the normal case: first push and ready-for-review. A later
user-requested code change may require another deliberate push. Cancelled superseded runs still bill — fewer
pushes is the only saving.

- First push only when the implementation is coherent and local deterministic checks pass. Never push to
  checkpoint work in progress.
- Open the PR as a draft at first push — primary CI skips drafts, so body edits and follow-up commits are
  free until ready.
- Do not push per edit; accumulate commits locally and push in batches.
- Mark ready-for-review exactly once, when implementation and local checks are complete.
- After CI findings, fix every accepted finding locally and push once.

## 1. Preflight

Confirm GitHub authentication, repository/default branch, and issue count. Fetch and base worktrees on
`origin/<default>`; stop on a diverged local default — do not repair a dirty checkout. For each issue, check
existing branches, worktrees, and open PRs; ask whether to skip or resume existing work, and never reset it
without explicit approval. List recently merged PRs and flag overlapping routes, modules, or features before
building.

## 2. Dependency graph and spec bundle

Fetch dependency relations and topologically sort issues into waves; stop on a cycle or ambiguous
dependency. Create one reusable spec bundle per issue: issue title and body, **all comments** in
chronological order, linked decisions/PRDs/designs/acceptance criteria, dependency and recent-overlap notes,
and any explicit hotfix or duty-of-care signal. Pass the bundle path to every downstream stage — a comment
that changed a decision is spec, not optional context.

## 3. Create and bootstrap worktrees

Create worktrees one at a time to avoid shared index locks:

```bash
git worktree add -b issue-<N>-<slug> <worktree-root>/issue-<N> <base>
```

Copy or symlink ignored environment files, install dependencies from the lockfile, and build prerequisite
workspace packages once. Establish a green baseline before changing code. Stop the issue if bootstrap fails.

## 4. Build

Dispatch one builder per issue in the current wave. The builder reads the complete spec bundle and
repository instructions; implements with `/tdd`, extending existing tests where possible; runs the
repository's targeted tests plus lint/typecheck/format checks once; and commits without pushing. It returns
only files changed, checks run with outcomes, test delta by tier, and a short summary.

## 5. Optional manual review

If, and only if, the user explicitly requests it, invoke five-a-side separately against the committed diff.
The report is advisory evidence for that user-requested review; it is not a CI requirement, merge condition
or automatic remediation trigger. Any remediation must be separately requested by the user and is handled as
ordinary implementation work with the normal deterministic checks.

## 6. Open the PR

Push the issue branch once and open one draft PR against the default branch. Include: `Closes #<N>`;
dependency/merge-order notes; deterministic check results and test delta; and, when the user requested a
manual five-a-side review, its report as optional evidence.

Finalize the body while still a draft, then mark ready — the CI snapshot comes from that run and is the
deterministic delivery gate; do not describe queued checks as green.
Remove the worktree after the branch and PR are safely remote.

## Failure handling

Retry a failed bootstrap, builder, or deterministic check once with the exact failure; a second failure
stops that issue — clean up only its dedicated worktree/branch and continue independent issues. A failed
dependency blocks its dependents. Report issue, branch, PR, CI snapshot, test delta, and outcome; state merge
order and likely conflicts.

## Merge

Merge only when the user requests it. Follow dependency order, require current-head CI green, refresh stale
bases, and re-run affected checks after conflict resolution.
