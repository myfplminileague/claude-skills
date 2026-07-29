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
| `steward` | **Mertesacker** | *Substitute.* Were we allowed to do this to a user? | Consent, retention, exclusion, false promises |
| — | **Wenger** | The Gaffer: names the team sheet, calls the decision | Nothing — reports, never reranks |

**Why a substitute and not a sixth starter.** The five own engineering correctness. `steward` owns duty of care to a real person using a real product — lawful basis, consent, data minimisation, accessibility as exclusion, and copy that makes a commercial promise. None of those are security (a consent defect is not an exploit), none are spec (the issue rarely mentions them), and on most diffs there is nothing for him to do. So he sits on the bench and comes on for the diffs that touch a user. Five on the pitch.

**Roles are canonical, names are display.** Every file, key, finding prefix and trigger uses the role slug. A maintainer must never need to know who Raya is to work out what that reviewer checks.

## Hard rules

- **A reviewer that does not report is not a pass.** Its outcome is `DID NOT REPORT`, the run is `INCOMPLETE`, and the decision is never `CLEAR`. This exists because a previous five-agent fan-out spawned, went idle, and returned nothing — silence read as approval would have shipped unreviewed code.
- **Never merge or rerank findings across roles.** Report each role separately. A role's finding is not downgraded because another role disagrees; the axes are separate so one cannot mask another.
- **A reviewer may only block inside its declared scope.** Out-of-scope observations are `note`, never `block`. Ødegaard does not block on security; Rice does not block on naming.
- **Max 5 findings per reviewer — and truncation must be declared.** More than five is a review nobody reads. Report the five that matter, then state how many were dropped and at what severities (`dropped: 3 more (1 block, 2 note)`). A silent cap reads as "that was everything", which is the one thing it must never mean.
- **Packs are the repo's rules, not yours.** Never invent a standard. If it is not in a pack, in `CLAUDE.md`, or in a doc either links to, it is at most a `note`.
- **Skip what tooling already enforces.** Lint, format and typecheck are CI's job. A reviewer spending a finding on something `ruff`/`eslint` catches has wasted it.
- This skill **reviews**; it does not fix, commit, push or merge.

## Models and effort

Set `model` on every `Agent` call. Tier by **what the role has to invent**, not by how important it sounds — a role reading rules off a good pack is doing lookup, a role that must imagine an attack nobody wrote down is doing the hard thing.

**A tier that does not name a model is not a policy.** This section used to reason at length about "top" and "mid" without anywhere saying what either one *was*, and paired that with a closing line that inherited the caller's model when a name did not resolve. Since no name was ever given, that line was the only rule that ever fired: every role ran on whatever the session was running, which is the largest model available, while this document appeared to describe a considered allocation. Nobody chose it and nobody could see it. Name the models.

| Tier | Model | Effort |
| --- | --- | --- |
| **top** | `opus` | `high` |
| **mid** | `sonnet` | `medium` |

**The largest model in the family never reviews.** Not as a reviewer, not as a challenger, not as a fallback. Two reasons, and the second is the one that matters:

- No role's brief demonstrably needs it. The work is bounded — read a diff, check it against a written rule, try to break it — and the two tiers cover it.
- **It is the model that wrote the code.** Where builder and reviewer are the same model, the review re-derives the build's reasoning and agrees with itself. Excluding it is the cheapest model diversity this pipeline can buy, and it is the only change here that makes the reviews *better* rather than merely cheaper.

**No role runs on the small model either.** There is no mechanical stage to give it: every agent here exercises judgement, and the one genuinely mechanical step — gathering repo context — is deliberately plain shell run by the orchestrator, not an agent at all. Putting the small model on a judgement stage to save pennies degrades the stage. The savings live in the team sheet and in effort, not in a cheaper reviewer. Written down so it is not re-litigated by the next person reading the bill.

