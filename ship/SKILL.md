---
name: ship
description: Merge-and-deploy runbook for open PRs — watch CI, merge in dependency-safe order, run post-merge DB migrations, watch the deploy, smoke-check the deployed app, then clean up stale branches and worktrees. Use when the user runs /ship, or asks to "merge when green", "merge and deploy", "run db push", "clean up branches", or to land a batch of open PRs end to end.
---

# Ship

You are the **orchestrator** for the tail end of the delivery pipeline — everything after `/implement-issues` stops at open PRs. Keep your own context light: cheap `gh`/`git` calls yourself, delegate anything that needs reading code or driving a browser.

## Hard rules

- **CI is the gate.** Never merge a PR whose checks are pending or failing (`gh pr checks <N> --watch`). No exceptions, including "it's just lint".
- **Merge in dependency order.** "Depends on #X" lines in PR bodies come first; among independent PRs, merge same-file-touching PRs one at a time and re-check `mergeable` after each.
- **Confirm before prod side effects.** Database pushes/migrations against production and anything irreversible get one explicit user confirmation per run. Merging the PRs the user named is already consented — don't re-ask per PR.
- **Cleanup deletes only what's merged.** Never delete unmerged branches, never force-push, never drop a stash without showing it and asking.
- **Never claim "verified" without evidence.** If the smoke stage couldn't actually exercise the deployed app, report it as SKIPPED, not passed.

## Workflow

### 1. Preflight
Targets = PR numbers in args; else all open PRs authored by the user (`gh pr list --author @me --json number,title,body,files`). Confirm `gh auth status` and default branch. `git fetch origin` so local state is honest. Build the merge order from PR-body dependency notes + overlapping `files` lists. Present the plan (order + why) in one short block, then proceed.

### 2. CI gate, then merge — one PR at a time
For each PR in order: `gh pr checks <N> --watch`. If failing, diagnose cheaply: stale base (PR predates other merges) → refresh (`git merge origin/<default>` in a temp worktree, push, let CI re-run); genuine failure → **skip this PR and its dependents**, report why, continue with independent siblings. On green: `gh pr merge <N> --merge`. After each merge, re-check the next PR's `mergeable`; if `CONFLICTING`, resolve in a temp worktree (merge `origin/<default>`, fix, run affected tests + typecheck, push, wait for CI) before merging. Remove temp worktrees when done.

### 3. Post-merge migrations
Check merged diffs for schema/migration changes (`gh pr view <N> --json files` — look for the project's schema or migrations paths; infer the actual migrate/push command from the repo's CLAUDE.md or scripts, don't guess from memory). If present: show the user what changed and the exact command, **get confirmation**, run it, report output verbatim. If the command needs credentials you can't find, say where you looked and ask.

### 4. Deploy watch
If merging to the default branch triggers a deploy workflow, watch it (`gh run list --workflow <deploy> --limit 1`, then `gh run watch <id>`). Deploy failed → report the failing job's tail and **stop before smoke** (nothing to verify). No deploy workflow → note it and move on.

### 5. Smoke check (delegated)
Spawn one agent: from the merged PR titles/linked issues, list the user-facing flows that changed, then verify each on the **deployed** app — browser tooling (e.g. Playwright MCP) if available, else HTTP checks on the affected routes + API health endpoint. Read the deployed base URL from the repo's docs/CLAUDE.md; if it's not recorded anywhere, ask once and suggest adding it. Prompt the agent to *Return ONLY: per-flow PASS/FAIL/UNTESTABLE with one line of evidence each (status code, element seen, screenshot path)*. Any FAIL → offer to file a GitHub issue citing the PR that shipped it.

### 6. Cleanup
`git fetch --prune`. Delete local branches fully merged into the default (`git branch --merged origin/<default>`, minus the default itself). Delete their merged remote branches if auto-delete isn't configured. `git worktree prune` and remove leftover `issue-*` worktrees whose PRs merged. List any stashes and ask before dropping. Fast-forward the local default.

### 7. Report
Compact table: PR → CI → merged → deploy → smoke result, then one line each for migrations run and cleanup done. Flag anything skipped or failed, and the exact command to resume (`/ship <remaining PR numbers>`).

## Token discipline
- Never read source diffs yourself — file lists and check states only.
- The smoke agent gets flow names and the base URL, not code.
- Trust structured returns; don't re-verify green checks by other means.

## Commit attribution
Do not add Co-Authored-By or any Claude/Anthropic attribution to merge commits, fix commits, or issues.
