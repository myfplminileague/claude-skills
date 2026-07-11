# claude-skills

A collection of [Claude Code](https://claude.com/claude-code) skills — reusable, model-invocable workflows that extend what Claude can do in the terminal. Each skill lives in its own directory with a `SKILL.md` (name, description, and instructions) plus any supporting reference files.

## Skills

| Skill | What it does |
| --- | --- |
| [`debrief-a-call`](debrief-a-call/SKILL.md) | Turn raw impressions after a meeting into a structured summary — asks deep follow-up questions one at a time, then captures the user's thinking plus next steps and action items. |
| [`next-batch`](next-batch/SKILL.md) | Triage front-end for `/implement-issues`: pick and prepare the next buildable batch of GitHub issues, check dependencies and in-flight work, and propose a build order. |
| [`implement-issues`](implement-issues/SKILL.md) | Orchestrate end-to-end implementation of GitHub issues — dependency-ordered parallel builders (TDD), two adversarial review-and-fix cycles, then one PR per issue. |
| [`ship`](ship/SKILL.md) | Merge-and-deploy runbook for open PRs — watch CI, merge in dependency-safe order, run migrations, watch the deploy, smoke-check, then clean up branches. |
| [`tdd`](tdd/SKILL.md) | Test-driven development with the red-green-refactor loop, plus references on mocking, interface design, deep modules, and refactoring. |

## Installation

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/sarinsaurabh/claude-skills.git
```

Then copy or symlink the skills you want into `~/.claude/skills/` (personal) or your project's `.claude/skills/` directory. Claude Code discovers each skill by its `SKILL.md` and invokes it by name or when the described trigger matches.

## Structure

```
claude-skills/
├── debrief-a-call/SKILL.md
├── next-batch/SKILL.md
├── implement-issues/SKILL.md
├── ship/SKILL.md
└── tdd/
    ├── SKILL.md
    ├── mocking.md
    ├── interface-design.md
    ├── deep-modules.md
    ├── refactoring.md
    └── tests.md
```

## License

MIT
