---
name: ez-cv
description: >
  Interview-driven resume builder that turns a conversation into a personalized,
  reusable resume-generation skill. EZ-CV asks one question at a time until it has
  enough verified detail, then scaffolds a private per-user skill that renders a
  terminal-themed HTML resume, an AI-assistant one-pager, ATS-clean Markdown, and
  LaTeX/PDF — full and one-page — with humanized prose and automatic keyword/metric
  bolding. Use when the user says "build my resume", "ez-cv", "make me a resume",
  "resume from scratch", "I need a resume", or "set up my resume skill".
---

# EZ-CV

Turn a guided interview into a finished resume **and** a personal resume skill the
user keeps. EZ-CV does the asking; once it has enough verified material it writes a
`profile.json` and scaffolds a per-user skill (under `~/.cursor/skills/` or a folder
the user picks) that regenerates every format on demand from that one file.

Salient features it delivers to the end user:
- **ATS-friendly, high-scoring** Markdown + LaTeX/PDF (single-column, plain-unicode,
  standard headings, quantified bullets).
- **Humanized prose** — a deterministic AI-fingerprint scan that must pass before
  anything is called done.
- **A new kind of HTML resume** — a scrolling terminal-themed page plus an
  AI-assistant chat-UI one-pager, both self-contained.
- **One source of truth** — edit `profile.json`, re-run, and all outputs update.

## When to Use

Trigger when the user says: "build my resume", "ez-cv", "make me a resume",
"resume from scratch", "I have no idea where to start", or "set up my resume skill".

## Hard Rules (non-negotiable)

- **No hallucination, no assumptions.** Never invent a job, metric, tool, date, or
  award. If you do not have it from the user, you do not write it.
- **Ask, do not guess.** When a field is unknown, ask. There is no cap on questions.
- **One question (or one tight batch) at a time.** Do not dump a 30-question form.
- **Every claim is tagged** `verified` / `estimate` / `placeholder`. Estimates get a
  `~` and explicit user sign-off. Placeholders are surfaced loudly, never shipped silently.
- **Numbers or it didn't happen.** Push every achievement toward a metric, but only
  a metric the user confirms.
- **The user owns the data.** Write files only where the user agrees. Never push to
  any remote or host anything without explicit confirmation.

## Process

### Phase 1 — Interview (gather, don't assume)
1. Run `python3 scripts/interview.py` to load the question bank (sections: identity
   & contact, target role/JD, each work experience, projects, skills, education,
   certifications, awards, speaking, links, theme).
2. Ask **section by section**, one focused question or a small batch at a time. After
   each answer, ask the natural follow-up that pushes toward a number or a mechanism
   ("how much faster?", "how did you do it?", "how many people use it?").
3. For every answer, record provenance. If the user says "I don't know / skip", mark
   it `placeholder` and move on — do not fill it in yourself.
4. Continue until the **Readiness Gate** (below) is satisfied. Do not proceed early.

### Phase 2 — Write the profile
1. Assemble answers into a `profile.json` that matches `template/data/profile.schema.json`.
2. Wrap the few highest-signal phrases per bullet in `**double asterisks**`; let the
   renderer auto-bold numeric metrics. Do not over-bold.
3. Keep titles, companies, and dates verbatim from what the user gave you.

### Phase 3 — Scaffold the personal skill
1. Run `python3 scripts/scaffold.py --name "<Full Name>" [--dest <dir>] --profile <path-to-profile.json>`.
   This copies `template/` into a new per-user skill, drops in the `profile.json`,
   personalizes the skill name, and renders all outputs once.
2. Default destination is `~/.cursor/skills/<slug>-resume`. Confirm the path with the
   user before writing if they have a preference.

### Phase 4 — Critique and humanize (gate)
1. From the scaffolded skill, run `python3 scripts/humanize_scan.py`. Fix every hard
   FAIL in `profile.json` and re-render. Re-run until it prints `RESULT: PASS`.
2. Do a fresh-eyes pass with `reference/critique-framework.md`. Tighten weak bullets
   with the user; never invent to fill a gap (`reference/gap-coverage-plan.md`).

