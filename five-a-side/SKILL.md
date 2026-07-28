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

## Model tiers

Set `model` per `Agent` call. Tier by **what the role has to invent**, not by how important it sounds — a role reading rules off a good pack is doing lookup, a role that must imagine an attack nobody wrote down is doing the hard thing.

| Role | Tier | Why |
| --- | --- | --- |
| `adversary` | **top** | Has to invent the attack. In trial it chained a push to `staging` → auto-deploy → a prod rollback with a `../..` path to serve an attacker's tree from prod. Nothing in any pack described that. |
| `operator` | **top** | Has to hold the whole failure surface at once and know what the shell actually does — e.g. that bash elides the fork for a lone simple command but not for a `cd && cmd` list, which is the entire probe-leak bug. |
| `prover` | **top** | Choosing *which* mutation is worth making, and explaining why a survivor survived, is judgement. Its cost is mostly tool calls (it runs suites repeatedly), so a lower tier saves little and loses the insight. |
| `standards` | **mid** | Mostly "does this line breach that written rule". The pack does the thinking; the model does the matching. |
| `spec` | **mid** | A requirement-by-requirement walk. Escalate to **top** when there is no pack, or the spec is a long PRD with interacting acceptance criteria. |
| `steward` | **mid** | Checklist-driven against the pack. Escalate to **top** for payments, consent defaults, or anything where the answer is "it depends". |
| refute pass | **top**, and **never below the tier of the reviewer that produced the finding** | See below. |

**Do not economise on the refute pass.** It is the only stage that *removes* findings. The failure modes are not symmetric: a weak finder misses something, which shows up as a thin report someone can notice; a weak refuter deletes something already found, and nobody ever learns it existed. Combined with the split uncertainty defaults, a cheap refuter is the single most effective way to make this system quietly worse while it appears to be working. It must also differ from the producing reviewer's model — same model, same blind spot, so it re-derives the original reasoning and agrees with itself.

**Escalation rules.**

- **Hotfix → every role on top tier.** Same argument as the full squad: highest blast radius, least time, no staging net.
- **A mid-tier role that reports `dropped: n more` was saturated.** Re-run that one role at top tier before trusting its five. Truncation is the signal that the cheap tier hit its ceiling.
- **No pack matched → top tier for everyone.** Mid tier is only justified when a pack is carrying the reasoning; with no pack the model is doing it unaided.

**Where the real saving is.** Model tier is the smaller lever. The team sheet is the bigger one — a typical UI diff plays three roles, not six, and that halves the run regardless of tier. Tune the pack globs before tuning the models.

**Depth.** Default is the deep run: full tiers, refute pass on. `/five-a-side quick` drops every role to mid tier and **skips the refute pass** — findings come through unfiltered, so a quick run is noisier, never quieter. That is the correct trade for a work-in-progress sanity check, and it is not acceptable on a PR.

If a named model is unavailable in the session, inherit the parent's model and say so in the report rather than silently downgrading.

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
- `spec` with no locatable issue/PRD still plays, and reports `no spec available` as its only finding.

Announce the team sheet before fanning out: which roles play, which packs matched, and why anyone is benched. A benched reviewer is a deliberate decision the user can overrule.

### 5. Fan out

One message, one `Agent` call per playing role, `agentType` general-purpose. Each prompt contains:

- The diff and log commands from step 1 (the **commands**, not the diff text — the subagent runs them itself).
- The full text of `references/<role>.md`.
- The `## <role>` sections of every matched pack, pasted in full. The subagent has no other access to them.
- **For `standards` and `spec` only**: the repo-context block from step 2.
- The spec source for `spec` (issue number to `gh issue view`, or a path).
- **Its output path**: `<scratch>/five-a-side/<role>.md`. **`<scratch>` must be outside the repo working tree.** Reports written inside it are picked up by repo-wide formatters and linters — `prettier --check .` and friends do not care that a file is untracked — so the first commit after a review fails on the review's own artifacts.

Set `model` on each call per *Model tiers* above, and record the tier each role ran at — the report must state it, because a finding's absence means something different at mid tier than at top.

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

### 7. Challenge the blocking findings

**Deduplicate first.** Several reviewers reaching the same underlying defect from different briefs is the system working — but it is one claim, not four, and challenging it four times wastes the pass and produces four verdicts on one line of code. Collapse blocking findings that name the same root cause into a single claim, listing which roles reached it. **Independent convergence is evidence: say so in the report, and give the merged claim one challenge, not none.**

Then one `Agent` call per **distinct** blocking claim, prompted to **refute**:

> Here is a review finding on this diff: `<finding>`. Your job is to refute it. Read the actual code at that location and the rule it cites. Return `REFUTED: <why>` if the finding is wrong, misreads the code, or rests on a rule that does not say what it claims — or `STANDS: <the one-line reason it is real>`. `<default-clause>`

