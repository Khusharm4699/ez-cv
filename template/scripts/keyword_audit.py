#!/usr/bin/env python3
"""Audit the generated resume against a job description's keywords.

Usage:
    python3 scripts/keyword_audit.py path/to/jd.txt
    python3 scripts/keyword_audit.py            # uses data/target_jd.txt if present

Reports which JD keywords are present/missing in the resume so you can
close coverage gaps before sending. Deterministic, zero LLM tokens.
"""
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILE = SKILL_DIR / "data" / "profile.json"
DEFAULT_JD = SKILL_DIR / "data" / "target_jd.txt"

# Curated agentic-AI / engineering keyword bank. Extend per target role.
KEYWORDS = [
    "python", "llm", "agent", "multi-agent", "context window", "token", "embedding",
    "rag", "tool calling", "prompt", "orchestration", "memory", "eval", "mcp",
    "langgraph", "langchain", "crewai", "kafka", "sqs", "rabbitmq", "sql", "nosql",
    "production", "deploy", "vector", "ollama", "open source", "kubernetes",
    "ci/cd", "system design", "failure mode", "streaming", "voice", "tts", "stt",
]


def text_blob(profile):
    parts = [profile.get("summary", "")]
    for s in profile.get("skills", []):
        parts += s.get("items", [])
        parts.append(s.get("group", ""))
    for x in profile.get("experience", []):
        parts += [x.get("summary", ""), x.get("paragraph", "")]
        parts += x.get("bullets", [])
        parts += x.get("tags", [])
    for p in profile.get("projects", []):
        parts += [p.get("blurb", ""), p.get("subtitle", "")]
        parts += p.get("bullets", [])
        parts += p.get("tags", [])
    return " ".join(parts).lower()


def main():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    blob = text_blob(profile)

    jd_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JD
    jd_words = set()
    if jd_path.exists():
        jd_text = jd_path.read_text(encoding="utf-8").lower()
        jd_words = {k for k in KEYWORDS if k in jd_text}
    keys = sorted(jd_words) if jd_words else KEYWORDS

    def found(k):
        # word-boundary match for short alphanumeric tokens to avoid
        # false positives (e.g. "rag" inside "storage"); substring for phrases.
        if re.fullmatch(r"[a-z0-9]+", k) and len(k) <= 5:
            return re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", blob) is not None
        return k in blob

    present, missing = [], []
    for k in keys:
        (present if found(k) else missing).append(k)

    print(f"Resume keyword audit  ({len(present)}/{len(keys)} present)\n")
    print("PRESENT:")
    for k in present:
        print(f"  [x] {k}")
    print("\nMISSING (close these before sending):")
    for k in missing:
        print(f"  [ ] {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
