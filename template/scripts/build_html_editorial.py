#!/usr/bin/env python3
"""Render profile.json into a light, print-grade "Editorial" HTML resume.

A clean, recruiter-friendly single-column theme: serif display headings, a sans
body, generous whitespace, and hairline rules. Deterministic and dependency-free.

    python3 scripts/build_html_editorial.py
    python3 scripts/build_html_editorial.py --compact   # denser one-page variant
    python3 scripts/build_html_editorial.py --public     # hide phone (host-safe)

Output: output/<slug>_resume_editorial.html  (slug derived from header.name)
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _condense import condense  # noqa: E402
from _emphasis import spans  # noqa: E402
from _identity import identity  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILE = SKILL_DIR / "data" / "profile.json"
OUT_DIR = SKILL_DIR / "output"

PUBLIC = False
IDENT = {}


def esc(value):
    return html.escape(str(value), quote=True)


def _themed(css):
    """Swap the default accent tokens for the profile's accent theme."""
    return (
        css.replace("#1D4ED8", IDENT["accent"])
        .replace("#1E40AF", IDENT["accent_dim"])
    )


def rich(value):
    """Escape text and render **bold** + auto-bolded metrics as <strong>."""
    return "".join(
        f"<strong>{esc(seg)}</strong>" if bold else esc(seg)
        for seg, bold in spans(value)
    )


def join_links(h):
    """Inline contact line: email, phone (unless public), then profile links."""
    parts = [f'<a href="mailto:{esc(h["email"])}">{esc(h["email"])}</a>']
    if not PUBLIC and h.get("phone"):
        parts.append(f'<a href="tel:{esc(h["phone"])}">{esc(h["phone"])}</a>')
    for link in h.get("links", []):
        parts.append(
            f'<a href="{esc(link["url"])}" target="_blank" rel="noopener">'
            f'{esc(link["label"])}</a>'
        )
    return '<span class="sep">/</span>'.join(parts)


def build_masthead(h):
    return f"""
<header class="masthead">
  <h1 class="name">{esc(h['name'])}</h1>
  <p class="tagline">{esc(h['tagline'])}</p>
  <p class="meta">{esc(h.get('current_role',''))} &middot; {esc(h.get('location',''))}</p>
  <div class="contact">{join_links(h)}</div>
</header>
"""


def build_highlights(items):
    if not items:
        return ""
    cells = "".join(
        f'<div class="hi"><span class="hi-num">{esc(it["stat"])}</span>'
        f'<span class="hi-label">{esc(it["label"])}</span></div>'
        for it in items
    )
    return f'<div class="highlights">{cells}</div>'


def build_summary(text):
    if not text:
        return ""
    return f"""
<section class="block">
  <h2 class="block-title">Summary</h2>
  <p class="lead-prose">{rich(text)}</p>
</section>
"""


def build_skills(groups):
    if not groups:
        return ""
    rows = "".join(
        f'<div class="skill-row"><span class="skill-group">{esc(g["group"])}</span>'
        f'<span class="skill-items">{esc(", ".join(g["items"]))}</span></div>'
        for g in groups
    )
    return f"""
<section class="block">
  <h2 class="block-title">Skills</h2>
  <div class="skills">{rows}</div>
</section>
"""


def _entry(role, company, location, start, end, body, awards, tags):
    loc = f' <span class="entry-loc">&middot; {esc(location)}</span>' if location else ""
    return f"""
  <article class="entry">
    <div class="entry-head">
      <div class="entry-id"><span class="entry-role">{esc(role)}</span>
        <span class="entry-co">{esc(company)}{loc}</span></div>
      <span class="entry-date">{esc(start)} &ndash; {esc(end)}</span>
    </div>
    {body}{awards}{tags}
  </article>"""


def build_experience(items):
    if not items:
        return ""
    rows = []
    for x in items:
        body = ""
        if x.get("type") == "primary" and x.get("bullets"):
            lead = f'<p class="lead">{rich(x["summary"])}</p>' if x.get("summary") else ""
            lis = "".join(f"<li>{rich(b)}</li>" for b in x["bullets"])
            body = f'{lead}<ul class="bullets">{lis}</ul>'
        elif x.get("type") == "collapsed":
            lead = f'<p class="lead">{rich(x["summary"])}</p>' if x.get("summary") else ""
            body = f'{lead}<p class="para">{rich(x.get("paragraph",""))}</p>'
        else:
            body = f'<p class="para">{rich(x.get("summary",""))}</p>'
        awards = ""
        if x.get("awards"):
            joined = " &middot; ".join(esc(a) for a in x["awards"])
            awards = f'<p class="awards"><span class="awards-label">Awards</span> {joined}</p>'
        tags = ""
        if x.get("tags"):
            tags = (
                '<p class="tags">'
                + " &middot; ".join(esc(t) for t in x["tags"])
                + "</p>"
            )
        rows.append(_entry(
            x["role"], x["company"], x.get("location", ""),
            x["start"], x["end"], body, awards, tags))
    return f"""
<section class="block">
  <h2 class="block-title">Experience</h2>
  {"".join(rows)}
</section>
"""


