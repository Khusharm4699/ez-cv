#!/usr/bin/env python3
"""Render profile.json into a self-contained terminal-themed HTML resume.

Deterministic, dependency-free renderer. Edit data/profile.json, then run:

    python3 scripts/build_html.py

Output: output/<slug>_resume.html  (slug derived from header.name)
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

# When True (--public), the phone number is omitted from the rendered page
# (email + profile links are kept) so the file is safe to host publicly.
PUBLIC = False

# Identity token bundle (slug, monogram, terminal handle, accent theme), filled
# in main() from the profile header so nothing about the person is hardcoded.
IDENT = {}


def esc(value):
    return html.escape(str(value), quote=True)


def _themed(css):
    """Recolor the default green palette to the profile's accent theme.

    The base CSS is authored with the default OLED-green tokens; this swaps the
    accent hexes and the literal green rgb (used in rgba glows) so any accent
    in the profile header propagates everywhere without per-rule edits.
    """
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


def chips(items, cls="chip"):
    return "".join(f'<span class="{cls}">{esc(i)}</span>' for i in items)


def link_icon():
    return (
        '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">'
        '<path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
        '<path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
        "</svg>"
    )


def prompt(path, cmd):
    """A terminal prompt line."""
    return (
        '<div class="cmd-line">'
        f'<span class="prompt-user">{esc(IDENT["user"])}</span>'
        f'<span class="prompt-sep">:</span>'
        f'<span class="prompt-path">{esc(path)}</span>'
        f'<span class="prompt-dollar">$</span> '
        f'<span class="prompt-cmd">{esc(cmd)}</span>'
        "</div>"
    )


def build_header(h, compact=False):
    photo = ""
    if h.get("photo"):
        ph_class = "photo placeholder" if h.get("photo_placeholder") else "photo"
        note = (
            '<span class="photo-note">drop photo.jpg in output/assets/</span>'
            if (h.get("photo_placeholder") and not PUBLIC)
            else ""
        )
        photo = (
            f'<div class="{ph_class}">'
            f'<img src="{esc(h["photo"])}" alt="{esc(h["name"])}" '
            f'onerror="this.style.display=\'none\';this.parentNode.classList.add(\'empty\')"/>'
            f'<span class="photo-mono">{esc(IDENT["monogram"])}</span>{note}'
            "</div>"
        )

    links = []
    for l in h.get("links", []):
        links.append(
            f'<a class="link" href="{esc(l["url"])}" target="_blank" rel="noopener">'
            f"{link_icon()}{esc(l['label'])}</a>"
        )
    links_html = "".join(links)

    chips_html = ""
    # contact chips (phone omitted in --public builds)
    contact = f'<a class="link" href="mailto:{esc(h["email"])}">{link_icon()}{esc(h["email"])}</a>'
    if not PUBLIC and h.get("phone"):
        contact += f'<a class="link" href="tel:{esc(h["phone"])}">{link_icon()}{esc(h["phone"])}</a>'

    cmd_text = f'whoami --role "{IDENT["role_slug"]}"'
    if compact:
        hero_cmd = (
            f'<div class="cmd-line"><span class="prompt-user">{esc(IDENT["user"])}</span>'
            '<span class="prompt-sep">:</span><span class="prompt-path">~</span>'
            f'<span class="prompt-dollar">$</span> <span class="prompt-cmd">{esc(cmd_text)}</span></div>'
        )
    else:
        hero_cmd = (
            f'<div class="cmd-line"><span class="prompt-user">{esc(IDENT["user"])}</span>'
            '<span class="prompt-sep">:</span><span class="prompt-path">~</span>'
            '<span class="prompt-dollar">$</span> <span id="typed"></span>'
            '<span class="caret">&#9608;</span></div>'
        )
    return f"""