| Role | Tier | Effort | Why |
| --- | --- | --- | --- |
| `adversary` | **top** | `high` | Has to invent the attack. In trial it chained a push to `staging` → auto-deploy → a prod rollback with a `../..` path to serve an attacker's tree from prod. Nothing in any pack described that. |
| `operator` | **top** | `high` | Has to hold the whole failure surface at once and know what the shell actually does — e.g. that bash elides the fork for a lone simple command but not for a `cd && cmd` list, which is the entire probe-leak bug. |
| `prover` | **top** | `medium` | Choosing *which* mutation is worth making is judgement, so it keeps the tier. But its cost is overwhelmingly tool calls — it runs suites repeatedly — and "mutate it, run it, look at the colour" is not a reasoning-heavy loop. Effort is the one dial here that is safe to turn down. |
| `standards` | **mid** | `medium` | Mostly "does this line breach that written rule". The pack does the thinking; the model does the matching. |
| `spec` | **mid** | `medium` | A requirement-by-requirement walk. Escalate to **top** when there is no pack, or the spec is a long PRD with interacting acceptance criteria. |
| `steward` | **mid** | `medium` | Checklist-driven against the pack. Escalate to **top** for payments, consent defaults, or anything where the answer is "it depends". |
| challenger | **mid** | session, unless pinned | May not share the producing model, which under this policy usually puts it a tier below the finding it is challenging. There is no `challenger` role and so no role definition to pin its effort; a repo that wants one ships `.claude/agents/five-a-side-challenger.md` and the coverage check must permit that seventh file. Until then the compensation is not effort but the uncertainty default in *Challenge the blocking findings*, which is the part that actually protects the finding. |

**Effort is set on the agent definition, not on the call.** `Agent` takes `model` but has no effort parameter. A repo that wants per-role effort ships `.claude/agents/five-a-side-<role>.md` with `effort:` in the frontmatter and a `tools:` list — read-only for every role except `prover`, which mutates by design. The skill still passes `model` at call time, which takes precedence over the definition's own. **A definition's `model:` must name the cheap tier**, so a call that forgets to pass one fails cheap rather than expensive. Where a repo ships no definitions, the roles run at the session's effort with only the model pinned: degraded, not broken, and worth a line in the report.

**Do not economise on the refute pass.** It is the only stage that *removes* findings. The failure modes are not symmetric: a weak finder misses something, which shows up as a thin report someone can notice; a weak refuter deletes something already found, and nobody ever learns it existed. Combined with the split uncertainty defaults, a cheap refuter is the single most effective way to make this system quietly worse while it appears to be working. It must also differ from the producing reviewer's model — same model, same blind spot, so it re-derives the original reasoning and agrees with itself.

**Fallbacks go down, and say so.** If a named model is unavailable in the session, drop one tier and record it in the report beside that role. **Never inherit the caller's model.** The caller is usually running the excluded model, so "inherit" resolves to the one model this policy exists to keep out — silently, and at the moment nobody is looking. That is not a hypothetical; it is what the previous version of this section did.

**There are only two tiers, so the ladder needs a bottom rung.** A mid-tier role whose model is unavailable has nowhere to drop to: the rung below is the small model, which the paragraph above forbids outright. **Bench it and record it on the team sheet instead.** Dropping it would recreate the original failure exactly — a role silently running on a model the policy excludes — just at the other end of the range, and a benched role at least announces itself.

**Escalation rules.**

- **Hotfix → every role on top tier.** Same argument as the full squad: highest blast radius, least time, no staging net.
- **A mid-tier role that reports `dropped: n more` was saturated.** Re-run that one role at top tier before trusting its five. Truncation is the signal that the cheap tier hit its ceiling.
- **No pack matched → top tier for everyone.** Mid tier is only justified when a pack is carrying the reasoning; with no pack the model is doing it unaided. **This rule is a bill, and writing the pack is how you stop paying it** — the paths with no pack tend to be the risky ones that get reviewed most often, so the escalation lands precisely where the volume is.

