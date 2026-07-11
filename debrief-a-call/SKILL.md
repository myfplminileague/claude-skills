---
name: debrief-a-call
description: Debrief a call or meeting by capturing the user's impressions and reflections, asking deep structured follow-up questions one at a time, then producing a summary that preserves their thinking plus next steps and action items. Use when the user wants to debrief, recap, process, or write up notes from a call, meeting, conversation, or interview — especially when they have impressions but incomplete notes.
---

# Debrief a Call

Turn raw impressions after a meeting into a structured summary that captures the user's actual thinking — not just what was said, but what they took away.

## Workflow

### 1. Let them dump first
Open with a light prompt and let the user ramble freely. Do **not** interrupt or question yet.

> "Tell me about the call — who was it with, what was it about, and whatever's on your mind. Ramble freely, and paste any notes you took if you have them. I'll organize it after."

Explicitly invite both: their verbal impressions **and** any raw notes to paste. Listen for: participants, topic/purpose, decisions, tensions, surprises, the user's reactions and gut feelings.

### 2. Ask deep questions — ONE AT A TIME
This is the core of the skill. After the dump, ask probing questions **one at a time** and wait for each answer before the next. Never batch questions. Adapt based on what they've already said — skip what's covered, dig into what's thin.

Set expectations up front: tell the user this'll be a handful of questions (aim for ~5–8, more only if they're engaged) and that they can say **"done"** anytime to jump straight to the summary.

Draw from these angles (pick what's relevant, follow the energy):
- **Purpose & outcome** — What was this meeting trying to achieve? Did it?
- **The unsaid** — What was left unspoken? Any subtext, hesitation, or politics?
- **Surprises** — What caught you off guard, confirmed, or challenged your assumptions?
- **Stakeholder read** — Where does each person actually stand? Who's bought in, who isn't?
- **Your reaction** — What's your honest gut feeling now? Excited, worried, skeptical?
- **Decisions & open loops** — What got decided? What's still unresolved?
- **Risks & blockers** — What could derail this? What are you uncertain about?
- **Next steps** — Who owes what, by when? What's *your* move?

Ask follow-ups when an answer is vague or interesting ("You said it felt off — what specifically?"). Keep going until the user signals they're done or the well runs dry. Aim for depth over coverage.

### 3. Relay understanding back, then confirm — ALWAYS
This gate is **mandatory** — never skip straight to saving. Once questioning is done, play your understanding back to the user before writing anything to disk:

> "Great — I've gone through the questions. Here's my understanding of the call: [tight recap of what happened, their read, the key risks, and the action items]. **Do you want to change or add anything before I save it?**"

Keep the recap tight but complete — hit the reflections, risks, and every action item so they can catch a misread or a missing to-do. Wait for their explicit go-ahead. If they correct something, fold it in and re-confirm the changed part.

In the same step, settle the three things needed to save (so there's no second round of questions after the go-ahead):
- **Project** — infer from the debrief; if unclear, ask, and offer existing folders by listing `~/Documents/meetings/`.
- **Topic** — propose a short kebab-case topic and let them correct it.
- **Meeting date** — assume today unless they say the call was on another day.

### 4. Save the summary
Write the summary to `~/Documents/meetings/<project>/<yymmdd>-<topic>.md`.

- **One folder per project** under `meetings/` (e.g. `meetings/woofendale/`, `meetings/jimis-burger/`). Create it if it doesn't exist.
- File name: `<yymmdd>` meeting date + short kebab-case topic, e.g. `260618-q3-influencer-strategy.md`.
- **Before writing, check if the file already exists.** If it does, don't overwrite silently — append a numeric suffix (`260618-q3-influencer-strategy-2.md`) or ask whether to overwrite.

Write a summary that **preserves the user's voice and judgment**, not a neutral transcript. Use this structure:

```markdown
# Debrief: [Meeting] — [Meeting date]

**Who:** [participants]
**Purpose:** [why it happened]

## What happened
[Key topics, decisions, and discussion — concise]

## My read / reflections
[The user's impressions, gut feelings, and interpretation — first person, in their voice]

## Surprises & signals
[What was unexpected, subtext, where people stand]

## Open questions & risks
[Unresolved items, uncertainties, things to watch]

## Next steps & action items
- [ ] [Action] — [owner] — [due date if known]
```

### 5. Offer to update the project to-do (optional)
After saving, ask: **"Want me to add these action items to the HardSkills running to-do?"** (name the actual project). Only proceed if they say yes.

Each project folder keeps a standing `TODO.md` at `~/Documents/meetings/<project>/TODO.md` — the single rolling list of open items for that project:
- **Newest on top.** Add this debrief's open action items to the top, grouped under a dated heading (`## 260616 — Microsoft co-sell event`) so each item traces back to its source call.
- **Don't delete completed work — cross it out.** Mark finished items with strikethrough (`- [x] ~~old task~~`) so the history stays visible.
- Before adding, read the existing `TODO.md` (if present) and check whether any open item is now done based on this debrief — if so, strike it through. Create the file if it doesn't exist.
- Confirm the path after writing.

## Rules
- **One question at a time.** This is non-negotiable — it's what gets the full picture out.
- **Always relay your understanding back and get explicit confirmation before saving** (Step 3). Never write to disk without it.
- Capture *their* thinking and conclusions, not a sanitized minutes doc.
- Use the user's own words and phrasing in the reflections section.
- **Don't fabricate reflections.** Only capture impressions the user actually voiced. If you surface a genuine inference, label it "(my read)" rather than asserting it as theirs.
- Distinguish facts (what happened) from their interpretation (their read).
- If they have notes, fold them in — but the impressions are the priority.
- Dates use `yymmdd` and refer to the **meeting** date, not the day you write the file.
- Save to `~/Documents/meetings/<project>/<yymmdd>-<topic>.md`; confirm the path after writing.
