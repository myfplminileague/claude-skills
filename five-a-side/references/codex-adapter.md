# Codex adapter

Use this adapter only when the five-a-side workflow is running in Codex. The
planner, repository packs, review budgets, role scopes, output format, and final
verdict remain unchanged.

## Model tiers

- Treat `opus` as the strongest available general coding and reasoning model.
- Treat `sonnet` as the balanced agentic coding model.
- Preserve the reasoning effort pinned in `models.yml` when the runtime exposes
  an effort control.
- Never substitute a lightweight model for a role whose policy excludes it.
- If the required capability is unavailable, bench the role and return
  `INCOMPLETE`; do not claim parity by silently changing the policy.

Record the actual Codex model and effort in the report, alongside the policy
tier it fulfilled.

## Agents and tools

- Treat `five-a-side-<role>` as a role brief, not as a required Claude agent
  identifier. Dispatch a read-only Codex subagent with the corresponding
  `references/<role>.md` brief and matched repository-pack section.
- Translate `Read`, `Glob`, and `Grep` to read-only filesystem/search tools, and
  `Bash` to the available terminal tool. Reviewers remain read-only even if the
  runtime offers write tools.
- Keep each reviewer independent. Do not pass another reviewer's conclusion to
  it before adjudication.

## Paths and invocation

In a consuming repository, the canonical vendored paths remain
`.claude/skills/five-a-side/` and `.claude/five-a-side/packs/`; Codex can execute
those scripts and read those packs directly. In this organisation repository,
resolve scripts relative to the skill directory when the vendored path is
absent.

Claude may invoke the workflow as `/five-a-side`; Codex may invoke it as
`$five-a-side` or by naming the skill. These are equivalent entrypoints.