**Escalation lifts the model. It cannot lift the effort.** Effort lives in a static per-role agent definition, so there is no call-time dial to turn — an escalated `standards` runs `opus`/`medium`, not `opus`/`high`, and the report will say so. Read the tier table's effort column as *the role's setting*, not as a property of the tier that escalation carries with it: `prover` already sits at top tier on `medium` deliberately, so tier and effort were never a fixed pair. This is a real limit rather than a rounding error — the no-pack rule fires on precisely the unpacked, high-churn paths, so escalated-but-medium is the common case, not the exotic one. If you want a role escalated in both dimensions, the only lever is a second definition, and that is not worth building until a run demonstrably needed it.

**Where the real saving is.** Model tier is the smaller lever. The team sheet is the bigger one — a typical UI diff plays three roles, not six, and that halves the run regardless of tier. Tune the pack globs before tuning the models.

## Depth

Three modes. The distinction that matters is not the tier — it is **whether the refute pass runs**, because that is the only stage that removes a finding before someone acts on it.

| Mode | Reviewer tier | Refute pass | Use for |
| --- | --- | --- | --- |
| `deep` | per the role table | **on** | risk paths, hotfixes, any second review cycle |
| `standard` | all roles **mid** | **on** | the default — ordinary diffs, first review cycles |
| `quick` | all roles **mid** | **off** | interactive work-in-progress, watched by a human |

**The refute pass is mandatory wherever findings reach anything but a human reading them.** Skipping it is safe in exactly one situation: a person is sitting there and can discard a wrong finding by eye. The moment findings feed an automated fixer, a PR body, or a merge decision, an unrefuted false positive stops being noise and becomes work — and with a TDD fixer downstream, it becomes *a test written to enshrine a defect that was never there*. So `quick` is forbidden on a PR and forbidden whenever this skill is called by another skill.

A quick run is noisier, never quieter. That is the right trade for a sanity check and the wrong one for a gate.

**Choosing the mode** — invoked as `/five-a-side <mode>`, or resolved in this order, first match winning:

1. An explicit mode from the user or the calling skill. A caller asking for `quick` gets `standard`.
2. **Hotfix → `deep`.** Highest blast radius, least time, no staging net.
3. **`adversary`, `operator` or `steward` on the team sheet → `deep`.** Those three only come on when a matched pack has a section for them or the diff touches a user, so their presence is the run's own evidence that this is not an ordinary change. It costs nothing to evaluate — step 4 already worked it out — and it means the expensive mode is chosen by the same signal that picks the squad, rather than by a second copy of the repo's risk list kept somewhere else and free to drift from the first.
4. Otherwise `standard`.

Whatever it resolves to, the report says so. Someone who thinks a change deserved more than it got can then ask for it, which is only possible if the mode is on the page.

**Mode sets the floor; the escalation rules lift from there.** The two are not alternatives, and a mode never overrides an escalation. A hotfix resolves to `deep` *and then* lifts every role to top tier — including the three the role table leaves at mid. A run where no pack matched lifts everyone to top whatever the mode said; that is the bill *Models and effort* describes. A saturated mid-tier role is re-run at top even on a `standard` run. Escalation only ever moves a tier up; nothing in this section moves one down.

**`quick` is the one exception.** It is exempt from escalation, because it is an explicit request for a cheap look with a human reading the output, and quietly promoting it to top tier because no pack matched would make the cheap mode expensive at precisely the moment someone asked for cheap. A `quick` run that turns out to need more gets re-run as `standard` by the person who is, by definition, watching it.

## When it must run

Review is required where a mistake is **expensive, slow to detect, or hard to reverse** — and nowhere else. This is the opposite of where this skill started, and the correction was expensive enough to be worth stating plainly.

