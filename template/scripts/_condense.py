#!/usr/bin/env python3
"""Shared one-page condenser for the resume renderers.

`condense(data)` returns a trimmed deep copy of profile.json so the same data
source can drive both the full resume and a single-page variant. Trimming is
content-preserving in spirit: it keeps the lead facts/numbers and drops trailing
detail rather than rewording anything.

Condensing is data-driven, not name-hardcoded. Per-entry hints in profile.json
control trimming:
  - experience/project entry  "onepage": "drop"    -> removed on the one-pager
  - project entry             "onepage": "oneline" -> blurb only, no bullets
  - experience entry          "type": "oneliner"    -> removed on the one-pager
Otherwise sensible defaults apply (see below).
"""
import copy
import re


def first_sentences(text, n):
    if not text:
        return text
    parts = re.split(r"(?<=[.!?])\s+", str(text).strip())
    return " ".join(parts[:n]).strip()


def condense(data):
    d = copy.deepcopy(data)

    # Summary -> first 2 sentences.
    d["summary"] = first_sentences(d.get("summary", ""), 2)

    # Highlights -> top 4 (drop the least punchy trailing stats).
    if d.get("highlights"):
        d["highlights"] = d["highlights"][:4]

    # Skills -> cap each group to its first 6 items to curb line wrapping while
    # keeping the highest-signal keywords up front.
    for group in d.get("skills", []):
        if group.get("items"):
            group["items"] = group["items"][:6]

    # Experience: drop one-liner roles and any entry tagged onepage=drop. For
    # the remaining primary roles, the most recent keeps up to 6 bullets (each
    # collapsed to its first sentence) plus its lead-in; older primary roles
    # keep 3 first-sentence bullets and drop the lead-in to hold the one-page
    # fit. Awards are kept but capped to two so the line never wraps.
    experience = [
        x for x in d.get("experience", [])
        if x.get("type") != "oneliner" and x.get("onepage") != "drop"
    ]
    primary_seen = 0
    for x in experience:
        if x.get("type") == "primary" and x.get("bullets"):
            limit = 6 if primary_seen == 0 else 3
            x["bullets"] = [first_sentences(b, 1) for b in x["bullets"][:limit]]
            if primary_seen > 0:
                x["summary"] = ""
            primary_seen += 1
        elif x.get("type") == "collapsed":
            short = x.get("paragraph_short")
            x["paragraph"] = short or first_sentences(x.get("paragraph", ""), 3)
        if x.get("awards"):
            x["awards"] = x["awards"][:2]
    d["experience"] = experience

    # Projects: drop entries tagged onepage=drop; collapse onepage=oneline to a
    # single-sentence blurb with no bullets.
    projects = []
    for project in d.get("projects", []):
        hint = project.get("onepage")
        if hint == "drop":
            continue
        if hint == "oneline":
            project["bullets"] = []
            project["subprojects"] = []
            project["blurb"] = first_sentences(project.get("blurb", ""), 1)
        projects.append(project)
    d["projects"] = projects

    # Workshop -> one line.
    workshop = d.get("workshop")
    if workshop and workshop.get("blurb"):
        workshop["blurb"] = first_sentences(workshop["blurb"], 1)

    return d
