---
name: next-batch
description: Pick and prepare the next buildable batch of GitHub issues — sync origin, enumerate open issues for a chunk or milestone, check dependencies, in-flight work, and overlap with recently merged PRs, verify each issue body is builder-ready, then propose a ≤4-issue batch in build order and hand off to /implement-issues. Use when the user runs /next-batch, or asks "what should we build next", "are these unblocked", "give me a build order", or wants the next wave from a chunk.
---

# Next Batch

You are the **triage front-end** for `/implement-issues`. Your job is to answer, with evidence: *what should we build next, in what order, and is it actually ready to hand to a context-free builder?* You do not build anything.

## Hard rules

- **Sync before judging.** A stale local default makes shipped work look unbuilt (observed failure mode: user nearly rebuilt two already-merged issues). `git fetch origin` first; reason from `origin/<default>` and from GitHub state, never from the local tree.
- **Recommend at most 4 issues** per batch (the `/implement-issues` cap). More candidates → rank and defer the rest to the next batch.
- **Never mark an issue "ready" you haven't had read.** Readiness is judged from the full issue body, by a delegated agent.
- **If dependency relations are ambiguous, ask the user** rather than guessing an order.

## Workflow

### 1. Enumerate candidates
Args may be a chunk/milestone name ("chunk 8"), a label, or explicit issue numbers. Discover how this repo groups work — milestone, `chunk-N` label, or a project-plan doc referenced in CLAUDE.md — and list open issues in that group (`gh issue list --json number,title,labels,milestone`). No args → ask which chunk/group, showing what groups exist.

### 2. Exclude in-flight and shipped work
For each candidate, check: open PRs referencing it (`gh pr list --state open --search "in:body #<N>"`), existing `issue-<N>-*` branches, and the recent-merge overlap scan (`gh pr list --state merged --limit 20 --json number,title,mergedAt`). Anything already in flight or plausibly shipped gets flagged with evidence, not silently included. If a merged PR looks like it *partially* covers an issue, say so — that changes the issue's scope.

### 3. Dependency graph (cheap)
Native GitHub relations only: `gh issue view <N> --json number,title,labels` plus the timeline cross-references (same commands as `/implement-issues` step 2). Topologically sort; note which candidates are unblocked *now* vs blocked on unmerged work.

### 4. Readiness audit (delegated)
One agent for the whole candidate set. Prompt: *For each issue number below, run `gh issue view <N>` and judge whether a builder with no other context could implement it: acceptance criteria present, key decisions resolved (no open questions), scope bounded, test expectations stated. Return ONLY per issue: READY, or NOT-READY with the specific gaps (missing decision, vague AC, unresolved question).* Issues that come back NOT-READY get a recommendation to run `/grill-me` + `/to-prd` on them first — do not put them in the batch.

### 5. Propose the batch
Present: a ≤4-issue batch in build order (waves if there are dependencies), per-issue one-line rationale, flagged same-area pairs likely to conflict at merge, the NOT-READY list with gaps, and what's deferred. Recommend, don't auto-run.

### 6. Hand off
On the user's confirmation, invoke the **/implement-issues** skill with the chosen issue numbers. Pass along anything the builders must know from step 2 (e.g. "PR #296 already added the order-detail page — reuse it").

## Token discipline
- You read titles, labels, and relations; only the readiness agent reads bodies.
- Demand "Return ONLY" structured outputs; no body echoing.
- The overlap scan is titles + dates, not diffs.