The first version required a review on every change into a protected branch and exempted nothing. Within a day of real use it had blocked the first production promotion, and a colleague could not merge a single small fix. *"The workflow has become very restrictive… Every issue has become colossal."* That is the failure mode that gets a gate deleted rather than respected, and a deleted gate protects nothing at all.

**Exempt by default, required by exception.** Three exemptions, each earned by blocking someone real:

- **Promotions** from an integration branch to a release branch. Their commits were each reviewed on the way in; re-reviewing the aggregate re-reads reviewed work and finds nothing new.
- **Bot pull requests** — version bumps, lockfile updates. No human wrote the diff, so there is no judgement for a reviewer to check. Their real risk is dependencies and secrets, which belong to `npm audit` and a secret scanner.
- **Anything touching no risk path.** Measured on the eight PRs before the correction, five needed no review at all.

**The risk set must come from incidents, not categories.** Write down the paths where you have actually been hurt — the deploy scripts that took the site down, the consent surface that leaked to real users, auth, personal-data writes, migrations, published legal text. Resist tidy taxonomies: the first draft of one such list omitted the exact file whose review had found five live defects.

Keep the set short. Every entry is friction on every future change, so each one earns its place by naming somewhere a mistake was expensive.

**A risky hotfix plays the full squad.** Where a hotfix touches a risk path, it withdraws the path-based benching that normally trims the team sheet:

- It goes straight to the release branch, so a bad one takes the live site down — the highest blast radius any change has.
- It was written under time pressure, which is when the guards get skipped.
- It skips the integration branch, losing the one environment that would have caught it.

Urgency is the argument for **more** review of a risky change, not less.

But a hotfix that touches no risk path is still just a change — a copy fix on a live page is not made dangerous by the branch it lands on. The old rule here said "no exceptions", which combined with an always-on gate is exactly how this skill made a small fix impossible to ship. If the squad is genuinely in the way, override with a reason; that is on the record, which is all the rule was ever really buying.

## Workflow

### 1. Pin the fixed point

Whatever the user supplied — a SHA, branch, tag, `main`, `HEAD~5`. If they gave none, ask.

```
git rev-parse <fixed-point>                     # must resolve
git diff --stat <fixed-point>...HEAD            # must be non-empty
git diff --name-only <fixed-point>...HEAD       # the path list, for steps 2 and 3
git log <fixed-point>..HEAD --oneline
```

Three-dot, so the comparison is against the merge-base. A bad ref or empty diff fails **here** — not inside five parallel subagents.

### 2. Gather what the diff cannot show

A diff shows what changed, never what already exists. Without this step no reviewer can tell you this is the fourth implementation of the same thing, that a route is now unreachable, or that someone merged the same feature last week — the whole class of finding that is invisible from the change alone.

This is **cheap shell, not an agent**. Run it yourself and pass the result into the fan-out:

```
# What landed recently near these files — the overlap the dependency graph never shows
git log <fixed-point> --oneline -15 --  <changed paths>
gh pr list --state merged --limit 15 --json number,title,mergedAt -q '.[] | "#\(.number) \(.title)"'

# Who else depends on what changed, so a "small" edit's real radius is visible
# Quote the patterns: unquoted --include=*.ts is glob-expanded by the calling
# shell before grep sees it, and zsh aborts the command outright.
grep -rl "<each changed module's export or path>" \
  --include='*.ts' --include='*.tsx' --include='*.js' --include='*.py' . | head -20

# How settled each changed file is: brand new, or load-bearing for a year
git log --oneline -3 -- <each changed file>
```

Summarise into a short block — recent overlapping work, who imports the changed modules, which files are new versus long-lived. Keep it under ~15 lines; this is orientation, not a second diff.

Give it to **`standards`** (it makes Duplicated Code and Shotgun Surgery visible instead of theoretical) and **`spec`** (scope creep and "this already exists" are only judgeable against what already exists). The other roles reason about the change itself and do not need it.

