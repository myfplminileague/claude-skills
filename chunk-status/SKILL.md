---
name: chunk-status
description: Reconcile a project-plan chunk against reality — map each plan item to its GitHub issues, merged PRs, and (optionally) the deployed app, report shipped/in-flight/missing per item, and propose exact plan-doc corrections for stale statuses. Use when the user runs /chunk-status, asks "what's the status of chunk N", "what got implemented", "is everything built/deployed", or wants the project plan's statuses fixed.
---

# Chunk Status

You produce a trustworthy answer to: *for chunk N, what is actually shipped, what is in flight, what is missing, and where does the plan doc lie?* Three sources of truth, reconciled: the plan doc, GitHub (issues + merged PRs), and — only when asked — the deployed app.

## Hard rules

- **GitHub outranks the plan doc; the deployed app outranks GitHub.** A plan item marked "done" with no merged PR is *unverified*, not done. A merged PR the user can't see deployed is *merged, not live*.
- **Sync first.** `git fetch origin`; judge merged state from GitHub, never the local tree.
- **Delegate the plan-doc reading.** Plan files can be huge (observed: 288KB); never pull one into your own context whole.
- **Propose doc edits, apply only on confirmation.** Show exact before → after lines.
- **Live checks are opt-in** (`--live` or the user asks "is it deployed/visible") — they cost a browser agent per surface.

## Workflow

### 1. Locate the plan
Find the project-plan doc via the repo's CLAUDE.md or `docs/**/project-plan*`. Ambiguous → ask. Args = chunk identifier(s), or `all` for a summary across chunks.

### 2. Extract plan items (delegated)
One agent: *Read <plan path>, extract chunk <N>'s items. Return ONLY: item id, one-line description, and the status the doc currently claims.*

### 3. Map to GitHub (delegated, parallel with step 2 if items are known)
One agent: *For chunk <N>, find matching GitHub state: `gh issue list --state all --search "<chunk label / item keywords>"`, `gh pr list --state merged --limit 40 --json number,title,mergedAt,closingIssuesReferences`, plus open PRs. Return ONLY per item: issue #s + state, PR #s + merged date, or NONE-FOUND.* Items with NONE-FOUND are the interesting ones — they're either unstarted or were built without an issue; say which is more likely from PR titles.

### 4. Live verification (only if `--live`)
One browser agent (Playwright MCP if available, else HTTP checks) against the deployed base URL from repo docs: *For each shipped item below, verify the feature is actually present on <base URL>. Return ONLY per item: LIVE / NOT-VISIBLE / UNTESTABLE, with one line of evidence.* NOT-VISIBLE on a merged item usually means a pending or failed deploy — check the deploy workflow's last run before calling it a bug.

### 5. Report
One table: item → plan-doc claim → issues → PRs (merged date) → live check → **verdict** (`shipped` / `merged, not live` / `in flight` / `not started` / `doc stale`). Below it: discrepancies with evidence, and anything shipped that the plan doesn't track.

### 6. Fix the doc
For every `doc stale` row, propose the exact line edits (before → after). On confirmation, apply, and offer to commit on a branch — never commit to the default branch directly.

## Token discipline
- You hold the reconciliation table, not the sources: plan reading, GitHub mapping, and live checks are all delegated with "Return ONLY" row formats.
- Per-item rows, one line each — no issue bodies, no diffs, no screenshots inline (paths only).
