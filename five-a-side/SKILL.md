---
name: five-a-side
description: Review a diff with a five-member adversarial review team — Standards, Spec, Adversary, Operator and Prover — each loading this repo's own rule packs, then aggregate into one merge decision. Use when the user runs /five-a-side, asks to review a branch, PR, or work-in-progress changes, asks to "review since X", or when another skill needs a review gate.
---

# Five-a-side

Five reviewers, one question each. The **roles are fixed**; the **domain is a variable** — each reviewer loads the repo's own packs for whatever the diff touches, so the same five cover frontend, backend, database, design system, CI and content without becoming ten.

| Role | Name | Question it owns | May block on |
| --- | --- | --- | --- |
| `standards` | **Ødegaard** | Does this match how we build here? | Documented-standard breaches |
| `spec` | **Bergkamp** | Does it do what was asked — no less, no more? | Missing or wrong requirements |
| `adversary` | **Rice** | Can it be broken? | Anything exploitable |
| `operator` | **Raya** | Can I see it fail, and can I undo it? | Unrecoverable or invisible failure |
| `prover` | **Henry** | Do the tests go red when the code is wrong? | Behaviour change no test catches |
| — | **Wenger** | The Gaffer: names the team sheet, calls the decision | Nothing — reports, never reranks |

**Roles are canonical, names are display.** Every file, key, finding prefix and trigger uses the role slug. A maintainer must never need to know who Raya is to work out what that reviewer checks.

## Hard rules

- **A reviewer that does not report is not a pass.** Its outcome is `DID NOT REPORT`, the run is `INCOMPLETE`, and the decision is never `CLEAR`. This exists because a previous five-agent fan-out spawned, went idle, and returned nothing — silence read as approval would have shipped unreviewed code.
- **Never merge or rerank findings across roles.** Report each role separately. A role's finding is not downgraded because another role disagrees; the axes are separate so one cannot mask another.
- **A reviewer may only block inside its declared scope.** Out-of-scope observations are `note`, never `block`. Ødegaard does not block on security; Rice does not block on naming.
- **Max 5 findings per reviewer.** More than that is a review nobody reads. Report the five that matter and say how many were dropped.
- **Packs are the repo's rules, not yours.** Never invent a standard. If it is not in a pack, in `CLAUDE.md`, or in a doc either links to, it is at most a `note`.
- **Skip what tooling already enforces.** Lint, format and typecheck are CI's job. A reviewer spending a finding on something `ruff`/`eslint` catches has wasted it.
- This skill **reviews**; it does not fix, commit, push or merge.

## When it must run

Every change landing on a **protected branch** gets reviewed — in this org that is `staging` and `main` on the frontend, `main` on the backend. `staging` is not a lower bar: it is the first branch that actually deploys, so it is the first place a defect becomes real.

**A hotfix plays the full squad.** No path-based benching, no exceptions:

- A hotfix targets `main`, so a bad one takes the live site down — the highest blast radius any change in this org has.
- It was written under time pressure, which is when the guards get skipped.
- It skips `staging`, so it loses the one environment that would have caught it.

Urgency is the argument for **more** review, not less. The path triggers in step 3 are an optimisation for routine work; a hotfix withdraws the optimisation. If someone wants to ship without the squad, that is a decision they take explicitly and on the record — not a default the skill hands them.

## Workflow

### 1. Pin the fixed point

Whatever the user supplied — a SHA, branch, tag, `main`, `HEAD~5`. If they gave none, ask.

```
git rev-parse <fixed-point>                     # must resolve
git diff --stat <fixed-point>...HEAD            # must be non-empty
git diff --name-only <fixed-point>...HEAD       # the path list, for step 2
git log <fixed-point>..HEAD --oneline
```

Three-dot, so the comparison is against the merge-base. A bad ref or empty diff fails **here** — not inside five parallel subagents.

### 2. Select packs from the changed paths

Read `.claude/five-a-side/packs/*.md` in the repo under review. Each pack declares `paths:` globs in its frontmatter. A pack is **matched** if any changed path matches any of its globs. Read only the matched packs.

If the repo has **no packs directory**, say so in the report and run with `CLAUDE.md` plus whatever it links as the only rule source — degraded, but honest. Do not invent packs.

### 3. Name the team sheet