If the repo is not a git checkout, or `gh` is unavailable, say so in the report and continue — degraded, not blocked.

### 3. Select packs from the changed paths

Read `.claude/five-a-side/packs/*.md` in the repo under review. Each pack declares `paths:` globs in its frontmatter. A pack is **matched** if any changed path matches any of its globs. Read only the matched packs.

If the repo has **no packs directory**, say so in the report and run with `CLAUDE.md` plus whatever it links as the only rule source — degraded, but honest. Do not invent packs.

### 4. Name the team sheet

- `standards` and `spec` **always play**.
- `prover` plays whenever the diff changes behaviour (any non-docs code change).
- `adversary` and `operator` play when a matched pack has a non-empty section for them.
- `steward` comes off the bench when the diff touches **a user**, not merely a domain: PII collection or a new stored field about a person, consent capture or its defaults, retention or deletion, payments and pricing, messaging (WhatsApp/SMS/email), analytics properties, public-page accessibility, or user-facing copy that promises something. A matched pack's `steward` section also brings him on.
- **Everyone plays, triggers ignored, when the change is a hotfix** — the branch targets `main` on a repo where routine work targets `staging`, the issue carries a `hotfix` label, or the caller says so. See *When it must run*.
- `/five-a-side full` plays everyone regardless of triggers.
- **`spec` is benched when there is no spec.** If no issue, PRD or design doc can be located, record that on the team sheet and do not spawn it. An agent whose only possible finding is `no spec available` spends a full model call telling you something the orchestrator already knew before it fanned out. The information is not lost — benched-for-no-spec is itself the finding, and on a change that should have had an issue it is one worth reading.

Announce the team sheet before fanning out: the depth mode, which roles play, which packs matched, and why anyone is benched. A benched reviewer is a deliberate decision the user can overrule.

### 5. Fan out

One message, one `Agent` call per playing role — `agentType` `five-a-side-<role>` where the repo defines one (see *Models and effort*), otherwise `general-purpose`. Each prompt contains:

- The diff and log commands from step 1 (the **commands**, not the diff text — the subagent runs them itself).
- The full text of `references/<role>.md`.
- The `## <role>` sections of every matched pack, pasted in full. The subagent has no other access to them.
- **For `standards` and `spec` only**: the repo-context block from step 2.
- The spec source for `spec` (issue number to `gh issue view`, or a path).
- **Its output path**: `<scratch>/five-a-side/<role>.md`. **`<scratch>` must be outside the repo working tree.** Reports written inside it are picked up by repo-wide formatters and linters — `prettier --check .` and friends do not care that a file is untracked — so the first commit after a review fails on the review's own artifacts.

**Isolate `prover`, when the work under review is committed.** It is the only reviewer that writes: its protocol is mutate → run the suite → revert, in the same tree the other four are reading. Two things go wrong there. Another reviewer reads a file mid-mutation and reports, confidently and with a line number, on code that never existed. Or the prover goes idle between the mutation and the revert — an observed failure mode, see *Known limits* — and leaves deliberately broken code in a branch someone is about to push, with nothing in the report to say so. Passing `isolation: "worktree"` on that one call makes both impossible and stops the revert step being load-bearing. It costs one dependency bootstrap per run, which is the price of the only role that writes.

**But not for uncommitted work.** A fresh worktree checks out the branch, not the caller's unsaved edits, so an isolated prover on a work-in-progress diff would faithfully mutate and test the wrong code — a worse failure than the one the isolation prevents. When the diff under review is uncommitted, run `prover` in place, tell the user their working tree will be mutated and restored, and treat the `git status` check in step 6 as a hard gate rather than a courtesy.

Set `model` on each call per *Models and effort* above, and record the model and effort each role actually ran at — the report must state them, because a finding's absence means something different at `sonnet`/`medium` than at `opus`/`high`.

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
> `block` only for the scope your brief declares blocking; everything else is `note`. If you had more than 5, end the file with `dropped: n more (x block, y note)`. If you find nothing, write `NO FINDINGS` to the file. Never write an empty file.

