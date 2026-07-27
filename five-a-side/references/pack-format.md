# Pack format

A **pack** is one domain's rules, written once per repo, read by whichever reviewers the domain engages. Packs are what make five fixed reviewers cover a whole stack: the skill knows the five questions, the pack knows the answers for this repo.

Location: `.claude/five-a-side/packs/<domain>.md`, in the repo being reviewed.

## Shape

```markdown
---
domain: design-system
paths:
  - "src/components/**"
  - "src/app/**/*.tsx"
  - "src/app/globals.css"
---

# design-system

One paragraph: what this domain is and where its source of truth lives.

## standards
- Rules, one per line, each one checkable against a diff.

## spec
- What "faithful" means in this domain.

## adversary
- Omit this section entirely if the domain has no attack surface.

## operator
- ...

## prover
- ...
```

## Rules for writing packs

- **A section's presence is a trigger.** `adversary` and `operator` only play when a matched pack has a non-empty section for them. An empty or omitted section benches that reviewer — that is the intended way to keep a UI-only PR from being reviewed for rollback safety. Do not write a placeholder section to be polite.
- **One rule per line, checkable against a diff.** "Never hardcode Tailwind colours — use the semantic tokens in `globals.css @theme`" is checkable. "Write clean components" is not, and will produce noise in every review forever.
- **Link, don't restate.** If `docs/security/code-requirements.md` already says it, the pack line is a pointer plus the one-line summary. A pack that duplicates a doc will drift from it, and the reviewer will then cite a rule that no longer exists.
- **Cite the incident where there is one.** A rule that carries "we had a nine-day silent outage because of this" gets weighted correctly by the reviewer and survives the next person who wants to delete it.
- **Say what is out of scope.** A pack line that reads "ignore X, CI enforces it" saves a wasted finding on every future review.
- **Globs are the whole trigger mechanism.** Too broad and every reviewer plays on every PR; too narrow and a real change is reviewed by nobody. Check yours against `git diff --name-only` on a few recent merges.

## Suggested domains

Not prescriptive — split by *whose rules they are*, not by directory:

| Domain | Typically covers |
| --- | --- |
| `design-system` | tokens, component primitives, icons, a11y, responsive |
| `frontend-app` | routing, server/client boundary, data fetching, state |
| `api` | route handlers, auth, middleware, request validation |
| `data` | schema, migrations, RLS, query patterns |
| `pipeline` | batch jobs, ingestion, scheduling, retries |
| `ci-deploy` | workflows, deploy scripts, release process |
| `content-legal` | vendored or generated prose, sync invariants |

## Keeping packs honest

A pack is a prompt, not a wiki — the same discipline `CLAUDE.md` gets. When a review produces a finding nobody agrees with, the fix is usually to delete or narrow a pack line, not to argue with the reviewer. When an incident happens that a reviewer could have caught, add the line.
