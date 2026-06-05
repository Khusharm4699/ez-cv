#!/usr/bin/env python3
"""Render profile.json into a modern two-column "Sidebar" HTML resume.

A dark accent rail (name, contact, skills, education, highlights) beside a light
main column (summary, experience, projects, speaking). The classic modern resume
layout. Deterministic and dependency-free.

    python3 scripts/build_html_sidebar.py
    python3 scripts/build_html_sidebar.py --compact   # denser one-page variant
    python3 scripts/build_html_sidebar.py --public     # hide phone (host-safe)

Output: output/<slug>_resume_sidebar.html  (slug derived from header.name)
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
        css.replace("#22C55E", IDENT["accent"])
        .replace("#16A34A", IDENT["accent_dim"])
        .replace("34,197,94", IDENT["accent_rgb"])
    )


def rich(value):
    """Escape text and render **bold** + auto-bolded metrics as <strong>."""
    return "".join(
        f"<strong>{esc(seg)}</strong>" if bold else esc(seg)
        for seg, bold in spans(value)
    )


def build_rail(data):
    h = data["header"]
    contact = [
        f'<li><a href="mailto:{esc(h["email"])}">{esc(h["email"])}</a></li>'
    ]
    if not PUBLIC and h.get("phone"):
        contact.append(f'<li><a href="tel:{esc(h["phone"])}">{esc(h["phone"])}</a></li>')
    for link in h.get("links", []):
        contact.append(
            f'<li><a href="{esc(link["url"])}" target="_blank" rel="noopener">'
            f'{esc(link["label"])}</a></li>'
        )
    contact_block = (
        '<div class="rail-block"><h2 class="rail-title">Contact</h2>'
        f'<ul class="rail-list">{"".join(contact)}</ul></div>'
    )

    skills_block = ""
    if data.get("skills"):
        groups = "".join(
            f'<div class="sk"><span class="sk-g">{esc(g["group"])}</span>'
            f'<span class="sk-i">{esc(", ".join(g["items"]))}</span></div>'
            for g in data["skills"]
        )
        skills_block = (
            '<div class="rail-block"><h2 class="rail-title">Skills</h2>'
            f'{groups}</div>'
        )

    edu_rows = []
    for e in data.get("education", []):
        note = f' &middot; {esc(e["note"])}' if e.get("note") else ""
        edu_rows.append(
            f'<div class="rail-edu"><span class="re-school">{esc(e["school"])}</span>'
            f'<span class="re-deg">{esc(e["degree"])}{note}</span>'
            f'<span class="re-year">{esc(e["year"])}</span></div>'
        )
    for c in data.get("certifications", []):
        edu_rows.append(
            f'<div class="rail-edu"><span class="re-school">{esc(c["name"])}</span>'
            '<span class="re-deg">Certification</span>'
            f'<span class="re-year">{esc(c["year"])}</span></div>'
        )
    edu_block = ""
    if edu_rows:
        edu_block = (
            '<div class="rail-block"><h2 class="rail-title">Education</h2>'
            f'{"".join(edu_rows)}</div>'
        )

    hi_block = ""
    if data.get("highlights"):
        cells = "".join(
            f'<div class="rail-hi"><span class="rh-num">{esc(it["stat"])}</span>'
            f'<span class="rh-label">{esc(it["label"])}</span></div>'
            for it in data["highlights"]
        )
        hi_block = (
            '<div class="rail-block"><h2 class="rail-title">Highlights</h2>'
            f'{cells}</div>'
        )

    return f"""
  <aside class="rail">
    <div class="badge">{esc(IDENT["monogram"])}</div>
    <h1 class="rail-name">{esc(h['name'])}</h1>
    <p class="rail-role">{esc(h['tagline'])}</p>
    <p class="rail-meta">{esc(h.get('current_role',''))}<br>{esc(h.get('location',''))}</p>
    {contact_block}{skills_block}{edu_block}{hi_block}
  </aside>"""


def _main_entry(role, company, location, start, end, body, awards, tags):
    loc = f' &middot; {esc(location)}' if location else ""
    return f"""
    <article class="entry">
      <div class="entry-head">
        <span class="entry-role">{esc(role)}</span>
        <span class="entry-date">{esc(start)} &ndash; {esc(end)}</span>
      </div>
      <div class="entry-co">{esc(company)}{loc}</div>
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
            tags = '<div class="tags">' + "".join(
                f'<span class="tag">{esc(t)}</span>' for t in x["tags"]) + "</div>"
        rows.append(_main_entry(
            x["role"], x["company"], x.get("location", ""),
            x["start"], x["end"], body, awards, tags))
    return f"""
    <section class="block">
      <h2 class="block-title">Experience</h2>
      {"".join(rows)}
    </section>"""


