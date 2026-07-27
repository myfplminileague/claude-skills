---
name: implement-issues
description: Orchestrate end-to-end implementation of GitHub issues — dependency-ordered parallel builders (TDD), two adversarial review-and-fix cycles, then one PR per issue. Use when the user runs /implement-issues, or asks to implement/build/ship a set of tracker issues (e.g. "implement #203 #204", "build out these issues and open PRs").
---

# Implement Issues

You are the **orchestrator**. You coordinate subagents and keep your own token use minimal: never read full issue bodies, file contents, or diffs yourself. Fetch only the compact dependency graph, then delegate everything and require short structured returns from every subagent.

## Hard rules

- **Max 4 issues per run.** If more are requested, stop and ask the user to pick ≤4.
- **You** (orchestrator) create one **persistent git worktree + branch per issue** with `git worktree add`, and reuse it across that issue's whole agent chain. Do NOT use the Agent tool's `isolation: "worktree"` — it gives each agent call a separate, ephemeral worktree, but the build/review/fix/PR agents for one issue must all act on the *same* branch.
- Every issue goes through: **build → review cycle 1 → fix → review cycle 2 → fix → PR**, **up to 2 review cycles**. If any review returns `CLEAR TO MERGE`, skip the remaining cycle(s) and go straight to PR.
- **The review stage is the /five-a-side skill.** Do not write your own review prompt — the five roles, their blocking scopes and the repo's rule packs live there, and a hand-rolled reviewer silently bypasses all of it.
- Builders implement with the **/tdd** skill (red-green-refactor). They do not skip tests.
- **Never push or open a PR until both review cycles pass** for that issue.
- **PRs always target the default branch — never another issue's branch.** Build a dependent issue's worktree *on* its dependency's branch (so the code compiles and tests), but open its PR against the default branch with a "merge after #X" note. Stacking a PR onto another open PR's branch gets it **auto-closed** when that branch is deleted at merge (observed failure mode).
- **Worktrees live OUTSIDE the repo** — never inside the working tree (it pollutes it and confuses git). Use a session temp dir; treat `<wt-root>` as the scratchpad path you were given (or `$(git rev-parse --show-toplevel)/../.implement-issues-worktrees` if none), and `<path> = <wt-root>`.
- **A fresh worktree has no `node_modules`, no `.env`, no built packages** — every "run the tests" instruction silently no-ops until it's bootstrapped. Bootstrap each worktree before the builder runs (see step 3).
- **Green-path is not assumed.** A red builder or an unresolved fix does **not** flow into a PR — see *Failure handling*.
- Remove each worktree **and its branch** once its PR is open, and tear both down on any abort.

## Workflow

### 1. Parse & validate
Args are issue numbers (e.g. `203 204 205`). If >4, ask the user to reduce. Confirm prerequisites: `gh auth status` (authed) and a git repo with a default branch (`gh repo view --json nameWithOwner,defaultBranchRef -q .defaultBranchRef.name`). If either fails, stop and report.