<header id="top" class="hero">
  <div class="hero-grid">
    <div class="hero-main">
      {hero_cmd}
      <h1 class="name">{esc(h['name'])}</h1>
      <p class="role">{esc(h['tagline'])}</p>
      <p class="subrole">{esc(h.get('subtagline',''))}</p>
      <p class="meta">{esc(h.get('current_role',''))} &middot; {esc(h.get('location',''))}</p>
      <div class="links">{links_html}{contact}</div>
    </div>
    <div class="hero-side">
      {photo}
    </div>
  </div>
  <div class="scroll-hint" aria-hidden="true">scroll &darr;</div>
</header>
"""


def build_summary(text):
    return f"""
<section id="about" class="section">
  {prompt('~/resume', 'cat about.md')}
  <p class="prose reveal">{rich(text)}</p>
</section>
"""


def build_skills(groups):
    blocks = []
    for g in groups:
        blocks.append(
            '<div class="skill-group reveal">'
            f'<div class="skill-head"><span class="folder">{esc(g["group"])}/</span></div>'
            f'<div class="skill-chips">{chips(g["items"], "chip")}</div>'
            "</div>"
        )
    return f"""
<section id="skills" class="section">
  {prompt('~/resume', 'ls -la skills/')}
  <div class="skill-grid">{"".join(blocks)}</div>
</section>
"""


def build_highlights(items):
    if not items:
        return ""
    cards = "".join(
        f'<div class="stat reveal"><div class="stat-num">{esc(it["stat"])}</div>'
        f'<div class="stat-label">{esc(it["label"])}</div></div>'
        for it in items
    )
    return f"""
<section class="section">
  {prompt('~/resume', './run highlights')}
  <div class="stats">{cards}</div>
</section>
"""


def build_experience(items):
    rows = []
    for x in items:
        tags = f'<div class="tags">{chips(x.get("tags", []), "tag")}</div>' if x.get("tags") else ""
        awards = ""
        if x.get("awards"):
            items_html = "".join(
                f'<li>{esc(a)}</li>' for a in x["awards"]
            )
            awards = (
                f'<div class="awards"><span class="awards-label">'
                f'&#9733; Awards</span><ul>{items_html}</ul></div>'
            )
        body = ""
        if x.get("type") == "primary" and x.get("bullets"):
            lis = "".join(f"<li>{rich(b)}</li>" for b in x["bullets"])
            body = f'<p class="exp-summary">{rich(x.get("summary",""))}</p><ul class="bullets">{lis}</ul>'
        elif x.get("type") == "collapsed":
            body = (
                f'<p class="exp-summary">{rich(x.get("summary",""))}</p>'
                f'<p class="prose">{rich(x.get("paragraph",""))}</p>'
            )
        else:  # oneliner
            body = f'<p class="exp-summary">{rich(x.get("summary",""))}</p>'

        rows.append(f"""
  <article class="exp reveal">
    <div class="exp-top">
      <div>
        <h3 class="exp-role">{esc(x['role'])}</h3>
        <div class="exp-co">{esc(x['company'])} <span class="exp-loc">&middot; {esc(x.get('location',''))}</span></div>
      </div>
      <div class="exp-date">{esc(x['start'])} &mdash; {esc(x['end'])}</div>
    </div>
    {body}
    {awards}
    {tags}
  </article>""")
    return f"""
<section id="experience" class="section">
  {prompt('~/resume', 'git log --oneline experience/')}
  <div class="timeline">{"".join(rows)}</div>
