---
name: two-axis-review
description: DEPRECATED — superseded by five-a-side. Kept only so existing invocations keep working; it now hands off. Use five-a-side directly.
---

# two-axis-review (deprecated)

**Superseded by [`five-a-side`](../five-a-side/SKILL.md). Do not extend this skill.**

Invoke `five-a-side` with the same fixed point the user gave you, and carry on there. Tell the user once, in one line, that two-axis-review has been replaced and they can use `/five-a-side` directly next time. Do not review anything yourself.

## Why it was replaced

Both original axes were **internally referenced** — Standards checked the code against our own docs, Spec checked it against our own issue. A change could pass both and still be wrong, and one did: the atomic-deploy work (frontend #636/#637) conformed to every documented standard and implemented its issue exactly, while containing a leaked probe process holding a port, a `set -e` interaction that skipped rollback entirely, part-built releases that were never collected, a remote command-injection path, and three test assertions that passed against deliberately broken code.

None of that was reachable from either axis. What found it was adversarial red-teaming, running the scripts against a fixture, and mutation-testing the assertions — now the `adversary`, `operator` and `prover` roles.

The two original axes survive as `standards` and `spec`, and the Fowler smell baseline moved to [`five-a-side/references/standards.md`](../five-a-side/references/standards.md) unchanged.

## Removal

Delete this directory once no vendored copy or doc still references it.
