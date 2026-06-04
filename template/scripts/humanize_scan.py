#!/usr/bin/env python3
"""Deterministic human-voice / AI-fingerprint scanner for the resume prose.

Implements the claude-resume-kit 12-item scan over data/profile.json. Zero LLM
tokens. Exits non-zero if any hard check fails, so it is CI-usable.

Usage:
    python3 scripts/humanize_scan.py

Checks (hard = must pass, soft = warning):
  1. Tier-1 banned words          (hard)
  2. Banned verbs / adverbs       (hard)
  3. Banned phrases               (hard)
  4. Em-dashes in prose (<=2)     (hard)
  5. Bullets ending in -ing       (hard, the #1 structural AI marker)
  6. Abstract "X, Y, and Z" triplets (<=2; proper-noun lists ignored) (soft)
  7. 3+ consecutive same-length sentences (soft)
  8. Passive-voice bullet ratio (<20%) (soft)
"""
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILE = SKILL_DIR / "data" / "profile.json"

TIER1 = [
    "delve", "tapestry", "multifaceted", "pivotal", "realm", "synergy",
    "paradigm", "holistic", "nuanced", "foster", "embark", "leverage",
    "utilize", "harness", "spearhead", "cornerstone", "cutting-edge",
    "groundbreaking", "robust", "comprehensive", "meticulous", "seamless",
]
BANNED_VERBS = ["leverage", "utilize", "harness", "spearhead", "foster",
                "facilitate", "showcase", "underscore", "bolster"]
BANNED_ADVERBS = ["meticulously", "notably", "subsequently", "remarkably",
                  "seamlessly", "thereby"]
BANNED_PHRASES = [
    "in today's", "at the forefront", "it is worth noting", "this experience has taught",
    "uniquely positioned", "in an era of", "proven track record", "passionate about",
    "excited to apply", "demonstrated ability", "strong foundation in",
    "well-versed in", "adept at", "at the intersection of",
]


def _clean(value):
    """Strip ** emphasis markers so scans see the underlying prose."""
    return str(value).replace("**", "")


def collect(d):
    prose, bullets = [], []
    prose.append(("summary", _clean(d.get("summary", ""))))
    for x in d.get("experience", []):
        if x.get("summary"):
            prose.append((f"exp:{x['company']}:summary", _clean(x["summary"])))
        if x.get("paragraph"):
            prose.append((f"exp:{x['company']}:paragraph", _clean(x["paragraph"])))
        for b in x.get("bullets", []):
            bullets.append((f"exp:{x['company']}", _clean(b)))
    for p in d.get("projects", []):
        if p.get("blurb"):
            prose.append((f"proj:{p['name']}:blurb", _clean(p["blurb"])))
        for b in p.get("bullets", []):
            bullets.append((f"proj:{p['name']}", _clean(b)))
    w = d.get("workshop")
    if w and w.get("blurb"):
        prose.append(("workshop", _clean(w["blurb"])))
    return prose, bullets


def all_text(prose, bullets):
    return " ".join(t for _, t in prose) + " " + " ".join(t for _, t in bullets)


def word_hits(text, words):
    low = text.lower()
    return [w for w in words if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low)]


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def main():
    d = json.loads(PROFILE.read_text(encoding="utf-8"))
    prose, bullets = collect(d)
    blob = all_text(prose, bullets)
    results = []  # (name, ok, hard, detail)

    # 1. Tier-1 banned words
    hits = word_hits(blob, TIER1)
    results.append(("Tier-1 banned words", not hits, True, ", ".join(hits) or "none"))

    # 2. Banned verbs / adverbs
    bv = word_hits(blob, BANNED_VERBS + BANNED_ADVERBS)
    results.append(("Banned verbs/adverbs", not bv, True, ", ".join(bv) or "none"))

    # 3. Banned phrases
    bp = [p for p in BANNED_PHRASES if p in blob.lower()]
    results.append(("Banned phrases", not bp, True, ", ".join(bp) or "none"))

    # 4. Em-dashes in prose
    em = blob.count("\u2014") + blob.count(" --- ")
    results.append(("Em-dashes in prose (<=2)", em <= 2, True, f"{em} found"))

    # 5. Bullets ending in -ing analysis phrase
    ing = []
    for label, b in bullets:
        last = sentences(b)[-1] if sentences(b) else b
        m = re.search(r"([A-Za-z']+)[\".)\s]*$", last.strip())
        word = m.group(1).lower() if m else ""
        if word.endswith("ing") and word not in ("string", "engineering"):
            ing.append(f"{label}: ...{word}")
    results.append(("No bullet ends in -ing", not ing, True, "; ".join(ing) or "none"))

    # 6. Abstract triplets (ignore lists containing Capitalized/proper nouns)
    trip = []
    for label, t in prose + bullets:
        for m in re.finditer(r"([A-Za-z][\w'-]+), ([A-Za-z][\w'-]+),? and ([A-Za-z][\w'-]+)", t):
            grp = m.group(0)
            # ignore if any term is a proper noun / has a capital after first char span
            terms = [m.group(1), m.group(2), m.group(3)]
            if any(x[0].isupper() for x in terms):
                continue
            trip.append(f"{label}: {grp}")
    results.append(("Abstract triplets (<=2)", len(trip) <= 2, False,
                    (f"{len(trip)}: " + " | ".join(trip)) if trip else "0"))

    # 7. 3+ consecutive same-length sentences (within +-2 words) in prose blocks
    monotony = []
    for label, t in prose:
        lens = [len(s.split()) for s in sentences(t)]
        for i in range(len(lens) - 2):
            a, b, c = lens[i:i + 3]
            if max(a, b, c) - min(a, b, c) <= 2:
                monotony.append(f"{label}: {a}/{b}/{c} words")
                break
    results.append(("Sentence-length variety", not monotony, False,
                    "; ".join(monotony) or "varied"))

    # 8. Passive-voice bullet ratio (heuristic: was/were/been + past participle)
    passive = 0
    for _, b in bullets:
        if re.search(r"\b(was|were|been|is|are|be)\b\s+\w+ed\b", b.lower()):
            passive += 1
    ratio = (passive / len(bullets)) if bullets else 0
    results.append(("Passive voice (<20%)", ratio < 0.20, False,
                    f"{passive}/{len(bullets)} bullets ({ratio:.0%})"))

    # report
    hard_fail = False
    print("Human-voice scan (claude-resume-kit rules)\n" + "=" * 48)
    for name, ok, hard, detail in results:
        tag = "PASS" if ok else ("FAIL" if hard else "WARN")
        if not ok and hard:
            hard_fail = True
        print(f"  [{tag}] {name}: {detail}")
    print("=" * 48)
    print("RESULT:", "FAIL (fix hard items)" if hard_fail else "PASS")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
