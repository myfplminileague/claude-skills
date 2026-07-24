---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

The issue tracker is the GitHub project attached to the repo you are working in.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes an issue reference (issue number, URL, or path) as an argument, fetch it from GitHub with `gh issue view <number> --json number,title,body,labels,comments` and read its full body and comments. Note its priority label so child issues can inherit it.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

### 3. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

When the source material is a chunk/epic/PRD whose implementation will drift from the written spec, include one **documentation-delta slice**: a doc-only companion that lands at chunk end and reconciles the project docs (plan, architecture, runbook, ops-handover checklist) with what actually shipped. It is filed as a normal issue but is doc-only (no test surface), typically has no hard blockers, and should be worked only after the build slices merge so it describes reality, not intent.

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?
- For chunk/epic-scale plans (not tiny ones), is a documentation-delta slice wanted for this breakdown?

Iterate until the user approves the breakdown.

### 5. Publish the issues to GitHub

For each approved slice, create a new issue with `gh issue create --title "..." --body "..." --label "..."`. Use the issue body template below.

Labels to apply on each child issue:
- `ready-for-agent` (these issues are ready for AFK agents unless instructed otherwise)
- The same priority label as the parent issue (if a parent exists). If there is no parent, ask the user which priority label to apply once for the whole batch.

Publish issues in dependency order (blockers first) so you can reference real issue numbers (e.g. `#42`) in the "Blocked by" field of dependent issues.

If the repo has a GitHub Project attached, add each created issue to it with `gh project item-add`.

<issue-template>
## Parent

A reference to the parent issue on the issue tracker (if the source was an existing issue, otherwise omit this section).

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not layer-by-layer implementation.

Avoid specific file paths or code snippets — they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it here and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Testing

State which layer owns each behavior (unit / integration / route-wiring / component / store), so the builder doesn't default everything to the most expensive tier. DB/HTTP-tier tests only for what lower tiers can't observe (persistence, constraints, concurrency, wiring); validation matrices and pure logic are unit-owned with at most one integration wiring exemplar. Follow the repo's testing conventions doc if one exists. Omit this section only when the slice has no test surface.

## Blocked by

- A reference to the blocking ticket (if any)

Or "None - can start immediately" if no blockers.

</issue-template>

### 6. Wire native GitHub dependencies

The "Blocked by" prose in the body is human-readable context. After all issues exist, also create the **native GitHub issue dependencies** so the relationships render in the GitHub UI and tooling (e.g. `/implement-issues`) can derive the build order from the API instead of parsing prose.

Native dependencies are keyed on the issue's **database id** (an integer), not its number. For each blocking relationship, fetch the blocker's id and POST it to the blocked issue's `blocked_by` list:

```sh
# get the blocker's database id (integer)
BLOCKER_ID=$(gh api repos/{owner}/{repo}/issues/<blocker-number> --jq '.id')

# register: <blocked-number> is blocked by <blocker-number>
gh api --method POST repos/{owner}/{repo}/issues/<blocked-number>/dependencies/blocked_by -F issue_id=$BLOCKER_ID
```

Notes:
- Use `-F` (not `-f`) so `issue_id` is sent as an integer — a string is rejected with HTTP 422.
- One POST per edge; an issue blocked by N issues needs N calls.
- After wiring, verify with `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by --jq '[.[].number]'` and confirm it matches each issue's "Blocked by" section.

Do NOT close or modify any parent issue.