def build_projects(items):
    rest = [p for p in items if not p.get("featured")]
    if not rest:
        return ""
    rows = []
    for p in rest:
        head_date = f'<span class="entry-date">{esc(p.get("period",""))}</span>' if p.get("period") else ""
        sub = esc(p.get("subtitle", ""))
        role = f' <span class="entry-loc">&middot; {esc(p.get("role",""))}</span>' if p.get("role") else ""
        blurb = f'<p class="lead">{rich(p["blurb"])}</p>' if p.get("blurb") else ""
        bullets = ""
        if p.get("bullets"):
            lis = "".join(f"<li>{rich(b)}</li>" for b in p["bullets"])
            bullets = f'<ul class="bullets">{lis}</ul>'
        links = ""
        if p.get("links"):
            links = '<p class="proj-links">' + " &middot; ".join(
                f'<a href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>'
                for l in p["links"]
            ) + "</p>"
        tags = ""
        if p.get("tags"):
            tags = '<p class="tags">' + " &middot; ".join(esc(t) for t in p["tags"]) + "</p>"
        rows.append(f"""
  <article class="entry">
    <div class="entry-head">
      <div class="entry-id"><span class="entry-role">{esc(p['name'])}</span>
        <span class="entry-co">{sub}{role}</span></div>
      {head_date}
    </div>
    {blurb}{bullets}{links}{tags}
  </article>""")
    return f"""
<section class="block">
  <h2 class="block-title">Projects</h2>
  {"".join(rows)}
</section>
"""


def build_workshop(w):
    if not w:
        return ""
    return f"""
<section class="block">
  <h2 class="block-title">Speaking</h2>
  <article class="entry">
    <div class="entry-head">
      <div class="entry-id"><span class="entry-role">{esc(w.get('title',''))}</span>
        <span class="entry-co">{esc(w.get('audience',''))}</span></div>
    </div>
    <p class="para">{rich(w.get('blurb',''))}</p>
  </article>
</section>
"""


def build_education(edu, certs):
    if not edu and not certs:
        return ""
    rows = []
    for e in edu:
        note = f' <span class="entry-loc">&middot; {esc(e["note"])}</span>' if e.get("note") else ""
        rows.append(
            '<div class="entry-head"><div class="entry-id">'
            f'<span class="entry-role">{esc(e["school"])}</span>'
            f'<span class="entry-co">{esc(e["degree"])}{note}</span></div>'
            f'<span class="entry-date">{esc(e["year"])}</span></div>'
        )
    for c in certs:
        rows.append(
            '<div class="entry-head"><div class="entry-id">'
            f'<span class="entry-role">{esc(c["name"])}</span>'
            '<span class="entry-co">Certification</span></div>'
            f'<span class="entry-date">{esc(c["year"])}</span></div>'
        )
    return f"""
<section class="block">
  <h2 class="block-title">Education &amp; Certifications</h2>
  <div class="edu">{"".join(rows)}</div>
</section>
"""


