# Operating notes

Read this only when changing five-a-side, auditing its effectiveness, or investigating an incomplete or
late run. The operative workflow stays in `SKILL.md`.

## Why the system is risk-budgeted

The first gate reviewed every change into a protected branch. It immediately blocked promotions, bot PRs,
and small reversible fixes. A gate nobody can live with is eventually bypassed or deleted. The durable rule
is therefore: review where a mistake is expensive, slow to detect, or hard to reverse, and nowhere else.

The largest saving comes from the lane and team sheet, not from quietly downgrading every model. A typical
reversible product diff should use a small standard team. Authentication, authorisation, consent, payments,
migrations, outbound messaging, destructive data operations, and deploy/rollback work justify the critical
lane. Repository incidents—not a tidy generic taxonomy—should decide the actual pack globs.

## Why model diversity remains

Builder and reviewer agents share training priors even when they are separate processes. Excluding the
largest builder model from review cheaply reduces self-agreement. Cross-model adjudication is still useful,
but one call per finding multiplied cost without providing one independent mind per claim. Bounded batches
retain a different prior while capping the fan-out.

Never interpret convergence as votes. Two roles can share a mistaken prior. Deduplicate the root cause,
preserve which roles found it, and adjudicate the claim once.

## Why Prover is bounded and sequential

Mutation testing has found assertions that matched nothing, matched the wrong occurrence, or passed for an
unrelated failure. It is valuable and also the slowest role because it repeatedly runs tests.

Earlier runs isolated Prover into a fresh worktree for every review. That duplicated dependency bootstrap and,
when a frontend session reviewed a backend worktree, sometimes isolated the wrong repository. Running Prover
after read-only roles in the caller's dedicated clean worktree removes both costs. The orchestrator must still
verify restoration; an agent dying mid-mutation is the one review failure that can damage the branch.

Budgets are sampling limits, not coverage claims. The report must say what was mutated and what was skipped.

## Why remediation gets focused verification

A fix is new code and can introduce a regression. Repeating the entire original squad, however, re-reads large
areas that did not change. Verify the original blocker owners plus roles newly triggered by the remediation
delta. Escalate to a full review only for a new domain, contract, schema, deploy path, or explicit request.

One automated remediation is the hard limit. A remaining block after focused verification is a design or
judgement problem, not permission to start an unbounded third cycle.

## Known limits

- Packs are the quality ceiling. An unwritten rule is unreviewable.
- A diff plus local dependency search does not reveal slow architectural drift.
- Reviewers share a model family and are not independent experts.
- Slow and silent agents are hard to distinguish. Record `timed out` separately from `returned empty`, and
  reconcile late results.
- A clean automated review is insufficient human authority for legal, payments, consent, destructive data,
  or production-operational decisions when the pack asks for acknowledgement.
- Metrics describe cost and outcomes, not escaped defects. Periodically compare reports with later incidents,
  CI failures, rollbacks, and human-found bugs before loosening a critical pack.

## Pack maintenance

When a finding nobody accepts recurs, narrow or remove the pack rule instead of arguing on every PR. When an
incident a role could have caught occurs, add the smallest checkable rule and the incident reference. Keep
paths narrow; every glob is recurring friction.
