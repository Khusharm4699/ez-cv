#!/usr/bin/env python3
"""EZ-CV interview question bank.

The agent runs this to load the structured questions, then asks the user section
by section -- one focused question (or a tight batch) at a time -- recording each
answer's provenance. It NEVER invents an answer; unknowns are marked placeholder.

    python3 scripts/interview.py            # print the whole bank
    python3 scripts/interview.py identity   # print one section

This script only prints guidance; it does not collect input. Collection happens
in the conversation so the agent can ask natural follow-ups that push toward a
metric or a mechanism.
"""
import sys
from textwrap import indent

# Each section: (key, title, [questions]). Follow-ups in parentheses nudge toward
# numbers and mechanisms -- the things that make a resume land.
SECTIONS = [
    ("identity", "Identity & contact", [
        "Full name (exact spelling as you want it shown)?",
        "Target role / title for this resume (e.g. 'Backend Engineer')?",
        "One-line tagline you'd put under your name?",
        "City and country (location line)?",
        "Email? Phone? (phone is hidden from any public/hosted copy)",
    ]),
    ("target", "Target role / JD", [
        "Is there a specific job description? Paste it, or name the role + company.",
        "Which 5-8 keywords or skills does that role care about most?",
        "Seniority and years of experience the role expects?",
    ]),
    ("experience", "Work experience (repeat per job, newest first)", [
        "Company, your title, start and end dates (month + year), location?",
        "What did you OWN there, in one sentence?",
        "Top 3-6 achievements. For EACH: what changed, the number "
        "(before -> after / % / count / time / scale), and HOW you did it?",
        "Any awards or recognition at this job?",
        "Tools/tech you actually used here (for the tag row)?",
    ]),
    ("projects", "Projects (side, open-source, hackathon)", [
        "Project name, your role, and the timeframe?",
        "One-line description, then 1-2 quantified bullets (stars, users, speedup)?",
        "A public link (repo / demo)? Tools used?",
    ]),
    ("skills", "Skills", [
        "Group your skills into 3-6 buckets (e.g. Languages, Backend, Cloud).",
        "List the real items per bucket, strongest first. No aspirational tools.",
    ]),
    ("education", "Education", [
        "School, degree, graduation year, and any note (GPA/honors)?",
    ]),
    ("certifications", "Certifications", [
        "Certification name and year, for each you hold?",
    ]),
    ("speaking", "Speaking / teaching (optional)", [
        "Any talk/workshop? Title, audience size, one-line description?",
    ]),
    ("links", "Links", [
        "GitHub / LinkedIn / portfolio URLs you want shown? (skip any you lack)",
    ]),
    ("theme", "Look & feel (optional)", [
        "Accent color preference (hex)? Default is a terminal green (#22C55E).",
        "A custom terminal handle or monogram? (defaults derive from your name)",
    ]),
]

RULES = """\
Interview rules (read before asking):
  - Ask section by section, one focused question or a small batch at a time.
  - After each answer, ask the follow-up that gets a NUMBER or a MECHANISM.
  - Record provenance for every fact: verified / estimate(~) / placeholder.
  - NEVER invent a job, metric, tool, date, award, or link. Unknown -> placeholder.
  - There is no cap on questions. Keep going until the Readiness Gate is met.
"""


def print_section(key, title, questions):
  """Print one section's questions with numbering."""
  print(f"\n## {title}  [{key}]")
  for num, question in enumerate(questions, 1):
    print(indent(f"{num}. {question}", "  "))


def main():
  """Print the full bank, or a single section if named in argv."""
  wanted = sys.argv[1].lower() if len(sys.argv) > 1 else None
  print("EZ-CV interview question bank")
  print("=" * 40)
  print(RULES)
  matched = False
  for key, title, questions in SECTIONS:
    if wanted and key != wanted:
      continue
    print_section(key, title, questions)
    matched = True
  if wanted and not matched:
    valid = ", ".join(key for key, _, _ in SECTIONS)
    print(f"\nUnknown section '{wanted}'. Valid: {valid}")
    return 1
  print("\n" + "=" * 40)
  print("When the Readiness Gate is satisfied, write profile.json and run "
        "scripts/scaffold.py.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