CSS = r"""
:root{
  --paper:#FBFAF7; --ink:#1A1A1A; --soft:#4B4B4B; --faint:#7A7A7A;
  --rule:#E2DDD3; --accent:#1D4ED8; --accent-dim:#1E40AF;
  --serif:'Fraunces','Source Serif 4',Georgia,'Times New Roman',serif;
  --sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  --maxw:780px;
}
*{box-sizing:border-box}
body{margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans);
  font-size:15px; line-height:1.6; -webkit-font-smoothing:antialiased}
a{color:var(--accent-dim); text-decoration:none}
a:hover{text-decoration:underline}
.page{max-width:var(--maxw); margin:0 auto; padding:54px 40px 60px}

/* masthead */
.masthead{text-align:center; padding-bottom:22px; border-bottom:2px solid var(--ink); margin-bottom:8px}
.name{font-family:var(--serif); font-weight:600; font-size:clamp(34px,6vw,52px);
  letter-spacing:-.5px; margin:0 0 6px; line-height:1.05}
.tagline{font-family:var(--serif); font-style:italic; color:var(--accent-dim);
  font-size:clamp(15px,2.4vw,19px); margin:0 0 8px}
.meta{color:var(--faint); font-size:13px; margin:0 0 12px; letter-spacing:.02em}
.contact{font-size:13px; color:var(--soft); display:flex; flex-wrap:wrap;
  gap:8px; justify-content:center; align-items:center}
.contact .sep{color:var(--rule)}

/* highlights strip */
.highlights{display:flex; flex-wrap:wrap; justify-content:center; gap:26px;
  padding:16px 0 4px; border-bottom:1px solid var(--rule)}
.hi{display:flex; flex-direction:column; align-items:center; min-width:96px}
.hi-num{font-family:var(--serif); font-weight:600; font-size:22px; color:var(--accent-dim)}
.hi-label{color:var(--faint); font-size:11px; text-align:center; margin-top:2px}

/* blocks */
.block{padding:20px 0 4px; border-bottom:1px solid var(--rule)}
.block:last-of-type{border-bottom:none}
.block-title{font-family:var(--sans); text-transform:uppercase; letter-spacing:.16em;
  font-size:12px; font-weight:700; color:var(--accent-dim); margin:0 0 12px}
.lead-prose{margin:0; font-size:15.5px; color:var(--ink)}
.lead-prose strong, .lead strong, .bullets strong, .para strong{font-weight:700; color:var(--ink)}

/* skills */
.skills{display:flex; flex-direction:column; gap:6px}
.skill-row{display:grid; grid-template-columns:140px 1fr; gap:12px; align-items:baseline}
.skill-group{font-weight:600; color:var(--accent-dim); font-size:13.5px}
.skill-items{color:var(--soft); font-size:14px}

/* entries */
.entry{margin:0 0 16px}
.entry:last-child{margin-bottom:4px}
.entry-head{display:flex; justify-content:space-between; gap:14px; align-items:baseline; flex-wrap:wrap}
.entry-id{display:flex; flex-direction:column}
.entry-role{font-family:var(--serif); font-weight:600; font-size:17px; color:var(--ink)}
.entry-co{color:var(--accent-dim); font-size:13.5px; margin-top:1px}
.entry-loc{color:var(--faint)}
.entry-date{color:var(--faint); font-size:12.5px; white-space:nowrap; font-variant-numeric:tabular-nums}
.lead{font-style:italic; color:var(--soft); margin:7px 0 5px; font-size:14px}
.para{color:var(--soft); margin:7px 0 0; font-size:14px}
.bullets{margin:7px 0 0; padding-left:20px}
.bullets li{margin:5px 0; color:#333; font-size:14px}
.bullets li::marker{color:var(--accent-dim)}
.awards{margin:8px 0 0; font-size:13px; color:var(--soft)}
.awards-label{text-transform:uppercase; letter-spacing:.1em; font-size:10.5px;
  font-weight:700; color:var(--accent-dim); margin-right:6px}
.proj-links{margin:6px 0 0; font-size:13px}
.tags{margin:7px 0 0; font-size:11.5px; color:var(--faint); letter-spacing:.02em}

/* education */
.edu{display:flex; flex-direction:column; gap:10px}

/* footer */
.foot{text-align:center; color:var(--faint); font-size:11.5px; padding-top:24px}

@media (max-width:640px){
  .page{padding:32px 20px 40px}
  .skill-row{grid-template-columns:1fr; gap:2px}
  .entry-head{flex-direction:column; gap:1px}
}

/* print */
@media print{
  body{background:#fff; font-size:11px}
  .page{max-width:none; margin:0; padding:0}
  .block{break-inside:avoid; padding:12px 0 2px}
  .entry{break-inside:avoid}
  a{color:var(--ink)}
}
"""

COMPACT_CSS = r"""
body.compact{font-size:13px; line-height:1.42}
body.compact .page{padding:30px 36px 34px}
body.compact .masthead{padding-bottom:14px; margin-bottom:4px}
body.compact .name{font-size:clamp(28px,5vw,40px); margin-bottom:3px}
body.compact .highlights{gap:18px; padding:10px 0 2px}
body.compact .hi-num{font-size:18px}
body.compact .block{padding:13px 0 2px}
body.compact .block-title{margin-bottom:7px}
body.compact .entry{margin-bottom:10px}
body.compact .lead{margin:4px 0 3px}
body.compact .bullets{margin:4px 0 0}
body.compact .bullets li{margin:3px 0; font-size:13px}
@media print{ body.compact{font-size:9.4px; line-height:1.32} }
"""


def main():
    global PUBLIC, IDENT
    compact = "--compact" in sys.argv[1:]
    PUBLIC = "--public" in sys.argv[1:]
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    if compact:
        data = condense(data)
    h = data["header"]
    IDENT = identity(h)

    body = (
        build_masthead(h)
        + build_highlights(data.get("highlights", []))
        + build_summary(data.get("summary", ""))
        + build_skills(data.get("skills", []))
        + build_experience(data.get("experience", []))
        + build_projects(data.get("projects", []))
        + build_workshop(data.get("workshop"))
        + build_education(data.get("education", []), data.get("certifications", []))
        + f'<p class="foot">{esc(h["name"])} &middot; {esc(h.get("location",""))} '
          "&middot; generated by EZ-CV</p>"
    )
    doc = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{esc(h['name'])} \u2014 {esc(h['tagline'])}</title>\n"
        f'<meta name="description" content="{esc(data.get("summary","").replace("**", "")[:155])}"/>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>\n'
        f"<style>{_themed(CSS)}{COMPACT_CSS if compact else ''}</style>\n</head>\n"
        f"<body class=\"{'compact' if compact else ''}\">\n"
        f'<main class="page">\n{body}\n</main>\n'
        "</body>\n</html>\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = IDENT["slug"]
    if PUBLIC:
        out_file = OUT_DIR / f"{slug}_resume_editorial_public.html"
    elif compact:
        out_file = OUT_DIR / f"{slug}_resume_editorial_onepage.html"
    else:
        out_file = OUT_DIR / f"{slug}_resume_editorial.html"
    out_file.write_text(doc, encoding="utf-8")
    print(f"Wrote {out_file}  ({len(doc):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
