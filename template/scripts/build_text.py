#!/usr/bin/env python3
"""Render profile.json into Markdown and self-contained LaTeX resumes.

Deterministic, dependency-free. Edit data/profile.json, then run:

    python3 scripts/build_text.py

Outputs:
    output/<slug>_resume.md   (ATS-clean Markdown)
    output/<slug>_resume.tex  (compiles with pdflatex / Overleaf)

The .tex uses only standard packages (geometry, titlesec, enumitem,
hyperref, xcolor) and no external .cls, so it compiles anywhere.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _condense import condense  # noqa: E402
from _emphasis import spans  # noqa: E402
from _identity import identity  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILE = SKILL_DIR / "data" / "profile.json"
OUT_DIR = SKILL_DIR / "output"

# Accent color (HTML hex, no #) for the LaTeX section rules; set in main() from
# the profile header so the PDF matches the chosen theme.
TEX_ACCENT = "0A7D2C"


# ----------------------------- shared helpers ----------------------------- #

def load():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


# Unicode -> ascii/markdown niceties (keep MD readable, avoid odd glyphs)
_MD_MAP = {
    "\u2192": "->", "\u2014": "\u2014", "\u2013": "\u2013",
    "\u00b7": "\u00b7", "\u2026": "...",
}


def md_text(s):
    s = str(s)
    for k, v in _MD_MAP.items():
        s = s.replace(k, v)
    return s


def md_rich(s):
    """Markdown text with **bold** + auto-bolded metrics applied."""
    return "".join(
        f"**{seg}**" if bold else seg for seg, bold in spans(md_text(s))
    )


# ------------------------------- Markdown --------------------------------- #

def md_links(links, email=None, phone=None):
    parts = []
    if email:
        parts.append(f"[{email}](mailto:{email})")
    if phone:
        parts.append(phone)
    for l in links:
        parts.append(f"[{l['label']}]({l['url']})")
    return " \u00b7 ".join(parts)


def md_project_lines(p):
    out = []
    period = f" · {md_text(p['period'])}" if p.get("period") else ""
    out.append(f"### {md_text(p['name'])}{period}")
    sub = md_text(p.get("subtitle", ""))
    role = md_text(p.get("role", ""))
    out.append(f"*{sub}{(' · ' + role) if role else ''}*\n")
    if p.get("blurb"):
        out.append(f"{md_rich(p['blurb'])}\n")
    for b in p.get("bullets", []):
        out.append(f"- {md_rich(b)}")
    if p.get("bullets"):
        out.append("")
    for s in p.get("subprojects", []):
        out.append(f"  - `{md_text(s['name'])}` — {md_text(s['desc'])}")
    if p.get("subprojects"):
        out.append("")
    for l in p.get("links", []):
        out.append(f"[{md_text(l['label'])}]({l['url']})")
    if p.get("tags"):
        out.append(f"`{'` `'.join(md_text(t) for t in p['tags'])}`\n")
    return out


def render_md(d):
    h = d["header"]
    out = []
    out.append(f"# {md_text(h['name'])}")
    out.append("")
    out.append(f"**{md_text(h['tagline'])}** · {md_text(h.get('current_role',''))} · {md_text(h.get('location',''))}")
    out.append("")
    out.append(md_links(h.get("links", []), h.get("email"), h.get("phone")))
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"## Summary\n\n{md_rich(d.get('summary',''))}")
    out.append("")

    # Highlights are intentionally omitted from the text/ATS formats: the
    # metrics already live in the experience bullets.
    projects = d.get("projects", [])

    # skills
    out.append("## Skills\n")
    for g in d.get("skills", []):
        out.append(f"- **{md_text(g['group'])}:** {', '.join(md_text(i) for i in g['items'])}")
    out.append("")

    # experience
    out.append("## Experience\n")
    for x in d.get("experience", []):
        out.append(f"### {md_text(x['role'])} · {md_text(x['company'])}")
        out.append(f"*{md_text(x['start'])} \u2013 {md_text(x['end'])} · {md_text(x.get('location',''))}*\n")
        if x.get("summary"):
            out.append(f"{md_rich(x['summary'])}\n")
        if x.get("type") == "primary" and x.get("bullets"):
            for b in x["bullets"]:
                out.append(f"- {md_rich(b)}")
            out.append("")
        elif x.get("type") == "collapsed" and x.get("paragraph"):
            out.append(f"{md_rich(x['paragraph'])}\n")
        if x.get("awards"):
            joined = " \u00b7 ".join(md_text(a) for a in x["awards"])
            out.append(f"**Awards:** {joined}\n")
        if x.get("tags"):
            out.append(f"`{'` `'.join(md_text(t) for t in x['tags'])}`\n")

    # projects (non-featured)
    rest = [p for p in projects if not p.get("featured")]
    if rest:
        out.append("## Projects\n")
        for p in rest:
            out.extend(md_project_lines(p))

    # workshop
    w = d.get("workshop")
    if w:
        out.append("## Speaking\n")
        out.append(f"**{md_text(w['title'])}** ({md_text(w['audience'])}) \u2014 {md_text(w['blurb'])}\n")

    # education + certs
    out.append("## Education\n")
    for e in d.get("education", []):
        note = f" · {md_text(e['note'])}" if e.get("note") else ""
        out.append(f"- **{md_text(e['school'])}** \u2014 {md_text(e['degree'])}{note} *({md_text(e['year'])})*")
    out.append("")
    certs = d.get("certifications", [])
    if certs:
        out.append("## Certifications\n")
        for c in certs:
            out.append(f"- {md_text(c['name'])} *({md_text(c['year'])})*")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


# -------------------------------- LaTeX ----------------------------------- #

_TEX_REPL = [
    ("\\", r"\textbackslash{}"),  # must be first
    ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
    ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
    ("^", r"\textasciicircum{}"), ("~", r"$\sim$"),
    ("\u2192", r"$\rightarrow$"), ("\u2014", "---"), ("\u2013", "--"),
    ("\u00b7", r"\textperiodcentered{}"), ("\u2026", r"\ldots{}"),
    ("\u2019", "'"), ("\u201c", "``"), ("\u201d", "''"),
]


def tex(s):
    s = str(s)
    for a, b in _TEX_REPL:
        s = s.replace(a, b)
    return s


def tex_rich(s):
    """LaTeX text with \\textbf bold for **bold** + auto-bolded metrics."""
    return "".join(
        f"\\textbf{{{tex(seg)}}}" if bold else tex(seg)
        for seg, bold in spans(s)
    )


_TEX_COMPACT = False


def tex_items(items):
    if not items:
        return ""
    isep = "1pt" if _TEX_COMPACT else "2pt"
    tsep = "1pt" if _TEX_COMPACT else "2pt"
    lines = [f"\\begin{{itemize}}[leftmargin=1.2em,itemsep={isep},topsep={tsep},parsep=0pt]"]
    for it in items:
        lines.append(f"  \\item {tex_rich(it)}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def tex_project_lines(p):
    L = []
    L.append(r"\needspace{3\baselineskip}")
    period = f" \\hfill {tex(p['period'])}" if p.get("period") else ""
    L.append(f"\\textbf{{{tex(p['name'])}}}{period}\\\\")
    sub = tex(p.get("subtitle", ""))
    role = tex(p.get("role", ""))
    L.append(f"\\textit{{{sub}{(' -- ' + role) if role else ''}}}\\\\[2pt]")
    if p.get("blurb"):
        L.append(tex_rich(p["blurb"]) + r"\\")
    if p.get("bullets"):
        L.append(tex_items(p["bullets"]))
    if p.get("subprojects"):
        subs = [f"\\texttt{{{tex(s['name'])}}} ({tex(s['desc'])})" for s in p["subprojects"]]
        L.append(r"\textbf{Includes:} " + r", ".join(subs) + r"\\")
    for l in p.get("links", []):
        L.append(f"\\href{{{l['url']}}}{{{tex(l['label'])}}}\\\\")
    L.append(r"\vspace{2pt}" if _TEX_COMPACT else r"\vspace{4pt}")
    return L


def render_tex(d, compact=False):
    h = d["header"]
    contact = [f"\\href{{mailto:{h['email']}}}{{{tex(h['email'])}}}", tex(h["phone"])]
    for l in h.get("links", []):
        contact.append(f"\\href{{{l['url']}}}{{{tex(l['label'])}}}")
    contact_line = r" \textperiodcentered{} ".join(contact)

    docclass = "9pt" if compact else "10.5pt"
    margin = "0.8cm" if compact else "1.5cm"
    sec_space = "3pt" if compact else "10pt"
    sec_after = "1pt" if compact else "6pt"

    L = []
    L.append(f"\\documentclass[{docclass},a4paper]{{article}}")
    L.append(r"\usepackage[utf8]{inputenc}")
    L.append(r"\usepackage[T1]{fontenc}")
    L.append(f"\\usepackage[margin={margin}]{{geometry}}")
    L.append(r"\usepackage{enumitem}")
    L.append(r"\usepackage{needspace}")
    L.append(r"\usepackage{titlesec}")
    L.append(r"\usepackage{xcolor}")
    L.append(r"\usepackage[hidelinks]{hyperref}")
    L.append(f"\\definecolor{{accent}}{{HTML}}{{{TEX_ACCENT}}}")
    L.append(r"\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[\titlerule]")
    L.append(f"\\titlespacing*{{\\section}}{{0pt}}{{{sec_space}}}{{{sec_after}}}")
    L.append(r"\setlength{\parindent}{0pt}")
    if compact:
        L.append(r"\setlength{\parskip}{0.5pt}")
        L.append(r"\linespread{0.9}")
    L.append(r"\pagestyle{empty}")
    L.append(r"\hypersetup{colorlinks=true,urlcolor=accent}")
    L.append("")
    L.append(r"\begin{document}")
    # header
    L.append(r"\begin{center}")
    L.append(f"  {{\\Huge\\bfseries {tex(h['name'])}}}\\\\[3pt]")
    L.append(f"  {{\\large\\color{{accent}} {tex(h['tagline'])}}}\\\\[2pt]")
    L.append(f"  {tex(h.get('current_role',''))} \\textperiodcentered{{}} {tex(h.get('location',''))}\\\\[3pt]")
    L.append(f"  \\small {contact_line}")
    L.append(r"\end{center}")
    L.append("")
    # summary
    L.append(r"\section{Summary}")
    L.append(tex_rich(d.get("summary", "")))
    L.append("")
    # Highlights are omitted from the text/ATS formats: the metrics already
    # live in the experience bullets.
    projects = d.get("projects", [])
    # skills
    L.append(r"\section{Skills}")
    for g in d.get("skills", []):
        L.append(f"\\textbf{{{tex(g['group'])}:}} {tex(', '.join(g['items']))}\\\\")
    L.append("")
    # experience
    L.append(r"\section{Experience}")
    for x in d.get("experience", []):
        L.append(r"\needspace{4\baselineskip}")
        L.append(f"\\textbf{{{tex(x['role'])}}} \\hfill {tex(x['start'])} -- {tex(x['end'])}\\\\")
        L.append(f"\\textit{{{tex(x['company'])}}} \\hfill \\textit{{{tex(x.get('location',''))}}}\\\\[2pt]")
        if x.get("type") == "primary" and x.get("bullets"):
            L.append(tex_items(x["bullets"]))
        elif x.get("type") == "collapsed" and x.get("paragraph"):
            L.append(tex_rich(x["paragraph"]))
        else:
            L.append(tex_rich(x.get("summary", "")))
        if x.get("awards"):
            joined = " \\textperiodcentered{} ".join(tex(a) for a in x["awards"])
            L.append(f"\\textit{{Awards: {joined}}}\\\\")
        L.append(r"\vspace{2pt}" if _TEX_COMPACT else r"\vspace{4pt}")
    L.append("")
    # projects (non-featured)
    rest = [p for p in projects if not p.get("featured")]
    if rest:
        L.append(r"\section{Projects}")
        for p in rest:
            L.extend(tex_project_lines(p))
        L.append("")
    # workshop
    w = d.get("workshop")
    if w:
        L.append(r"\section{Speaking}")
        L.append(f"\\textbf{{{tex(w['title'])}}} ({tex(w['audience'])}) --- {tex(w['blurb'])}")
        L.append("")
    # education (+ certifications merged under one heading in compact mode so a
    # standalone "Certifications" heading is not orphaned to a second page)
    certs = d.get("certifications", [])
    L.append(r"\section{Education \& Certifications}" if (compact and certs) else r"\section{Education}")
    for e in d.get("education", []):
        note = f" \\textperiodcentered{{}} {tex(e['note'])}" if e.get("note") else ""
        L.append(f"\\textbf{{{tex(e['school'])}}} --- {tex(e['degree'])}{note} \\hfill {tex(e['year'])}\\\\")
    if certs:
        if not compact:
            L.append(r"\vspace{4pt}\section{Certifications}")
        for c in certs:
            L.append(f"{tex(c['name'])} \\hfill {tex(c['year'])}\\\\")
    # A trailing "\\" before \end{document} can spawn a blank trailing page when
    # the body fills the text block; drop it on the final content line.
    while L and L[-1].strip() == "":
        L.pop()
    if L and L[-1].endswith(r"\\"):
        L[-1] = L[-1][:-2]
    L.append("")
    L.append(r"\end{document}")
    return "\n".join(L) + "\n"


def main():
    global _TEX_COMPACT, TEX_ACCENT
    compact = "--compact" in sys.argv[1:]
    d = load()
    ident = identity(d["header"])
    TEX_ACCENT = ident["accent_print"]
    slug = ident["slug"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if compact:
        d = condense(d)
        _TEX_COMPACT = True
        md = render_md(d)
        tx = render_tex(d, compact=True)
        md_file = OUT_DIR / f"{slug}_resume_onepage.md"
        tex_file = OUT_DIR / f"{slug}_resume_onepage.tex"
        md_file.write_text(md, encoding="utf-8")
        tex_file.write_text(tx, encoding="utf-8")
        print(f"Wrote {md_file}  ({len(md):,} bytes)")
        print(f"Wrote {tex_file} ({len(tx):,} bytes)")
    else:
        md = render_md(d)
        tx = render_tex(d)
        md_file = OUT_DIR / f"{slug}_resume.md"
        tex_file = OUT_DIR / f"{slug}_resume.tex"
        md_file.write_text(md, encoding="utf-8")
        tex_file.write_text(tx, encoding="utf-8")
        print(f"Wrote {md_file}  ({len(md):,} bytes)")
        print(f"Wrote {tex_file} ({len(tx):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
