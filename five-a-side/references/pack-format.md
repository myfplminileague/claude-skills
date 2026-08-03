# Pack format

A pack contains one repository domain's review rules and the policy that selects them. The deterministic
planner and CI both read its frontmatter, so do not maintain a separate risk regex.

Location: `.claude/five-a-side/packs/<domain>.md`.

## Shape

```markdown
---
domain: messaging
lane: critical
reviewers: ["standards", "spec", "adversary", "operator", "prover", "steward"]
human_ack: ["outbound messaging and consent"]
human_ack_exempt_paths: ["backend/notifications/**/tests/**"]
paths:
  - "backend/notifications/**"
  - ".github/workflows/whatsapp_campaign.yml"
---

# messaging

One paragraph naming the domain and its source of truth.

## standards
- One checkable rule per line.

## spec
- What faithful delivery means here.

## adversary
- Omit when this reviewer is absent from `reviewers`.
```

Required frontmatter:

- `domain`: unique and identical to the filename stem.
- `lane`: `standard` or `critical`.
- `reviewers`: JSON-compatible inline array using canonical role slugs.
- `paths`: one or more repository-relative globs.
- `human_ack`: optional JSON-compatible array of reasons; default `[]`.
- `human_ack_exempt_paths`: optional JSON-compatible array of globs; default `[]`. A diff that matches a
  pack only through these paths keeps the pack's lane and reviewers but does not require acknowledgement.
  If any matched path is not exempt, acknowledgement remains required.

Run:

```bash
python3 .claude/skills/five-a-side/scripts/review_plan.py \
  --packs-dir .claude/five-a-side/packs --validate
```

## Design rules

- **Frontmatter is policy.** The planner selects the highest matched lane, unions reviewers, and aggregates
  acknowledgement reasons. CI must consume the same output.
- **Exempt acknowledgement, not review.** Use `human_ack_exempt_paths` for test or fixture paths that still
  deserve the pack's review but cannot perform the irreversible action named by `human_ack`.
- **A reviewer needs a section.** Every slug in `reviewers` must have a non-empty `## <role>` section. Do not
  add placeholder sections or reviewers.
- **One rule per line, checkable against a diff.** Link to existing documentation instead of duplicating it.
- **Cite incidents.** They explain why recurring friction earns its place.
- **Name exclusions.** State when CI already owns a check so reviewers do not spend findings on it.
- **Keep globs narrow.** Backtest them against recent merges. A broad standard pack costs calls; a broad
  critical pack also costs top-tier models and acknowledgement.
- **Use overlapping packs deliberately.** A broad standard design-system pack can overlap a narrow critical
  consent pack; the latter raises only the relevant files.

## Suggested domains

| Domain | Typical lane and roles |
| --- | --- |
| Design system | standard: standards, spec, prover |
| API/auth | critical: add adversary, operator, steward where consent/data applies |
| Data/migrations | critical: standards, spec, adversary, operator, prover |
| Pipeline | critical for unattended/irreversible paths; otherwise standard |
| CI/deploy | critical: standards, spec, adversary, operator, prover |
| Legal publication | critical: standards, spec, steward; usually no prover |
| Review tooling | standard: standards, spec, prover |

When a finding nobody agrees with recurs, narrow the rule or glob. When an incident occurs that a role could
have caught, add the smallest checkable rule and incident reference.