### Phase 5 — Render, verify, hand off
1. Build all formats (the scaffold did the first pass; re-run after edits):
   `build_html.py`, `build_html.py --compact`, `build_html_ai.py`, `build_text.py`,
   `build_text.py --compact`.
2. PDF: `cd output && tectonic <slug>_resume.tex` (and the `_onepage` one). Confirm the
   one-pager is exactly one page before sharing.
3. Open the outputs for the user. Tell them: edit `profile.json`, re-run, done.

### Phase 6 — Publish (only on explicit request)
1. For a hostable site, build with `--public` (hides phone, keeps email + links).
2. Only if the user asks to host: create a `<handle>.github.io` repo, add the public
   HTML + PDF + `.nojekyll`, enable Pages, and verify the live URL returns HTTP 200
   before sharing it. Never publish contact details the user did not approve.

## Readiness Gate (do not scaffold before all are true)

- [ ] Identity: name, target role/title, location, email — all `verified`.
- [ ] At least one work experience with company, role, dates, and >=2 quantified bullets.
- [ ] Skills grouped into >=3 categories with real items.
- [ ] Education present (or explicitly waived by the user).
- [ ] Every metric in the profile is `verified` or a `~`-tagged `estimate` the user OK'd.
- [ ] Zero `placeholder` values remain in shipped fields (links/photo may stay placeholder if the user has none).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll infer a reasonable metric from context." | That is fabrication. Ask the user for the real number or mark it `placeholder`. |
| "Their role is X, so they probably used Y." | Probably is not verified. Never add a tool the user did not name. |
| "I'll ask everything in one big form." | Walls of questions get skipped. Ask section by section, one focused ask at a time. |
| "The bullet sounds good, ship it." | "Sounds good" is not the humanize scan. Run `humanize_scan.py` and pass it. |
| "Close enough to one page." | Open the PDF and count pages. One-pager means one page. |
| "I'll round 45.2% to 50%, punchier." | Changing a user's number is fabrication. Use what they said. |
| "They didn't give a date, I'll estimate the year." | Mark it `placeholder` and ask. Dates must be exact. |
| "I'll publish the resume to show it works." | Hosting needs explicit consent. Never push or host without it. |
| "Awards/links are minor, I'll invent plausible ones." | Never invent credentials or URLs. Leave them out or `placeholder`. |
| "The scan flagged a soft warning, ignore it." | Soft warnings are still signals — review before declaring done. |

## Red Flags

- **Writing any field the user did not state** — that is the cardinal failure.
- **Filling a `placeholder` with a guess** instead of asking.
- **Scaffolding before the Readiness Gate is satisfied.**
- **Declaring done without a passing `humanize_scan.py`.**
- **Sharing a one-pager without counting PDF pages.**
- **Sharing a hosted URL without a verified HTTP 200.**
- **Pushing to a remote / enabling Pages without explicit user consent.**
- **Changing a user's number or title to sound better.**

## Verification Checklist

### Interview
- [ ] Every section visited; unanswered fields marked `placeholder`, not invented.
- [ ] Each metric traced to a user statement (`verified`) or a `~` `estimate` they approved.

### Build
- [ ] `humanize_scan.py` prints `RESULT: PASS`.
- [ ] All five render commands ran without error.
- [ ] Full PDF and one-page PDF both compile; one-pager is exactly 1 page (counted).
- [ ] No `placeholder` text remains in shipped fields.

### Publish (only if requested)
- [ ] Built with `--public`; phone absent, email + links present.
- [ ] Live URL(s) verified HTTP 200 before sharing.
- [ ] User explicitly consented to hosting.

## Additional Resources

- `scripts/interview.py` — the question bank the interview follows.
- `scripts/scaffold.py` — clones `template/`, writes `profile.json`, renders outputs.
- `template/` — the per-user skill that gets cloned (renderers, schema, references,
  example profile, and its own SKILL.md).
- `examples/example_profile.json` — a fictional, fully-worked profile to study.
