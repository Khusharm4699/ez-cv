#!/usr/bin/env python3
"""Derive per-person identity tokens from the profile header.

Every renderer pulls its filenames, terminal prompt, monogram, AI assistant id,
and accent theme from here so a single profile.json fully personalizes the
resume with no hardcoded names. All values can be overridden explicitly in the
profile header; otherwise sensible defaults are derived from the person's name.
"""
import re


def slugify(value, sep="_"):
    """Lowercase, collapse non-alphanumerics to `sep` (e.g. 'Ada Lovelace')."""
    out = re.sub(r"[^a-z0-9]+", sep, str(value).lower()).strip(sep)
    return out or "resume"


def initials(name):
    """Two-letter monogram from a name ('Ada Lovelace' -> 'AL')."""
    parts = [p for p in re.split(r"\s+", str(name).strip()) if p]
    if not parts:
        return "CV"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _first_token(name):
    parts = [p for p in re.split(r"\s+", str(name).strip()) if p]
    raw = parts[0] if parts else "resume"
    return re.sub(r"[^a-z0-9]", "", raw.lower()) or "resume"


def _hex_to_rgb(value):
    """'#22C55E' -> '34,197,94' for use in rgba() glows."""
    h = str(value).lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    try:
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return f"{r},{g},{b}"
    except (ValueError, IndexError):
        return "34,197,94"


# Default theme matches the OLED terminal palette (ui-ux-pro-max recommendation).
DEFAULT_ACCENT = "#22C55E"
DEFAULT_ACCENT_DIM = "#16A34A"
DEFAULT_ACCENT_PRINT = "0A7D2C"  # darker green for print/LaTeX contrast


def identity(header):
    """Build the identity token bundle for a profile header.

    Args:
        header: The `header` object from profile.json. May contain optional
            overrides: `handle`, `monogram`, `role_slug`, `ai_id`, and
            `theme.accent` / `theme.accent_dim` / `theme.accent_print`.

    Returns:
        Dict of personalization tokens consumed by every renderer.
    """
    name = header.get("name", "Your Name")
    first = _first_token(name)
    theme = header.get("theme") or {}
    accent = theme.get("accent") or DEFAULT_ACCENT
    accent_dim = theme.get("accent_dim") or DEFAULT_ACCENT_DIM
    accent_print = theme.get("accent_print") or DEFAULT_ACCENT_PRINT
    return {
        "name": name,
        "slug": slugify(name),
        "monogram": header.get("monogram") or initials(name),
        "user": header.get("handle") or f"{first}@dev",
        "role_slug": header.get("role_slug")
        or slugify(header.get("current_role", "role"), "-"),
        "ai_id": header.get("ai_id") or f"{first}-1.0",
        "accent": accent,
        "accent_dim": accent_dim,
        "accent_rgb": _hex_to_rgb(accent),
        "accent_print": str(accent_print).lstrip("#").upper(),
    }