**The uncertainty default is not the same for every role.**

- `adversary` and `steward` → *"When genuinely uncertain, return `STANDS`."* A false positive costs one argument. A suppressed exploit or an unlawful data capture costs a great deal more — and those are exactly the finding types where certainty is hardest to reach, so a REFUTED-on-doubt default systematically discards the most valuable findings the squad produces.
- every other role → *"When genuinely uncertain, return `REFUTED`."*

**Run the challenge on a different model from the one that produced the finding** (set `model` on the Agent call). A challenger sharing the reviewer's model shares its blind spots, so it mostly re-derives the original reasoning and agrees with itself. This is the one point in the pipeline where independence is worth paying for.

**A third verdict: `STANDS — FIX WRONG`.** Refutation is not binary. A challenger may confirm the defect while establishing that the proposed remedy is wrong — the wrong file, the wrong repo, a mitigation that already exists elsewhere. Observed: a finding correctly identified a stale published policy but sent the fix to a repo whose sync pipeline is not built yet. Record the correction alongside the finding; a right diagnosis with a wrong prescription still wastes someone's afternoon.

**Silence fails safe.** A challenger that returns no verdict — idle, dead, or empty — leaves the finding **`block`, unchanged**. Retry once; if the second attempt is also silent, stop and mark the finding `unchallenged` in the report. Never read an absent verdict as consent to demote. This is the opposite of the fan-out's rule and deliberately so: there, a missing report means work was not done, so the run is `INCOMPLETE`; here, a missing verdict would *delete* work already done. Deleting a finding requires an affirmative refutation, never the absence of one.

Accept that failing safe has a cost — an unchallenged weak finding stays at `block` and someone must argue it down by hand. That is the correct side to err on: a wrongly-kept finding costs one conversation, a wrongly-deleted one costs whatever it was about.

`REFUTED` findings are demoted to `note` with the refutation attached, not deleted — the user still sees them and can disagree. This costs one cheap agent per distinct blocker and is what stops plausible-but-wrong findings reaching the user.

### 8. Wenger's report

```
## Team sheet
Played: standards (mid), spec (mid), prover (top)
Benched: adversary, operator, steward (no matching pack section)
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

**Human acknowledgement threshold.** When the diff touches **payments, authentication or authorisation, database migrations, outbound messaging, or legal/policy content**, append:

```
HUMAN ACK REQUIRED — <reason>. A named person must read this report before merge.
```

This is appended *regardless of the decision line*, including on `CLEAR TO MERGE`. These five areas are the ones where a mistake is expensive, slow to detect, and hard to reverse, and a clean automated review is not sufficient grounds to skip a person on them.

The skill only states the requirement. For the marker to mean anything the gate must **fail** on it unless a second, separately-applied signal says a named person acted — a `human-ack:confirmed` label or a required approving review. A gate that prints a notice and exits zero leaves the marker riding through untouched, which is worse than not emitting it: it reads as a control while being decoration. And note the author writes the body, so this constrains an honest author, not a determined one.

## Called by another skill

`implement-issues` invokes this as its review gate. When called that way:

- The caller supplies the fixed point (the issue branch's merge-base), the worktree path, the issue number as the spec source, and its own scratch dir.
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

- **Same model on both sides.** Builder and reviewers are separate agents, but one model with one set of blind spots. Five roles produce five prompts over one prior, not five independent judgements. The model-diverse refute pass narrows this at one point; it does not remove it.
- **Diff-scoped, partially.** Step 2 hands `standards` and `spec` the surrounding context, which covers recent overlapping work and the changed modules' dependents. What it still will not catch is architectural drift with no textual trace — a pattern quietly abandoned, a boundary eroded over months. Those need a human or a deliberate audit, not a diff review.
- **Packs are the ceiling.** Every reviewer is exactly as good as the rules it was handed. An unwritten rule is an unreviewable one.
- **Agents go silent.** Observed across two trial runs: reviewers and challengers both sometimes finish without returning anything, and not uniformly across models. Every stage therefore has an explicit rule for absence — `DID NOT REPORT` in the fan-out, `unchallenged` in the refute pass — and neither ever reads as approval. If a run reports neither, the orchestrator skipped a check.
- **Convergence can be correlated.** Roles sharing a model can reach the same wrong conclusion and look like corroboration. Cross-model challenge is what distinguishes agreement from a shared blind spot; a finding confirmed only by same-model roles is weaker than its vote count suggests.

## Adding a repo

Nothing in this skill is repo-specific, so onboarding a repo is only: write `.claude/five-a-side/packs/*.md` for its domains. See [`references/pack-format.md`](references/pack-format.md). The five roles do not change; the rules they read do.