</section>
"""


def _project_card(p, featured=False, show_tags=True):
    bullets = ""
    if p.get("bullets"):
        lis = "".join(f"<li>{rich(b)}</li>" for b in p["bullets"])
        bullets = f'<ul class="bullets">{lis}</ul>'
    subs = ""
    if p.get("subprojects"):
        sb = "".join(
            f'<span class="sub"><span class="sub-name">{esc(s["name"])}</span>'
            f'<span class="sub-desc">{esc(s["desc"])}</span></span>'
            for s in p["subprojects"]
        )
        subs = f'<div class="subgrid">{sb}</div>'
    links = ""
    if p.get("links"):
        la = "".join(
            f'<a class="link sm" href="{esc(l["url"])}" target="_blank" rel="noopener">{link_icon()}{esc(l["label"])}</a>'
            for l in p["links"]
        )
        links = f'<div class="links">{la}</div>'
    tags = f'<div class="tags">{chips(p.get("tags", []), "tag")}</div>' if (p.get("tags") and show_tags) else ""
    badge = '<span class="feat-badge">flagship</span>' if featured else ""
    cls = "card reveal featured" if featured else "card reveal"
    return f"""
  <article class="{cls}">
    <div class="card-head">
      <h3 class="card-title">{esc(p['name'])}{badge}</h3>
      <span class="card-period">{esc(p.get('period',''))}</span>
    </div>
    <div class="card-sub">{esc(p.get('subtitle',''))} <span class="card-role">&middot; {esc(p.get('role',''))}</span></div>
    <p class="prose">{rich(p.get('blurb',''))}</p>
    {bullets}
    {subs}
    {links}
    {tags}
  </article>"""


def build_projects(items):
    rest = [p for p in items if not p.get("featured")]
    if not rest:
        return ""
    cards = "".join(_project_card(p) for p in rest)
    return f"""
<section id="projects" class="section">
  {prompt('~/resume', './run projects --all')}
  <div class="cards">{cards}</div>
</section>
"""


def build_workshop(w):
    if not w:
        return ""
    return f"""
<section class="section">
  {prompt('~/resume', 'cat speaking/workshop.md')}
  <div class="callout reveal">
    <div class="callout-badge">{esc(w.get('audience',''))}</div>
    <h3 class="card-title">{esc(w.get('title',''))}</h3>
    <p class="prose">{esc(w.get('blurb',''))}</p>
  </div>
</section>
"""


def build_education(edu, certs):
    erows = "".join(
        f'<div class="edu-row reveal"><div class="edu-school">{esc(e["school"])}</div>'
        f'<div class="edu-deg">{esc(e["degree"])}{(" &middot; " + esc(e["note"])) if e.get("note") else ""}</div>'
        f'<div class="edu-year">{esc(e["year"])}</div></div>'
        for e in edu
    )
    crows = "".join(
        f'<div class="edu-row reveal"><div class="edu-school">{esc(c["name"])}</div>'
        f'<div class="edu-deg">Certification</div><div class="edu-year">{esc(c["year"])}</div></div>'
        for c in certs
    )
    return f"""
<section id="education" class="section">
  {prompt('~/resume', 'cat education.txt credentials.txt')}
  <div class="edu">{erows}{crows}</div>
</section>
"""


def build_footer(h):
    phone_link = ""
    if not PUBLIC and h.get("phone"):
        phone_link = (
            f'<a class="link" href="tel:{esc(h["phone"])}">'
            f'{link_icon()}{esc(h["phone"])}</a>'
        )
    return f"""
<footer id="contact" class="section footer">
  {prompt('~/resume', 'echo $CONTACT')}
  <h2 class="foot-name">Let's build things that run in production.</h2>
  <div class="links big">
    <a class="link" href="mailto:{esc(h['email'])}">{link_icon()}{esc(h['email'])}</a>
    {phone_link}
    {''.join(f'<a class="link" href="{esc(l["url"])}" target="_blank" rel="noopener">{link_icon()}{esc(l["label"])}</a>' for l in h.get('links', []))}
  </div>
  <p class="foot-note">{esc(h['name'])} &middot; {esc(h.get('location',''))} &middot; generated by EZ-CV</p>
</footer>
"""


CSS = r"""
:root{
  --bg:#0F172A; --bg2:#0B1220; --surface:#111A2E; --muted:#272F42;
  --fg:#F8FAFC; --fg-dim:#94A3B8; --border:#1F2A40;
  --accent:#22C55E; --accent-dim:#16A34A; --blue:#38BDF8; --amber:#FBBF24;
  --radius:12px; --maxw:980px;
  --mono:'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:
    radial-gradient(1200px 600px at 80% -10%, rgba(34,197,94,.08), transparent 60%),
    var(--bg);
  color:var(--fg); font-family:var(--mono); font-size:15px; line-height:1.6;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:var(--maxw); margin:0 auto; padding:0 22px}
