#!/usr/bin/env python3
"""Shared inline-emphasis tokenizer for the resume renderers.

`spans(text)` returns an ordered list of `(segment, is_bold)` tuples so every
renderer (HTML, Markdown, LaTeX) can bold identically. Two sources of bold:

  1. Manual emphasis written in profile.json as ``**like this**``.
  2. Auto-bolded impact metrics: percentages, multipliers, counts with ``+``,
     time spans, and ranges (e.g. ``80%``, ``15x``, ``900+``, ``18 hours to
     7 hours``, ``85% to 100%``, ``100-200+``).

Bare integers (``113``), version tokens (``3.x``, ``V1``), and 4-digit years
are intentionally NOT auto-bolded to avoid false positives. Renderers escape
each segment in their own syntax, then wrap bold segments.
"""
import re

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

# number with an optional single decimal (so "3.x" is not treated as "3.")
_NUM = r"\d[\d,]*(?:\.\d+)?"
_UNIT = r"(?:%|x|\+|hours?|hrs?|h)"
_RANGE = rf"{_NUM}\s*{_UNIT}?\s*(?:\u2013|\u2192|->|-|to)\s*{_NUM}\s*{_UNIT}?"
_SINGLE = rf"{_NUM}\s*{_UNIT}"
# A metric must carry a unit or be a range; a bare number is left alone.
METRIC_RE = re.compile(rf"(?<![\w.])(?:{_RANGE}|{_SINGLE})")


def _auto(segment):
    """Yield (text, is_bold) spans for auto-bolded metrics in a plain segment."""
    segment = segment.replace("**", "")  # drop any stray/unbalanced markers
    out = []
    pos = 0
    for match in METRIC_RE.finditer(segment):
        if match.start() > pos:
            out.append((segment[pos:match.start()], False))
        token = match.group(0)
        trimmed = token.rstrip()
        out.append((trimmed, True))
        if len(trimmed) < len(token):  # keep trailing whitespace outside bold
            out.append((token[len(trimmed):], False))
        pos = match.end()
    if pos < len(segment):
        out.append((segment[pos:], False))
    return out


def spans(text):
    """Split text into ordered (segment, is_bold) spans.

    Args:
        text: Raw string, possibly containing ``**manual**`` emphasis.

    Returns:
        List of (segment, is_bold) tuples covering the whole string in order.
    """
    text = str(text)
    out = []
    pos = 0
    for match in BOLD_RE.finditer(text):
        if match.start() > pos:
            out.extend(_auto(text[pos:match.start()]))
        out.append((match.group(1), True))
        pos = match.end()
    if pos < len(text):
        out.extend(_auto(text[pos:]))
    return out