def build_summary(text):
    if not text:
        return ""
    return f"""
    <section class="block">
      <h2 class="block-title">Profile</h2>
      <p class="lead-prose">{rich(text)}</p>
    </section>"""


def build_projects(items):
    rest = [p for p in items if not p.get("featured")]
    if not rest:
        return ""
    rows = []
    for p in rest:
        date = f'<span class="entry-date">{esc(p.get("period",""))}</span>' if p.get("period") else ""
        sub = esc(p.get("subtitle", ""))
        role = f' &middot; {esc(p.get("role",""))}' if p.get("role") else ""
        blurb = f'<p class="lead">{rich(p["blurb"])}</p>' if p.get("blurb") else ""
        bullets = ""
        if p.get("bullets"):
            lis = "".join(f"<li>{rich(b)}</li>" for b in p["bullets"])
            bullets = f'<ul class="bullets">{lis}</ul>'
        links = ""
        if p.get("links"):
            links = '<p class="proj-links">' + " &middot; ".join(
                f'<a href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>'
                for l in p["links"]) + "</p>"
        tags = ""
        if p.get("tags"):
            tags = '<div class="tags">' + "".join(
                f'<span class="tag">{esc(t)}</span>' for t in p["tags"]) + "</div>"
        rows.append(f"""
    <article class="entry">
      <div class="entry-head"><span class="entry-role">{esc(p['name'])}</span>{date}</div>
      <div class="entry-co">{sub}{role}</div>
      {blurb}{bullets}{links}{tags}
    </article>""")
    return f"""
    <section class="block">
      <h2 class="block-title">Projects</h2>
      {"".join(rows)}
    </section>"""


def build_workshop(w):
    if not w:
        return ""
    return f"""
    <section class="block">
      <h2 class="block-title">Speaking</h2>
      <article class="entry">
        <div class="entry-head"><span class="entry-role">{esc(w.get('title',''))}</span></div>
        <div class="entry-co">{esc(w.get('audience',''))}</div>
        <p class="para">{rich(w.get('blurb',''))}</p>
      </article>
    </section>"""