a{color:inherit; text-decoration:none}

/* terminal window chrome */
.term{max-width:var(--maxw); margin:34px auto; border:1px solid var(--border);
  border-radius:14px; overflow:hidden; background:linear-gradient(180deg,var(--surface),var(--bg2));
  box-shadow:0 30px 80px -30px rgba(0,0,0,.8), 0 0 0 1px rgba(255,255,255,.02) inset}
.titlebar{display:flex; align-items:center; gap:8px; padding:11px 14px;
  background:#0c1424; border-bottom:1px solid var(--border); position:sticky; top:0; z-index:50}
.dot{width:12px;height:12px;border-radius:50%}
.dot.r{background:#EF4444}.dot.y{background:#FBBF24}.dot.g{background:#22C55E}
.titlebar .tt{margin-left:10px; color:var(--fg-dim); font-size:13px}
.titlebar nav{margin-left:auto; display:flex; gap:4px; flex-wrap:wrap}
.titlebar nav a{color:var(--fg-dim); font-size:12.5px; padding:5px 9px; border-radius:7px; transition:all .18s ease}
.titlebar nav a:hover{color:var(--accent); background:rgba(34,197,94,.10)}

.body{padding:8px 26px 30px}

/* command lines */
.cmd-line{font-size:13.5px; color:var(--fg-dim); margin:0 0 14px; word-break:break-word}
.prompt-user{color:var(--accent)}
.prompt-sep{color:var(--fg-dim)}
.prompt-path{color:var(--blue)}
.prompt-dollar{color:var(--fg-dim); margin:0 6px 0 2px}
.prompt-cmd{color:var(--fg)}
.caret{color:var(--accent); animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}

/* hero */
.hero{padding:30px 0 8px}
.hero-grid{display:grid; grid-template-columns:1fr auto; gap:26px; align-items:center}
.name{font-size:clamp(34px,6vw,58px); margin:6px 0 4px; letter-spacing:-1px;
  text-shadow:0 0 22px rgba(34,197,94,.20)}
.role{color:var(--accent); font-size:clamp(16px,2.4vw,21px); margin:0 0 2px; font-weight:500}
.subrole{color:var(--fg-dim); margin:0 0 12px; font-size:14px}
.meta{color:var(--fg-dim); font-size:13.5px; margin:0 0 16px}
.links{display:flex; flex-wrap:wrap; gap:9px}
.links.big{gap:12px; margin-top:8px}
.link{display:inline-flex; align-items:center; gap:7px; padding:8px 13px; font-size:13px;
  border:1px solid var(--border); border-radius:9px; color:var(--fg-dim);
  background:rgba(255,255,255,.015); transition:all .18s ease; cursor:pointer}
.link:hover{color:var(--accent); border-color:var(--accent-dim); background:rgba(34,197,94,.08);
  transform:translateY(-1px)}
.link svg{opacity:.8}
.link.sm{padding:6px 10px; font-size:12px}

/* photo */
.photo{width:150px;height:150px;border-radius:16px;overflow:hidden;position:relative;
  border:1px solid var(--border); background:linear-gradient(135deg,#16233b,#0c1424);
  display:flex;align-items:center;justify-content:center; box-shadow:0 0 0 4px rgba(34,197,94,.06)}
.photo img{width:100%;height:100%;object-fit:cover;position:relative;z-index:2}
.photo .photo-mono{position:absolute; font-size:42px; color:var(--muted); z-index:1; font-weight:700; letter-spacing:2px}
.photo .photo-note{position:absolute; bottom:6px; left:0; right:0; text-align:center; font-size:9px; color:var(--fg-dim); z-index:3}
.photo.empty img{display:none}

.scroll-hint{text-align:center; color:var(--fg-dim); font-size:12px; margin:26px 0 4px; opacity:.7}

/* stats */
.stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:18px 0 6px}
.stat{border:1px solid var(--border); border-radius:var(--radius); padding:16px 14px;
  background:rgba(255,255,255,.015); text-align:left}
.stat-num{font-size:24px; color:var(--accent); font-weight:700; text-shadow:0 0 16px rgba(34,197,94,.25)}
.stat-label{color:var(--fg-dim); font-size:12.5px; margin-top:4px}

/* sections */
.section{padding:30px 0; border-top:1px solid var(--border)}
.section:first-of-type{border-top:none}
.prose{color:#CBD5E1; margin:6px 0 0; font-size:14.5px}
.folder{color:var(--blue)}

/* skills */
.skill-grid{display:grid; grid-template-columns:repeat(2,1fr); gap:14px}
.skill-group{border:1px solid var(--border); border-radius:var(--radius); padding:14px;
  background:rgba(255,255,255,.012)}
.skill-head{margin-bottom:9px; font-size:13px}
.skill-chips{display:flex; flex-wrap:wrap; gap:7px}
.chip{font-size:12px; padding:5px 10px; border-radius:7px; border:1px solid var(--border);
  color:#CBD5E1; background:rgba(56,189,248,.05)}
.chip:hover{border-color:var(--blue); color:var(--blue)}

/* timeline */
.timeline{display:flex; flex-direction:column; gap:16px}
.exp{border:1px solid var(--border); border-left:3px solid var(--accent-dim);
  border-radius:var(--radius); padding:18px; background:rgba(255,255,255,.012)}
.exp-top{display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap; align-items:flex-start}
.exp-role{margin:0; font-size:16.5px}
.exp-co{color:var(--accent); font-size:14px; margin-top:2px}
.exp-loc{color:var(--fg-dim)}
.exp-date{color:var(--fg-dim); font-size:12.5px; white-space:nowrap}
.exp-summary{color:var(--fg-dim); font-size:13.5px; margin:10px 0 6px; font-style:italic}
.bullets{margin:8px 0 0; padding-left:18px}
.bullets li{margin:7px 0; color:#CBD5E1; font-size:14px}
.bullets li::marker{color:var(--accent)}
.prose strong,.bullets strong,.exp-summary strong{color:#F1F5F9; font-weight:700}
.bullets strong{color:var(--accent)}
.awards{margin-top:12px; display:flex; gap:10px; align-items:flex-start;
  border-left:2px solid var(--accent); padding-left:12px}
.awards-label{color:var(--accent); font-size:11px; font-weight:600;
  letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; margin-top:3px}
.awards ul{margin:0; padding-left:16px}
.awards li{margin:3px 0; color:var(--fg-dim); font-size:13px}
.awards li::marker{color:var(--accent)}

/* cards */
.cards{display:flex; flex-direction:column; gap:16px}
.card{border:1px solid var(--border); border-radius:var(--radius); padding:20px;
  background:linear-gradient(180deg,rgba(34,197,94,.04),rgba(255,255,255,.012)); transition:all .2s ease}
.card:hover{border-color:var(--accent-dim); transform:translateY(-2px);
  box-shadow:0 20px 50px -28px rgba(34,197,94,.4)}
.card.featured{border-color:var(--accent);
  background:linear-gradient(180deg,rgba(34,197,94,.09),rgba(255,255,255,.012));
  box-shadow:0 0 0 1px var(--accent-dim) inset,0 26px 60px -30px rgba(34,197,94,.55)}
.feat-badge{display:inline-block; margin-left:10px; vertical-align:middle; font-size:10px;
  letter-spacing:.12em; text-transform:uppercase; padding:2px 8px; border-radius:20px;
  color:var(--bg); background:var(--accent); font-weight:700}
.card-head{display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap}
.card-title{margin:0; font-size:18px; color:var(--fg)}
.card-period{color:var(--fg-dim); font-size:12.5px}
.card-sub{color:var(--accent); font-size:13.5px; margin-top:3px}
.card-role{color:var(--fg-dim)}
.subgrid{display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:9px; margin-top:14px}
.sub{display:flex; flex-direction:column; padding:9px 11px; border:1px dashed var(--border);
  border-radius:9px; background:rgba(0,0,0,.18)}
.sub-name{color:var(--accent); font-size:12.5px}
.sub-desc{color:var(--fg-dim); font-size:11.5px; margin-top:2px}

.tags{display:flex; flex-wrap:wrap; gap:6px; margin-top:14px}
.tag{font-size:11px; padding:3px 9px; border-radius:20px; color:var(--fg-dim);
  border:1px solid var(--border); background:rgba(255,255,255,.02)}

/* callout */
.callout{border:1px solid var(--accent-dim); border-radius:var(--radius); padding:18px;
  background:rgba(34,197,94,.05); position:relative}
.callout-badge{position:absolute; top:-11px; left:16px; background:var(--accent); color:#03210f;
  font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px}

/* education */
.edu{display:flex; flex-direction:column; gap:2px}
.edu-row{display:grid; grid-template-columns:1fr auto; gap:8px; padding:12px 4px;
  border-bottom:1px solid var(--border)}
.edu-school{color:var(--fg); font-size:14.5px}
.edu-deg{color:var(--fg-dim); font-size:13px; grid-column:1; }
.edu-year{color:var(--accent); font-size:13px; grid-row:1/3; align-self:center}

/* footer */
.footer{text-align:left; padding-bottom:48px}
.foot-name{font-size:clamp(20px,3.4vw,30px); margin:8px 0 14px}
.foot-note{color:var(--fg-dim); font-size:12px; margin-top:22px}

/* reveal anim */
.reveal{opacity:0; transform:translateY(14px); transition:opacity .5s ease, transform .5s ease}
.reveal.in{opacity:1; transform:none}

@media (max-width:720px){
  .hero-grid{grid-template-columns:1fr}
  .hero-side{order:-1}
  .skill-grid{grid-template-columns:1fr}
  .stats{grid-template-columns:1fr}
  .body{padding:8px 16px 24px}
  .titlebar nav{display:none}
}
@media (prefers-reduced-motion: reduce){
  .reveal{opacity:1; transform:none; transition:none}
  .caret{animation:none}
  html{scroll-behavior:auto}
}

/* print */
@media print{
  body{background:#fff; color:#111; font-size:11px}
  .term{box-shadow:none; border:none; margin:0; background:#fff}
  .titlebar, .scroll-hint, .caret, .dot{display:none !important}
  .section{border-top:1px solid #ccc; padding:12px 0; break-inside:avoid}
  .name{color:#111; text-shadow:none}
  .role,.prompt-user,.exp-co,.card-sub,.stat-num,.edu-year{color:#0a7d2c}
  .prose,.bullets li,.exp-summary,.awards li{color:#222}
  .awards-label{color:#0a7d2c}
  .prose strong,.exp-summary strong{color:#111}
  .bullets strong{color:#0a7d2c}
  .link{border-color:#ccc; color:#333}
  .card:hover,.exp,.card,.stat,.skill-group{box-shadow:none; transform:none}
  .reveal{opacity:1; transform:none}
  a[href^="http"]::after{content:" (" attr(href) ")"; font-size:8px; color:#666}
}
"""

# Denser profile for the single-page variant (body gets class "compact").
COMPACT_CSS = r"""
body.compact{font-size:12.5px; line-height:1.4}
body.compact .term{margin:14px auto}
body.compact .body{padding:6px 24px 16px}
body.compact .hero{padding:12px 0 2px}
body.compact .hero-grid{gap:18px}
body.compact .name{font-size:clamp(26px,4vw,40px); margin:2px 0 2px}
body.compact .role{font-size:16px}
body.compact .subrole{margin:0 0 5px; font-size:12.5px}
body.compact .meta{margin:0 0 8px; font-size:12px}
body.compact .photo{width:104px; height:104px}
body.compact .scroll-hint{display:none}
body.compact .cmd-line{margin:0 0 6px; font-size:12px}
body.compact .section{padding:11px 0}
body.compact .prose{margin:4px 0 0; font-size:12.5px}
body.compact .bullets{margin:5px 0 0}
body.compact .bullets li{margin:3px 0; font-size:12.5px}
body.compact .cards{gap:10px}
body.compact .card{padding:13px}
body.compact .skill-grid{gap:10px}
body.compact .skill-group{padding:11px}
body.compact .reveal{opacity:1; transform:none; transition:none}
body.compact .links{gap:7px}
body.compact .link{padding:6px 10px; font-size:12px}
@media print{
  body.compact{font-size:9.2px; line-height:1.32}
  body.compact .term{margin:0}
  body.compact .section{padding:7px 0; border-top:1px solid #ddd}
  body.compact .name{font-size:26px}
}
"""

JS = r"""
(function(){
  // typewriter for hero command
  var typed = document.getElementById('typed');
  var text = 'whoami --role "__ROLE_SLUG__"';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(typed){
    if(reduce){ typed.textContent = text; }
    else{
      var i=0;
      (function tick(){
        if(i<=text.length){ typed.textContent = text.slice(0,i); i++; setTimeout(tick, 38); }
      })();
    }
  }
  // scroll reveal
  var els = document.querySelectorAll('.reveal');
  if('IntersectionObserver' in window && !reduce){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
    }, {threshold:0.12});
    els.forEach(function(el){ io.observe(el); });
  } else {
    els.forEach(function(el){ el.classList.add('in'); });
  }
})();
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
    nav = (
        '<nav>'
        '<a href="#about">about</a><a href="#skills">skills</a>'
        '<a href="#experience">experience</a><a href="#projects">projects</a>'
        '<a href="#education">education</a><a href="#contact">contact</a>'
        "</nav>"
    )
    body = (
        build_header(h, compact=compact)
        + build_highlights(data.get("highlights", []))
        + build_summary(data.get("summary", ""))
        + build_skills(data.get("skills", []))
        + build_experience(data.get("experience", []))
        + build_projects(data.get("projects", []))
        + build_workshop(data.get("workshop"))
        + build_education(data.get("education", []), data.get("certifications", []))
        + build_footer(h)
    )
    doc = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{esc(h['name'])} \u2014 {esc(h['tagline'])}</title>\n"
        f'<meta name="description" content="{esc(data.get("summary","").replace("**", "")[:155])}"/>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>\n'
        '<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet"/>\n'
        f"<style>{_themed(CSS)}{COMPACT_CSS if compact else ''}</style>\n</head>\n"
        f"<body class=\"{'compact' if compact else ''}\">\n"
        '<main class="term">\n'
        '<div class="titlebar"><span class="dot r"></span><span class="dot y"></span>'
        f'<span class="dot g"></span><span class="tt">{esc(IDENT["user"])}: ~/resume</span>'
        f"{nav}</div>\n"
        '<div class="body wrap">\n'
        f"{body}\n"
        "</div>\n</main>\n"
        f"<script>{JS.replace('__ROLE_SLUG__', IDENT['role_slug'])}</script>\n</body>\n</html>\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "assets").mkdir(parents=True, exist_ok=True)
    slug = IDENT["slug"]
    if PUBLIC:
        out_file = OUT_DIR / f"{slug}_resume_public.html"
    elif compact:
        out_file = OUT_DIR / f"{slug}_resume_onepage.html"
    else:
        out_file = OUT_DIR / f"{slug}_resume.html"
    out_file.write_text(doc, encoding="utf-8")
    print(f"Wrote {out_file}  ({len(doc):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
