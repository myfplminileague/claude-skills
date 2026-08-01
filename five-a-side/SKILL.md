---
name: five-a-side
description: Plan and run a risk-budgeted adversarial review of a diff using repository-owned rule packs, deterministic lane selection, bounded mutation testing, batched adjudication, and focused post-fix verification. Use for /five-a-side, branch or PR review, review since a fixed point, or an automated review gate invoked by another skill.
---

# Five-a-side

Review expensive, slow-to-detect, or hard-to-reverse mistakes. Exempt everything else.

| Role | Owns | May block on |
| --- | --- | --- |
| `standards` | Repository rules | A cited documented-standard breach |
| `spec` | Requested behaviour | A missing or wrong requirement |
| `adversary` | Abuse and security | An exploitable defect |
| `operator` | Failure and recovery | An invisible or unrecoverable failure |
| `prover` | Test strength | A changed behaviour that survives a demonstrated mutation |
| `steward` | Duty of care | Consent, retention, exclusion, or a false user promise |

Read the matching role brief under `references/` before dispatching that role. Read
[`references/operating-notes.md`](references/operating-notes.md) only when changing this skill,
auditing its effectiveness, or investigating an incomplete/late run.

## Hard rules

- Use `.claude/five-a-side/packs/*.md` as the repository's review policy. Do not invent a standard.
- Run `scripts/review_plan.py`; do not recreate its lane or team selection in prose or regex.
- A missing reviewer report makes the run `INCOMPLETE`, never clear.
- A role may block only inside its declared scope. Everything else is a note.
- Report at most five findings per role and at most 120 words per finding. Declare truncation.
- Skip lint, formatting, type checking, secret scanning, and other deterministic CI work.
- Review only. Do not fix, commit, push, label, approve, or merge.

## Lanes

| Lane | Review | Budgets |
| --- | --- | --- |
| `exempt` | No model review; deterministic checks remain | 0 mutations, 0 adjudicators |
| `standard` | Pack-selected roles on `sonnet`; adjudication on | 3 mutations, 1 adjudicator batch |
| `critical` | Pack-selected roles using `models.yml`; human acknowledgement when declared | 6 mutations, 2 adjudicator batches |

`quick` is an explicit interactive WIP check. Use the standard team and model, skip adjudication, and
require a human to read the findings. Never use it on a PR or from another skill.

`full` is explicit and expensive: critical lane, every role. A risky hotfix also plays every role.
A hotfix that matches no pack remains exempt.

No matched pack means `exempt`, not an all-model escalation. A missing risk pack is a policy-maintenance
problem; paying six reviewers on every unclassified diff hides that problem instead of fixing it.

## Model policy

[`models.yml`](models.yml) is authoritative.

- Standard: every role runs on `sonnet` with its pinned effort.
- Critical: use each role's tier from `models.yml`.
- Hotfix/full: every role uses the top tier.
- Never inherit the caller's model and never use an excluded model.
- Record the actual model and effort beside every role.
- Bench an unavailable mid-tier role and mark the run incomplete; never silently upgrade or inherit.

## Workflow

### 1. Pin the fixed point

Resolve the caller's SHA, branch, tag, or base branch and require a non-empty three-dot diff:

```bash
git rev-parse <fixed-point>
git diff --stat <fixed-point>...HEAD
git diff --name-only <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

Fail here on an invalid ref or empty diff.

### 2. Produce the deterministic plan

```bash
python3 .claude/skills/five-a-side/scripts/review_plan.py \
  --packs-dir .claude/five-a-side/packs \
  --base <fixed-point> --head HEAD \
  [--signal hotfix] [--signal duty-of-care] [--signal full]
```

Save the JSON under an external scratch directory. Initialize review state:

```bash
python3 .claude/skills/five-a-side/scripts/review_state.py init \
  --plan-file <scratch>/plan.json --state-file <scratch>/state.json