**Sync the base to `origin` FIRST — never build on a stale local default.** `git worktree add -b … <default>` resolves `<default>` to the *local* ref, which is often behind `origin` (the user rarely pulls before running this). Building on a stale base means builders work blind to features that already merged upstream — producing duplicated routes/modules, orphaned screens, and avoidable merge conflicts (observed failure mode: built order-confirmation/tracking screens on a base that predated an already-merged order-history+detail page, yielding two order-by-id routes and a dead tracking route). So before creating any worktree: `git fetch origin <default>`, then compare — `git rev-list --count <default>..origin/<default>`. If `origin/<default>` is **ahead**, fast-forward local first (`git fetch origin <default>:<default>` while it's not checked out, or `git -C <main-checkout> pull --ff-only`) and **base every worktree on `origin/<default>`**, not the bare local name. If the local default is checked out and *diverged* (not a clean fast-forward), STOP and report — don't guess.

**Pre-flight overlap scan (cheap, high-value).** Recently-merged work is invisible to the dependency graph (it's not a relation on an open issue). Before building, list what landed lately: `gh pr list --state merged --limit 15 --json number,title,mergedAt,files -q '.[] | "#\(.number) \(.title)"'` (or `--search 'merged:>=<date>'`). If any recent PR's title/area overlaps an issue you're about to build (same feature, screen, route, or module), **tell the builder about it in its prompt** ("note: PR #296 already added an order-history + order-detail page at `/account/orders/[id]` — reuse it, don't duplicate") so it builds *with* the current surface, not a stale mental model. When the overlap looks like it changes the issue's approach, surface it to the user before building.

**Re-run safety (idempotency).** Before touching an issue, check for prior state: `git worktree list`, `git branch --list 'issue-<N>-*'`, and `gh pr list --state open --search 'in:body #<N>'`. If a branch or open PR already exists for that issue, **do not blindly `worktree add -b`** (it errors on an existing branch). Ask the user whether to **skip** (already in flight / done), **resume** (re-attach a worktree to the existing branch with `git worktree add <path>/issue-<N> issue-<N>-<slug>`, no `-b`), or **reset** (`git worktree remove --force` + `git branch -D`, then start clean).

### 2. Build the dependency graph (cheap)
Fetch only relations + labels, not bodies:
```
gh issue view <N> --json number,title,labels
gh api repos/{owner}/{repo}/issues/<N>/timeline --jq '[.[]|select(.event=="cross-referenced" or .event=="connected")]'
```
Read native GitHub links (blocked-by / blocks, "Depends on" linked issues) and dependency labels. Topologically sort into **waves**: issues with no unmet dependency run together; dependents run in a later wave. If a cycle exists, stop and report it. **If the relations are ambiguous or unreadable, ask the user for the dependency order** rather than guessing.

### 3. Per-wave, per-issue pipeline
Process waves **strictly in order — finish an entire wave (every issue through its PR) before starting the next**, so a dependent issue branches off its dependency's final branch. Within a wave, run all issues concurrently: for each, kick off its chain (one Agent call per stage, in a single message across issues). Per issue, advance sequentially — do not start a stage until the previous one returns.

For each issue, **you** first create the worktree + branch (cheap shell, keeps your context light). Create them **one at a time** (the shared `.git` index lock makes concurrent `worktree add` flaky):
```
git worktree add -b issue-<N>-<slug> <path>/issue-<N> <base>
```
`<base>` = **`origin/<default>`** (the freshly-synced remote ref from step 1, NOT the bare local default name — that may be stale), unless this issue depends on earlier-wave issues — then base the worktree on **one** dependency's branch and `git merge` the **other** dependency branches into it (resolving any conflicts), so the worktree has all the code it needs to compile and test. The worktree base only controls *what code is present* — it is **not** the PR target (PRs always target the default branch; see the PR agent). Pass `<path>/issue-<N>` to every agent in the chain; each agent works **only inside that directory** (no `isolation`).

**Bootstrap the worktree before the builder runs.** A fresh worktree is an empty checkout — no installed deps, no `.env`, no built workspace packages, so tests and typecheck will fail spuriously. The builder does this as its **step 0** (see prompt) and must report if bootstrap fails: copy or symlink the repo's git-ignored env files (`.env`, `.env.local`, etc.) from the main checkout, install dependencies, and build any prerequisite workspace packages the tests import. Use whatever the project actually requires — the builder should infer it from the repo (lockfile, workspace config, build scripts). If bootstrap can't be made to pass, **stop that issue here** and report it rather than building blind.

**a. Builder** — `agentType` general-purpose. Prompt template:
> Work inside the worktree at `<path>/issue-<N>` (its branch `issue-<N>-<slug>` is already checked out — do not create branches). **Step 0 — bootstrap:** this is a fresh worktree with no installed deps, no env files, and no built workspace packages. Copy the git-ignored env files (`.env*`) from the main checkout at `<main-repo-path>`, install dependencies, and build any prerequisite workspace packages the tests import — infer the exact commands from the repo (lockfile, workspace config, build/setup scripts). Confirm the test command and typecheck/lint run **before** writing code; if you cannot get a clean baseline, STOP and return the bootstrap error. Then run `gh issue view <N>` to read the full spec and implement using the **/tdd** skill (red-green-refactor, real tests). If the repo has a testing conventions doc (check CLAUDE.md; e.g. `docs/technical/testing.md`), follow its tier-ownership rules; before writing each new test, search the suite for an existing test covering that behavior and extend it rather than duplicating it — write DB/HTTP-tier tests only for what lower tiers can't observe. Before committing, the changed code must pass tests **and** typecheck/lint. Commit on the branch. Do NOT push and do NOT open a PR. Return ONLY: bootstrap ok/failed, files changed (paths), test + typecheck/lint commands with pass/fail, a test tally (tests added/removed, split unit-tier vs DB/HTTP-tier), and a 2-line summary.

**b. Review cycle (run twice).** Each cycle = review agent, then fix agent.

- **Review** — invoke the **/five-a-side** skill; it *is* the review stage. Do not hand-roll a review agent. Pass it:
  - fixed point `origin/<default>`, and the worktree at `<path>/issue-<N>` (already bootstrapped) as the working directory
  - `<N>` as the spec source
  - `<scratch>/issue-<N>/cycle-<1|2>` as its scratch dir
  - `hotfix: true` if the issue carries a `hotfix` label or the PR will target `main` on a repo whose routine work targets `staging` — this makes all five reviewers play regardless of path triggers

  It returns the blocking findings plus one decision line: `CLEAR TO MERGE`, `BLOCKED — n …`, or `INCOMPLETE — <role> did not report`. The full report lands at `<scratch>/issue-<N>/cycle-<n>/five-a-side/report.md` for the PR body.

  A failing typecheck or lint is a blocking finding — five-a-side's `standards` and `prover` roles run them.

- **Fix agent** — same worktree path. Prompt:
  > Work inside the worktree at `<path>/issue-<N>`. Address every finding below, using /tdd for any behavior change (write/adjust the failing test first). Findings:\n<paste review findings>\nCommit fixes. Return ONLY: per-finding resolved/won't-fix+why, and test pass/fail.

  If the review returned `CLEAR TO MERGE`, skip the fix agent **and** the remaining cycle — jump straight to the PR agent.

  **`INCOMPLETE` is not a pass.** If a reviewer did not report, re-run five-a-side for that cycle once. If it comes back `INCOMPLETE` again, stop that issue and record it as FAILED — do **not** open its PR. An unreviewed axis is exactly the gap this stage exists to close, and "the agent went idle" is an observed failure mode, not a hypothetical.

  **Adjudicate won't-fix.** If the fix agent marks any **blocking/high-severity** finding as won't-fix, do not open the PR on autopilot — surface those items to the user and let them decide (accept / push back for another fix attempt / drop the issue). Low-severity won't-fix items can carry through to the PR body and final report.

**c. PR agent** — after the cycles complete (or early on a clean review). Prompt:
> Work inside the worktree at `<path>/issue-<N>`. Push the branch to origin and open a PR with `gh pr create` targeting the **default branch** (never another issue's branch). Title from the issue; body summarizing what changed and linking `Closes #<N>`. If this issue depends on earlier-wave issues, add a top line: "⚠️ Depends on #<dep> (PR #…) — merge those first." Return ONLY the PR URL.

**Always target the default branch.** A dependent PR's worktree already contains its dependencies' commits, so until they merge its diff will also show their changes — that's expected and resolves itself once they merge. Do **not** target a sibling branch to get a cleaner diff: it risks the dependent PR being auto-closed when that branch is deleted on merge.

The review agents only run tests locally — **CI is the real gate** and is still pending when the PR opens. After the PR agent returns the URL, the orchestrator records the check state (`gh pr checks <N>`) for the final report; do not wait on CI here (the skill stops at open PRs).

**d. Cleanup** — once the PR URL is returned, run `git worktree remove <path>/issue-<N>` (the branch is pushed, so it's safe to remove the worktree; keep the branch).

### Failure handling
The pipeline is **not** green-path-only. At any stage that reports failure — bootstrap fails, builder's tests/typecheck won't pass, a fix agent can't resolve a blocking finding or introduces a regression — **retry that one stage once** with the failure detail fed back in. If it still fails: **stop that issue, do not open its PR**, force-remove its worktree and delete its branch (see below), and continue with the wave's other issues (a failed issue blocks only its own dependents, not its independent siblings). Record it as **FAILED** with the reason in the final report. Never paper over a red stage by advancing to the next one.

**Abort teardown.** On any stop/abort for an issue (failure, user interrupt, or error), tear down its state so re-runs are clean: `git worktree remove --force <path>/issue-<N>` then `git branch -D issue-<N>-<slug>`. Leaking the worktree *or* the branch will break the next run's `worktree add -b`.

### 4. Report
Return a compact table to the user: issue # → branch → PR URL → review status → **CI status** (`gh pr checks` snapshot, e.g. `pending`/`passing`/`failing`) → **test delta** (from the builder's tally, e.g. `+5 unit / +2 DB-tier`) → outcome (`PR open` / `FAILED: reason` / `skipped: reason`). Flag any PR whose DB/HTTP-tier test additions look disproportionate to its feature (e.g. validation-matrix cases at the DB tier) — cheap to fix pre-merge, expensive forever after. Remind the user that PRs are open but **CI is the real gate** — don't merge before checks are green. **If there were dependencies, state the explicit merge order** (earlier waves first). Flag any PRs in the same wave that touch the same files — they have no declared dependency but will likely **conflict at merge** and must go one at a time. Note any won't-fix items, FAILED issues, and skipped issues.

### 5. Merge (only if the user asks — the skill stops at open PRs by default)
Do not merge as part of the normal flow. If the user asks to merge:
- Merge in **wave order** — every earlier-wave PR before any dependent one. Use a real merge commit (`gh pr merge <N> --merge`) for dependent/stacked work so the dependencies' shared commits **dedupe** instead of re-conflicting.
- **Wait for CI green** on each PR before merging (`gh pr checks <N> --watch`). The review agents only run tests locally; CI is the real gate (build, full suite, smoke). Don't merge on `UNSTABLE`/failing checks. If a check fails on a stale base (the PR predates other merges), refresh the branch (`git merge origin/<default>`) and let CI re-run before judging it.
- Two parallel same-wave PRs can both touch one file and **conflict at merge** with no declared dependency. After merging the first, re-check the second: if `mergeable=CONFLICTING`, resolve in a fresh worktree (`git worktree add <tmp> <branch>; cd <tmp>; git merge origin/<default>`), fix conflicts, **run the affected tests + typecheck**, push, let CI re-run, then merge. Remove the temp worktree after.
- If a dependent PR was based on a sibling branch and got **auto-closed** when that branch was deleted at merge, reopen the work as a new PR against the default branch (same head branch + commits).

## Token discipline (orchestrator)
- Pass issue **numbers**, not bodies — subagents fetch their own context.
- Demand "Return ONLY ..." short structured outputs; never ask subagents to echo code or diffs.
- Don't re-read files a subagent already reported on. Trust the structured return.
- Fan out a wave's builders in one message (parallel), but keep each issue's review→fix→PR chain sequential.
- Your only direct work is cheap shell (`gh` graph fetch, `git worktree add/remove`) and dispatching agents — never read source or run the build yourself.

## Commit attribution
Do not add Co-Authored-By or any Claude/Anthropic attribution to commits or PRs.
