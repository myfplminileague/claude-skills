# claude-skills

myfplminileague org fork of [sarinsaurabh/claude-skills](https://github.com/sarinsaurabh/claude-skills) — the org's canonical build-workflow skills. Vendored into `my-fml-frontend`, `my-fml-backend`, and `my-fml-business-docs` under `.claude/skills/`; edit HERE, then sync to the repos (never hand-edit the vendored copies). `debrief-a-call` is excluded (personal skill). Org conventions: PRs target the repo's default branch (frontend default = `staging` during the V2 build); no Co-Authored-By/Claude attribution on commits.

Upstream description: A collection of [Claude Code](https://claude.com/claude-code) skills — reusable, model-invocable workflows that extend what Claude can do in the terminal. Each skill lives in its own directory with a `SKILL.md` (name, description, and instructions) plus any supporting reference files.

## Skills

| Skill | What it does |
| --- | --- |
| [`to-prd`](to-prd/SKILL.md) | Turn the current conversation into a PRD and publish it to the issue tracker. |
| [`to-issues`](to-issues/SKILL.md) | Break a plan, spec or PRD into independently-grabbable issues using tracer-bullet vertical slices. |
| [`next-batch`](next-batch/SKILL.md) | Triage front-end for `/implement-issues`: pick and prepare the next buildable batch of GitHub issues, check dependencies and in-flight work, and propose a build order. |
| [`implement-issues`](implement-issues/SKILL.md) | Orchestrate end-to-end implementation with deterministic risk planning, at most one remediation, focused verification, and one PR per issue. |
| [`five-a-side`](five-a-side/SKILL.md) | A risk-budgeted review gate: repository packs select an exempt, standard, or critical lane; model review and mutation testing are bounded and measured. |
| [`ship`](ship/SKILL.md) | Merge-and-deploy runbook for open PRs — watch CI, merge in dependency-safe order, run migrations, watch the deploy, smoke-check, then clean up branches. |
| [`tdd`](tdd/SKILL.md) | Test-driven development with the red-green-refactor loop, plus references on mocking, interface design, deep modules, and refactoring. |
| [`chunk-status`](chunk-status/SKILL.md) | Reconcile a project-plan chunk against reality — issues, merged PRs, deployed app — and propose plan-doc corrections. |
| [`grill-me`](grill-me/SKILL.md) | Interview the user relentlessly about a plan or design until every branch of the decision tree is resolved. |

## Installation

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/sarinsaurabh/claude-skills.git
```

Then copy or symlink the skills you want into `~/.claude/skills/` (personal) or your project's `.claude/skills/` directory. Claude Code discovers each skill by its `SKILL.md` and invokes it by name or when the described trigger matches.

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
