# Organisation agent skills

The repository name is retained for continuity, but these are the
myfplminileague organisation's harness-neutral build and review skills. They are
vendored into consuming repositories and exposed through both `.claude/skills/`
and `.agents/skills/`. Edit the canonical skill here, merge through a pull
request, then re-vendor the merged commit; never hand-edit a consuming copy.

The collection began as an organisation fork of
[sarinsaurabh/claude-skills](https://github.com/sarinsaurabh/claude-skills).
`debrief-a-call` remains excluded because it is personal rather than
organisation policy. Product rules, branding, deployment targets, and review
packs remain local to each consuming repository.

Each skill is a reusable, model-invocable terminal workflow with a `SKILL.md`
and optional scripts or references. Claude Code may invoke a skill as
`/skill-name`; Codex may use `$skill-name` or name it directly. Invocation
syntax does not change the workflow.

## Skills

| Skill | What it does |
| --- | --- |
| [`to-prd`](to-prd/SKILL.md) | Turn the current conversation into a PRD and publish it to the issue tracker. |
| [`to-issues`](to-issues/SKILL.md) | Break a plan, spec or PRD into independently-grabbable issues using tracer-bullet vertical slices. |
| [`next-batch`](next-batch/SKILL.md) | Triage front-end for `implement-issues`: pick and prepare the next buildable batch of GitHub issues, check dependencies and in-flight work, and propose a build order. |
| [`implement-issues`](implement-issues/SKILL.md) | Orchestrate end-to-end implementation with deterministic risk planning, at most one remediation, focused verification, and one PR per issue. |
| [`five-a-side`](five-a-side/SKILL.md) | A risk-budgeted review gate: repository packs select an exempt, standard, or critical lane; model review and mutation testing are bounded and measured. |
| [`ship`](ship/SKILL.md) | Merge-and-deploy runbook for open PRs — watch CI, merge in dependency-safe order, run migrations, watch the deploy, smoke-check, then clean up branches. |
| [`tdd`](tdd/SKILL.md) | Test-driven development with the red-green-refactor loop, plus references on mocking, interface design, deep modules, and refactoring. |
| [`chunk-status`](chunk-status/SKILL.md) | Reconcile a project-plan chunk against reality — issues, merged PRs, deployed app — and propose plan-doc corrections. |
| [`grill-me`](grill-me/SKILL.md) | Interview the user relentlessly about a plan or design until every branch of the decision tree is resolved. |

## Discovery and vendoring

The root skill directories are canonical. This repository's
`.agents/skills/<name>` symlinks let Codex discover them when working in this
checkout. Consuming repositories vendor each selected skill, record its source
commit, and expose that one copy to both harnesses.

```text
canonical organisation repository
  <skill>/SKILL.md
  .agents/skills/<skill> -> ../../<skill>

consuming repository
  .claude/skills/<skill>/   # vendored copy + provenance manifest
  .agents/skills/<skill> -> ../../.claude/skills/<skill>
```

Claude-specific agent definitions and runtime settings may remain under
`.claude/`; Codex translates the same role briefs and workflow requirements
through its own tools. Runtime permissions, credentials, hooks, and model names
must never be copied as if they were portable skill content.

## Structure

```
claude-skills/
├── next-batch/SKILL.md
├── implement-issues/SKILL.md
├── five-a-side/
│   ├── SKILL.md
│   ├── models.yml
│   ├── scripts/
│   │   ├── review_plan.py    # deterministic lane/team selection
│   │   └── review_state.py   # metrics + one-remediation guard
│   └── references/
│       ├── standards.md      # Ødegaard — conventions + Fowler smell baseline
│       ├── spec.md           # Bergkamp — fidelity to the issue/PRD/design
│       ├── adversary.md      # Rice     — authz, injection, secrets, PII, concurrency
│       ├── operator.md       # Raya     — observability, rollback, blast radius
│       ├── prover.md         # Henry    — mutation-test the assertions
│       ├── steward.md        # Mertesacker — sub: consent, retention, a11y, promises
│       └── pack-format.md    # how a repo writes its own rule packs
├── ship/SKILL.md
└── tdd/
    ├── SKILL.md
    ├── mocking.md
    ├── interface-design.md
    ├── deep-modules.md
    ├── refactoring.md
    └── tests.md
```

Rule **packs** are not in this repo — they live in each consuming repo at `.claude/five-a-side/packs/*.md`, because they are that repo's rules. Their frontmatter is the single source for path matching, lane, reviewers, and human acknowledgement; both Claude and CI call `review_plan.py`. The skill is org-wide and identical everywhere, while packs remain local. See [`five-a-side/references/pack-format.md`](five-a-side/references/pack-format.md).

## License

MIT