CSS = r"""
:root{
  --rail:#111A2E; --rail2:#0c1424; --rail-fg:#E6EAF2; --rail-dim:#9AA6C0;
  --paper:#FFFFFF; --ink:#1B2333; --soft:#41506b; --faint:#7A879F; --rule:#E7EAF0;
  --accent:#22C55E; --accent-dim:#16A34A;
  --sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  --maxw:920px;
}
*{box-sizing:border-box}
body{margin:0; background:#E9ECF2; color:var(--ink); font-family:var(--sans);
  font-size:14.5px; line-height:1.55; -webkit-font-smoothing:antialiased}
a{color:inherit; text-decoration:none}
.resume{max-width:var(--maxw); margin:30px auto; display:grid;
  grid-template-columns:288px 1fr; background:var(--paper);
  box-shadow:0 24px 70px -30px rgba(20,30,60,.45); border-radius:14px; overflow:hidden}

/* rail */
.rail{background:linear-gradient(180deg,var(--rail),var(--rail2)); color:var(--rail-fg);
  padding:30px 24px; position:relative}
.badge{width:52px; height:52px; border-radius:13px; display:grid; place-items:center;
  background:linear-gradient(135deg,var(--accent),var(--accent-dim)); color:#04140a;
  font-weight:800; font-size:20px; letter-spacing:1px; margin-bottom:16px}
.rail-name{font-size:25px; line-height:1.1; margin:0 0 5px; font-weight:700}
.rail-role{color:var(--accent); font-size:13.5px; font-weight:600; margin:0 0 7px}
.rail-meta{color:var(--rail-dim); font-size:12px; margin:0 0 6px; line-height:1.5}
.rail-block{margin-top:22px}
.rail-title{font-size:11px; text-transform:uppercase; letter-spacing:.16em; font-weight:700;
  color:var(--accent); margin:0 0 9px; padding-bottom:6px; border-bottom:1px solid rgba(255,255,255,.10)}
.rail-list{list-style:none; margin:0; padding:0}
.rail-list li{font-size:12.5px; margin:5px 0; color:var(--rail-fg); word-break:break-word}
.rail-list a:hover{color:var(--accent)}
.sk{margin:8px 0}
.sk-g{display:block; font-size:12px; font-weight:600; color:var(--rail-fg)}
.sk-i{display:block; font-size:11.5px; color:var(--rail-dim); margin-top:1px}
.rail-edu{margin:9px 0}
.re-school{display:block; font-size:12.5px; font-weight:600}
.re-deg{display:block; font-size:11px; color:var(--rail-dim)}
.re-year{display:block; font-size:11px; color:var(--accent)}
.rail-hi{margin:8px 0}
.rh-num{font-size:17px; font-weight:700; color:var(--accent)}
.rh-label{display:block; font-size:11px; color:var(--rail-dim)}

/* main */
.main{padding:32px 32px 36px}
.block{margin-bottom:22px}
.block:last-child{margin-bottom:0}
.block-title{font-size:13px; text-transform:uppercase; letter-spacing:.14em; font-weight:700;
  color:var(--accent-dim); margin:0 0 12px; padding-bottom:7px; border-bottom:2px solid var(--rule)}
.lead-prose{margin:0; font-size:15px; color:var(--ink)}
.lead-prose strong,.lead strong,.bullets strong,.para strong{font-weight:700; color:var(--ink)}
.entry{margin-bottom:16px}
.entry:last-child{margin-bottom:0}
.entry-head{display:flex; justify-content:space-between; align-items:baseline; gap:12px}
.entry-role{font-size:16px; font-weight:700; color:var(--ink)}
.entry-date{font-size:12px; color:var(--faint); white-space:nowrap; font-variant-numeric:tabular-nums}
.entry-co{color:var(--accent-dim); font-size:13px; font-weight:600; margin-top:1px}
.lead{font-style:italic; color:var(--soft); margin:6px 0 4px; font-size:13.5px}
.para{color:var(--soft); margin:6px 0 0; font-size:13.5px}
.bullets{margin:6px 0 0; padding-left:18px}
.bullets li{margin:5px 0; color:#333; font-size:13.5px}
.bullets li::marker{color:var(--accent-dim)}
.awards{margin:7px 0 0; font-size:12.5px; color:var(--soft)}
.awards-label{text-transform:uppercase; letter-spacing:.1em; font-size:10px; font-weight:700;
  color:var(--accent-dim); margin-right:6px}
.proj-links{margin:5px 0 0; font-size:12.5px}
.proj-links a{color:var(--accent-dim)}
.proj-links a:hover{text-decoration:underline}
.tags{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px}
.tag{font-size:10.5px; padding:3px 9px; border-radius:20px; color:var(--soft);
  border:1px solid var(--rule); background:#F6F7FA}

@media (max-width:680px){
  .resume{grid-template-columns:1fr; margin:0; border-radius:0}
  .main{padding:24px 20px}
}
@media (prefers-reduced-motion: reduce){ html{scroll-behavior:auto} }

@media print{
  body{background:#fff}
  .resume{grid-template-columns:264px 1fr; margin:0; box-shadow:none; border-radius:0; max-width:none}
  .block,.entry{break-inside:avoid}
}
"""

COMPACT_CSS = r"""
body.compact{font-size:13px}
body.compact .resume{margin:14px auto}
body.compact .rail{padding:22px 18px}
body.compact .main{padding:22px 24px 26px}
body.compact .rail-name{font-size:21px}
body.compact .rail-block{margin-top:15px}
body.compact .block{margin-bottom:14px}
body.compact .block-title{margin-bottom:8px}
body.compact .entry{margin-bottom:11px}
body.compact .lead{margin:4px 0 3px}
body.compact .bullets{margin:4px 0 0}
body.compact .bullets li{margin:3px 0; font-size:12.5px}
@media print{ body.compact{font-size:9.6px} }
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

    main_col = (
        build_summary(data.get("summary", ""))
        + build_experience(data.get("experience", []))
        + build_projects(data.get("projects", []))
        + build_workshop(data.get("workshop"))
    )
    doc = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{esc(h['name'])} \u2014 {esc(h['tagline'])}</title>\n"
        f'<meta name="description" content="{esc(data.get("summary","").replace("**", "")[:155])}"/>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>\n'
        f"<style>{_themed(CSS)}{COMPACT_CSS if compact else ''}</style>\n</head>\n"
        f"<body class=\"{'compact' if compact else ''}\">\n"
        '<main class="resume">\n'
        f"{build_rail(data)}\n"
        f'    <div class="main">\n{main_col}\n    </div>\n'
        "</main>\n</body>\n</html>\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = IDENT["slug"]
    if PUBLIC:
        out_file = OUT_DIR / f"{slug}_resume_sidebar_public.html"
    elif compact:
        out_file = OUT_DIR / f"{slug}_resume_sidebar_onepage.html"
    else:
        out_file = OUT_DIR / f"{slug}_resume_sidebar.html"
    out_file.write_text(doc, encoding="utf-8")
    print(f"Wrote {out_file}  ({len(doc):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
