# AGENTS.md — organisation agent skills

This repository is the canonical organisation source for the reusable build and
review skills listed in [README.md](README.md). The skill directories at the
repository root are authoritative; `.agents/skills/` contains discovery
symlinks only.

The skills must remain usable by both Claude Code and Codex. Keep product rules,
brand systems, deployment targets, and repository-specific review packs in the
consuming repository. Translate harness-specific invocation syntax and model or
tool names without changing the workflow's behavioural contract.

Never hand-edit a vendored copy in a consuming repository. Change the skill
here, merge it through a pull request to `main`, then re-vendor the merged commit
and refresh that repository's provenance manifest.

Run `python -m unittest discover -s tests -v` before committing.