```

If the lane is `exempt`, report the matched paths and stop with `EXEMPT — deterministic checks only`.
Do not dispatch an agent.

For `quick`, use the planned standard team but do not initialize automated remediation.

### 3. Build the spec and context bundle

Gather once with shell and pass the compact result to the roles that need it:

- issue title, body, **all comments**, linked decisions, PRD/design paths, and acceptance criteria;
- recent commits and merged PRs near the changed files;
- direct consumers of changed public modules or contracts;
- the matched pack names and the exact role sections each reviewer owns.

Do not make every reviewer rediscover the same issue history. The `spec` role receives the complete spec
bundle; `standards` receives the repository-context portion.

### 4. Run read-only reviewers in parallel

Dispatch every planned role except `prover` in one fan-out. Use a pinned
`five-a-side-<role>` definition when present, otherwise a read-only general agent. Each prompt contains:

- commands for the fixed-point diff;
- `references/<role>.md`;
- that role's sections from the matched packs;
- the relevant context bundle; and
- an external output path `<scratch>/findings/<role>.md`.

Require this format and a short `DONE <count>` return:

```text
[<role>] <block|note> <file>:<line> — <claim>
  why: <concrete failure>
  fix: <smallest sufficient correction>
  cite: <pack, repository rule, or spec line>
```

Retry a missing report once. If two or more roles miss, run the remaining roles serially. A second miss is
`DID NOT REPORT` and makes the run incomplete.

### 5. Run Prover sequentially and within budget

Run `prover` only after read-only reviewers finish.

- When called by `implement-issues`, use its already-bootstrapped, committed, dedicated worktree. Require
  a clean precondition, mutate one file at a time, restore immediately from `HEAD`, and verify the original
  status/diff after every mutation. Do not create or bootstrap another worktree.
- For a standalone committed review, use an isolated worktree if the current checkout is not dedicated.
- For uncommitted WIP, bench Prover unless the user explicitly accepts in-place mutation and restoration.

Pass the plan's mutation budget. Run the narrowest test that should fail and stop when the budget is spent.
The report must state the mutation count and what was skipped.

### 6. Adjudicate blocking claims in bounded batches

Deduplicate blockers by root cause. Resolve objectively provable claims with direct evidence—an exact test,
grep, schema check, or reproduction—and record that evidence without another model call.

Batch remaining judgement claims, up to the plan's `adjudicator_batches`:

1. safety: `adversary` and `steward` claims;
2. ordinary: every other role.

Use a model different from the producing reviewer. Return one verdict per claim: `REFUTED`, `STANDS`, or
`STANDS — FIX WRONG`. Uncertainty defaults to `STANDS` for the safety batch or when the adjudicator is below
the producer's tier; otherwise it defaults to `REFUTED`. A missing verdict keeps the block and is recorded as
timed out or empty. Late verdicts must be reconciled.

Refuted findings become notes; never delete them from the report.

### 7. Report and record metrics

Report the plan, matched packs, roles/models, mutation use, adjudication, findings, and exactly one decision:

- `CLEAR TO MERGE`
- `BLOCKED — n blocking findings (<roles>)`
- `INCOMPLETE — <role> did not report`
- `EXEMPT — deterministic checks only`

Append `HUMAN ACK REQUIRED — <reasons>` when the plan declares reasons. Record agent calls, duration,
blocks, notes, refutations, and mutations with `review_state.py record`.

## Focused verification after remediation

This skill never starts remediation itself. When a caller fixes blockers:

1. Permit one automated remediation with `review_state.py authorize-remediation`. A second attempt fails.
2. Re-plan the remediation delta from the reviewed commit to the fixed commit.
3. Verify with the roles that owned surviving blockers, plus roles newly selected by that delta.
4. Re-run only the tests and mutations tied to changed behaviour; stay inside the original mutation budget.
5. Run a new full review only when the remediation introduces a new pack/risk domain, changes a public
   contract/schema/deploy path not present before, or the user explicitly asks.
6. If focused verification still blocks, stop for a human decision. Do not start cycle three.

## Called by another skill

`implement-issues` supplies the fixed point, dedicated worktree, complete spec source, scratch directory,
and signals. Return blockers plus the decision; write the full report and state externally. Propagate
`INCOMPLETE`. `quick` is unavailable to callers.

## Enforcement

CI should call `review_plan.py` against its changed-path file and require a recorded report only when the
result is not exempt. The same pack frontmatter therefore controls Claude and CI. A report marker proves a
review was recorded, not that it was good; required status checks determine whether the control is preventive
or merely detective.