### 6. Team-sheet check

After the fan-out, list `<scratch>/five-a-side/`. For every role that played:

- File present with findings or `NO FINDINGS` → **reported**.
- File missing, empty, or agent returned nothing → **retry that role once**.
- Still missing → mark `DID NOT REPORT` and carry it into the report. **Do not** substitute your own review for it, and do not quietly drop it.

If two or more roles fail the retry, abandon the fan-out and **run the remaining roles serially** — a fan-out that flaky is not going to improve on a third parallel attempt.

**Then check the tree, if `prover` ran un-isolated.** Run `git status --porcelain` yourself; do not take the agent's word for it. A surviving mutation is the one review artifact that can damage the thing being reviewed, and the role most likely to leave one is the role that also sometimes dies mid-protocol. If the tree is dirty in a way the diff does not explain, say so at the top of the report, name the files, and do not describe the run as complete.

### 7. Challenge the blocking findings

**Deduplicate first.** Several reviewers reaching the same underlying defect from different briefs is the system working — but it is one claim, not four, and challenging it four times wastes the pass and produces four verdicts on one line of code. Collapse blocking findings that name the same root cause into a single claim, listing which roles reached it. **Independent convergence is evidence: say so in the report, and give the merged claim one challenge, not none.**

Then one `Agent` call per **distinct** blocking claim, prompted to **refute**:

> Here is a review finding on this diff: `<finding>`. Your job is to refute it. Read the actual code at that location and the rule it cites. Return `REFUTED: <why>` if the finding is wrong, misreads the code, or rests on a rule that does not say what it claims — or `STANDS: <the one-line reason it is real>`. `<default-clause>`

**The uncertainty default is not the same for every role.**

- `adversary` and `steward` → *"When genuinely uncertain, return `STANDS`."* A false positive costs one argument. A suppressed exploit or an unlawful data capture costs a great deal more — and those are exactly the finding types where certainty is hardest to reach, so a REFUTED-on-doubt default systematically discards the most valuable findings the squad produces.
- every other role → *"When genuinely uncertain, return `REFUTED`."*

**And it is not the same at every tier.** Run the challenge on a different model from the one that produced the finding (set `model` on the `Agent` call) — a challenger sharing the reviewer's model shares its blind spots, re-derives the original reasoning and agrees with itself. But with the largest model excluded from review, "different from the producer" and "at least the producer's tier" cannot both hold for a top-tier finding: the only remaining choice is a tier down. Independence is the more valuable of the two, so take it, and pay for the weaker challenger explicitly:

> **A challenger running below the producer's tier defaults to `STANDS`, whatever the role.**

Which gives one rule covering both halves: **return `STANDS` on doubt unless the challenger is at least the producer's tier *and* the producing role is neither `adversary` nor `steward`.** Everything else defaults to `REFUTED`.

Note where this lands. On a hotfix every role plays at top tier, so every challenge is a tier down and every uncertain verdict keeps its finding — more surviving findings reach a human on exactly the changes that had the least margin for error. That is the intended direction, not an accident of the model policy.

**A third verdict: `STANDS — FIX WRONG`.** Refutation is not binary. A challenger may confirm the defect while establishing that the proposed remedy is wrong — the wrong file, the wrong repo, a mitigation that already exists elsewhere. Observed: a finding correctly identified a stale published policy but sent the fix to a repo whose sync pipeline is not built yet. Record the correction alongside the finding; a right diagnosis with a wrong prescription still wastes someone's afternoon.

**Silence fails safe.** A challenger that returns no verdict — idle, dead, or empty — leaves the finding **`block`, unchanged**. Retry once; if the second attempt is also silent, stop and mark the finding `unchallenged` in the report. Never read an absent verdict as consent to demote. This is the opposite of the fan-out's rule and deliberately so: there, a missing report means work was not done, so the run is `INCOMPLETE`; here, a missing verdict would *delete* work already done. Deleting a finding requires an affirmative refutation, never the absence of one.