- `standards` and `spec` **always play**.
- `prover` plays whenever the diff changes behaviour (any non-docs code change).
- `adversary` and `operator` play when a matched pack has a non-empty section for them.
- **All five play, triggers ignored, when the change is a hotfix** — the branch targets `main` on a repo where routine work targets `staging`, the issue carries a `hotfix` label, or the caller says so. See *When it must run*.
- `/five-a-side full` plays all five regardless of triggers.
- `spec` with no locatable issue/PRD still plays, and reports `no spec available` as its only finding.

Announce the team sheet before fanning out: which roles play, which packs matched, and why anyone is benched. A benched reviewer is a deliberate decision the user can overrule.

### 4. Fan out

One message, one `Agent` call per playing role, `agentType` general-purpose. Each prompt contains:

- The diff and log commands from step 1 (the **commands**, not the diff text — the subagent runs them itself).
- The full text of `references/<role>.md`.
- The `## <role>` sections of every matched pack, pasted in full. The subagent has no other access to them.
- The spec source for `spec` (issue number to `gh issue view`, or a path).
- **Its output path**: `<scratch>/five-a-side/<role>.md`.

Every prompt ends with the findings contract:

> Write your findings to `<scratch>/five-a-side/<role>.md` and return ONLY the word `DONE` plus your finding count. Max 5 findings. Format each as:
>
> ```
> [<role>] <block|note> <file>:<line> — <one-line claim>
>   why:  <what actually goes wrong>
>   fix:  <the smallest change that resolves it>
>   cite: <the pack rule, doc line, or spec line this rests on>
> ```
>
> `block` only for the scope your brief declares blocking; everything else is `note`. If you find nothing, write `NO FINDINGS` to the file. Never write an empty file.

### 5. Team-sheet check

After the fan-out, list `<scratch>/five-a-side/`. For every role that played:

- File present with findings or `NO FINDINGS` → **reported**.
- File missing, empty, or agent returned nothing → **retry that role once**.
- Still missing → mark `DID NOT REPORT` and carry it into the report. **Do not** substitute your own review for it, and do not quietly drop it.

If two or more roles fail the retry, abandon the fan-out and **run the remaining roles serially** — a fan-out that flaky is not going to improve on a third parallel attempt.

### 6. Challenge the blocking findings

Only `block` findings, and only if there are any. One `Agent` call per blocking finding, prompted to **refute**:

> Here is a review finding on this diff: `<finding>`. Your job is to refute it. Read the actual code at that location and the rule it cites. Return `REFUTED: <why>` if the finding is wrong, misreads the code, or rests on a rule that does not say what it claims — or `STANDS: <the one-line reason it is real>`. Default to `REFUTED` when genuinely uncertain.

`REFUTED` findings are demoted to `note` with the refutation attached, not deleted — the user still sees them and can disagree. This costs one cheap agent per blocker and is what stops plausible-but-wrong findings reaching the user.

### 7. Wenger's report

```
## Team sheet
Played: standards, spec, prover   Benched: adversary, operator (no matching pack)
Packs:  design-system, frontend-app

## Ødegaard — Standards
[standards] block src/components/prize-card.tsx:34 — hardcoded Tailwind colour
  why:  bg-red-500 bypasses the token layer; won't follow a theme change
  fix:  bg-error
  cite: packs/design-system.md — "never hardcode Tailwind colours"

## Bergkamp — Spec
NO FINDINGS

## Henry — Prover
[prover] note src/lib/prize-split.ts:12 — assertion passes against broken code
  ...

## Decision
BLOCKED — 1 blocking finding (standards). 3 notes.
```

One role per section, in the table's order. Then one decision line, exactly one of:

- `CLEAR TO MERGE` — every playing role reported, zero surviving blocks.
- `BLOCKED — n blocking findings (<roles>)`.
- `INCOMPLETE — <role> did not report` — **never** `CLEAR`, regardless of what the others found.

Do not pick a "worst finding overall". Report the worst *within each role* and stop there.

## Called by another skill

`implement-issues` invokes this as its review gate. When called that way:

- The caller supplies the fixed point (the issue branch's merge-base), the worktree path, the issue number as the spec source, and its own scratch dir.
- Return **only** the blocking findings plus the decision line — the caller feeds those to a fix agent and does not need the notes inline. Write the full report to `<scratch>/five-a-side/report.md` for the caller to attach to the PR body.
- `INCOMPLETE` must propagate. A caller must not open a PR on a run where a role did not report.

## Adding a repo

Nothing in this skill is repo-specific, so onboarding a repo is only: write `.claude/five-a-side/packs/*.md` for its domains. See [`references/pack-format.md`](references/pack-format.md). The five roles do not change; the rules they read do.
