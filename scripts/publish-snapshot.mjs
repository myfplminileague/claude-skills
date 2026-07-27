#!/usr/bin/env node
//
// Refresh the public snapshot at adigunners/agent-skills from this canonical repo.
//
// The public copy is deliberately NOT a mirror: it is generalised, because this
// repo's skills carry incident history and product decisions that should not be
// published. A straight copy would undo that, and doing it by hand each time is
// how the two silently diverge in the wrong direction — someone re-scrubs from
// memory, misses a line, and internal detail ships.
//
// So the scrub lives here, in the private repo, as code. Every substitution
// asserts its anchor exists, so an upstream rewording fails loudly rather than
// silently publishing the un-scrubbed line.
//
// Usage:  node scripts/publish-snapshot.mjs <path-to-agent-skills-checkout>

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const dest = process.argv[2];
if (!dest || !existsSync(dest)) {
  console.error("usage: node scripts/publish-snapshot.mjs <path-to-agent-skills-checkout>");
  process.exit(1);
}

const SRC = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", "five-a-side");
const OUT = path.join(dest, "five-a-side");

// Files the public repo owns and this script must never overwrite.
const PRESERVE = ["README.md", "examples"];

/**
 * Generalisations applied on publish. Each is [file, from, to].
 * `from` must be present or the run aborts — a silently-skipped scrub is the
 * failure mode that publishes internal detail.
 */
const SCRUB = [
  [
    "SKILL.md",
    "Every change landing on a **protected branch** gets reviewed — in this org that is `staging` and `main` on the frontend, `main` on the backend. `staging` is not a lower bar: it is the first branch that actually deploys, so it is the first place a defect becomes real.",
    "Every change landing on a **protected branch** gets reviewed. Where a repo has both an integration branch and a release branch, the integration branch is not a lower bar: it is the first branch that actually deploys, so it is the first place a defect becomes real.",
  ],
  [
    "SKILL.md",
    "- A hotfix targets `main`, so a bad one takes the live site down — the highest blast radius any change in this org has.",
    "- A hotfix targets the release branch, so a bad one takes the live site down — the highest blast radius any change has.",
  ],
  [
    "references/adversary.md",
    "In this org, anything with a `NEXT_PUBLIC_` prefix is public by definition — check nothing sensitive acquired that prefix.",
    "Framework build-time prefixes (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`) make a value public by definition — check nothing sensitive acquired one.",
  ],
  [
    "references/operator.md",
    "and a nine-day silent outage in this org started exactly there",
    "a silent outage lasting days usually starts exactly there",
  ],
  [
    "references/steward.md",
    "this org has a standing decision that messaging consent defaults to **off**, and a diff that flips it is a finding regardless of intent",
    "where the project has a standing decision on a default — messaging consent starting **off**, say — a diff that flips it is a finding regardless of intent",
  ],
  [
    "references/prover.md",
    "Three real ones from this org, all of which passed a reading review:",
    "Three real ones, all of which passed a reading review:",
  ],
  [
    "references/pack-format.md",
    'A rule that carries "we had a nine-day silent outage because of this" gets weighted correctly',
    'A rule that carries "we lost nine days of data to this" gets weighted correctly',
  ],
];

// Copy, preserving the public repo's own files.
for (const keep of PRESERVE) {
  const p = path.join(OUT, keep);
  if (existsSync(p)) execFileSync("mv", [p, path.join(dest, `.keep-${keep}`)]);
}
execFileSync("rm", ["-rf", OUT]);
execFileSync("cp", ["-R", SRC, OUT]);
for (const keep of PRESERVE) {
  const stashed = path.join(dest, `.keep-${keep}`);
  if (existsSync(stashed)) execFileSync("mv", [stashed, path.join(OUT, keep)]);
}

for (const [file, from, to] of SCRUB) {
  const p = path.join(OUT, file);
  const s = readFileSync(p, "utf8");
  if (!s.includes(from)) {
    console.error(`\nABORT: scrub anchor missing in ${file}\n  looked for: ${from.slice(0, 90)}…`);
    console.error("The upstream wording changed. Update this script — do not publish unscrubbed.");
    process.exit(1);
  }
  writeFileSync(p, s.replace(from, to));
}

// Belt and braces: nothing identifiable should survive.
const LEAK = /myfplminileague|contabo|msg91|this org|nine-day|NEXT_PUBLIC_ prefix is public/i;
const files = execFileSync("find", [OUT, "-name", "*.md"], { encoding: "utf8" }).trim().split("\n");
const leaked = files.filter((f) => LEAK.test(readFileSync(f, "utf8")));
if (leaked.length) {
  console.error(`\nABORT: identifiable content survived in:\n  ${leaked.join("\n  ")}`);
  process.exit(1);
}

const sha = execFileSync("git", ["rev-parse", "--short", "HEAD"], { encoding: "utf8" }).trim();
console.log(`snapshot refreshed from ${sha}: ${SCRUB.length} scrubs applied, no leaks detected`);