Accept that failing safe has a cost — an unchallenged weak finding stays at `block` and someone must argue it down by hand. That is the correct side to err on: a wrongly-kept finding costs one conversation, a wrongly-deleted one costs whatever it was about.

`REFUTED` findings are demoted to `note` with the refutation attached, not deleted — the user still sees them and can disagree. This costs one cheap agent per distinct blocker and is what stops plausible-but-wrong findings reaching the user.

### 8. Wenger's report

```
## Team sheet
Mode:    standard
Played:  standards (sonnet/medium), spec (sonnet/medium), prover (opus/medium)
Benched: adversary, operator (no matching pack section), steward (touches no user)
Packs:   design-system, frontend-app

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

**Name the actual model and effort, never the tier alias.** Three things depend on it: a reader weighing what a role's silence is worth, anyone auditing whether a fallback quietly downgraded a role mid-run, and the only per-run record of what the review cost. `mid` tells you none of that; `sonnet/medium` tells you all three. Where the repo ships no agent definitions and effort was the session's, write `sonnet/session` rather than inventing a number.

One role per section, in the table's order. Then one decision line, exactly one of:

- `CLEAR TO MERGE` — every playing role reported, zero surviving blocks.
- `BLOCKED — n blocking findings (<roles>)`.
- `INCOMPLETE — <role> did not report` — **never** `CLEAR`, regardless of what the others found.

Do not pick a "worst finding overall". Report the worst *within each role* and stop there.

**Human acknowledgement threshold.** When the diff touches **payments, authentication or authorisation, database migrations, outbound messaging, or legal/policy content**, append:

```
HUMAN ACK REQUIRED — <reason>. A named person must read this report before merge.
```

This is appended *regardless of the decision line*, including on `CLEAR TO MERGE`. These five areas are the ones where a mistake is expensive, slow to detect, and hard to reverse, and a clean automated review is not sufficient grounds to skip a person on them.

The skill only states the requirement. For the marker to mean anything the gate must **fail** on it unless a second, separately-applied signal says a named person acted — a `human-ack:confirmed` label or a required approving review. A gate that prints a notice and exits zero leaves the marker riding through untouched, which is worse than not emitting it: it reads as a control while being decoration. And note the author writes the body, so this constrains an honest author, not a determined one.

## Called by another skill

`implement-issues` invokes this as its review gate. When called that way:

- The caller supplies the fixed point (the issue branch's merge-base), the worktree path, the issue number as the spec source, its own scratch dir, and **the depth mode**.
- **`quick` is not available to a caller** — its findings go to a fix agent, not to a human's eyes, and that is the one thing the refute pass may never be skipped for. A caller asking for `quick` gets `standard`, and the report says so. The caller stays free to choose between `standard` and `deep`, which is where it belongs: the caller knows whether this is a first pass or the last gate before a PR.
- Return **only** the blocking findings plus the decision line — the caller feeds those to a fix agent and does not need the notes inline. Write the full report to `<scratch>/five-a-side/report.md` for the caller to attach to the PR body.
- `INCOMPLETE` must propagate. A caller must not open a PR on a run where a role did not report.

## Enforcement

A review gate that depends on someone remembering to run it is not a gate. Two mechanisms make it one, and neither costs a Claude token.

**The label check.** A CI job that fails only when a **risky** change carries no recorded review — the label plus a report block in the body. Seconds of runner time. It cannot verify the review was *good*, only that one happened.

**It must have an override, and the override must be advertised.** A gate a competent engineer cannot get past is a gate that gets ripped out of the workflow, and then nothing is checked at all. Require a written reason rather than a click: the bypass is then recorded instead of prevented, which is the honest trade. Say so *in the failure message* — someone blocked at 11pm should be told the legitimate way through, not left to conclude that deleting the workflow is the only exit.

**Know which of the two it is, because they are not the same control:**

- **Preventive** requires *required status checks* — a paid GitHub plan plus a branch-protection or ruleset rule. Only then does a red check actually stop a merge.
- **Detective** is what you get otherwise. The check goes red, the merge proceeds, and the value is the record.

Check before claiming either: `gh api repos/{owner}/{repo}/branches/{branch}/protection`. A `403 Upgrade to GitHub Pro` means every "this gate blocks X" sentence you write is false. That happened here — the gate was designed, documented and reviewed as preventive on a repo where it can only ever be detective, and the constraint was already written in the repo's own CI header.

**Trigger on `push` as well as `pull_request`.** A `pull_request`-only gate never fires on a direct push to the protected branch, which is precisely the 11pm hotfix path it exists to catch. Where direct pushes are routine, a PR-only trigger means the gate is absent exactly when it matters.

Never make the job skippable for urgent changes; that is the case it exists for.

**The pack check.** A test asserting that every pack's `paths:` globs match at least one real file, and every link in a pack resolves. Packs are the entire quality ceiling of this system, and a pack citing a rule that has since been deleted produces a *cited*, confident, wrong finding — more persuasive than an uncited one, and harder to argue with. Nothing else stops that drift.

## Known limits

State these when someone asks how much to trust a clean run:

- **A partly-shared prior.** Builder and reviewers are separate agents, and since *Models and effort* excludes the largest model — the one that usually writes the code — they are no longer the same model either. That much is now real diversity rather than a caveat, and it is the strongest argument for the exclusion: it was adopted to cut cost and happens to also cut correlated blind spots. What remains is still substantial. The reviewers share a family and a training lineage with the builder, and five roles on one model produce five prompts over one prior, not five independent judgements. The cross-model refute pass narrows it further at one point. Nothing here removes it.
- **Diff-scoped, partially.** Step 2 hands `standards` and `spec` the surrounding context, which covers recent overlapping work and the changed modules' dependents. What it still will not catch is architectural drift with no textual trace — a pattern quietly abandoned, a boundary eroded over months. Those need a human or a deliberate audit, not a diff review.
- **Packs are the ceiling.** Every reviewer is exactly as good as the rules it was handed. An unwritten rule is an unreviewable one.
- **Agents go silent, and the refute pass is where it hurts.** Observed across three runs now: reviewers and challengers both sometimes finish without returning anything, not uniformly across models. In the third run **both** challengers returned no verdict, including after a retry, so every blocking finding shipped `unchallenged` — a correct outcome under the fail-safe rule, but it means the pass that is supposed to remove wrong findings removed nothing at all. Budget for that: the refute pass is best-effort, and a run where it is silent is a run whose blocks have had exactly one pair of eyes. Every stage has an explicit rule for absence — `DID NOT REPORT` in the fan-out, `unchallenged` in the refute pass — and neither ever reads as approval. If a run reports neither, the orchestrator skipped a check.
- **Convergence can be correlated.** Roles sharing a model can reach the same wrong conclusion and look like corroboration. Cross-model challenge is what distinguishes agreement from a shared blind spot; a finding confirmed only by same-model roles is weaker than its vote count suggests.

## Adding a repo

Nothing in this skill is repo-specific, so onboarding a repo is only: write `.claude/five-a-side/packs/*.md` for its domains. See [`references/pack-format.md`](references/pack-format.md). The five roles do not change; the rules they read do.

Optionally, add `.claude/agents/five-a-side-<role>.md` definitions to pin each role's reasoning effort and tool set — see *Models and effort*. Without them the model is still pinned and the review still runs, so this is a refinement, not a prerequisite. Note that these live outside the skill directory, so a repo that checks its vendored copy against a hash must extend that check to cover them, or it has a drift fence with a hole next to it.
