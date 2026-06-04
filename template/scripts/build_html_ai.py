#!/usr/bin/env python3
"""Render profile.json into an AI-assistant / chat-UI themed one-page resume.

A second visual treatment alongside the terminal theme. It frames the resume as
a conversation with an AI assistant: a chat hero, "tool call" cards for the
agentic work, token chips for skills, and an aurora/mesh gradient with a faint
neural-node motif. Deterministic and dependency-free.

    python3 scripts/build_html_ai.py

Output: output/<slug>_resume_onepage_ai.html  (condensed, prints to 1 A4)
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

# When True (--public), the phone number is omitted (email + links kept).
PUBLIC = False

# Identity token bundle, filled in main() from the profile header.
IDENT = {}


def esc(value):
    return html.escape(str(value), quote=True)


def rich(value):
    """Escape text and render **bold** + auto-bolded metrics as <strong>."""
    return "".join(
        f"<strong>{esc(seg)}</strong>" if bold else esc(seg)
        for seg, bold in spans(value)
    )


def sparkle(size=16):
    return (
        f'<svg class="spark" viewBox="0 0 24 24" width="{size}" height="{size}" '
        'fill="currentColor" aria-hidden="true">'
        '<path d="M12 2l1.8 5.4L19 9.2l-5.2 1.8L12 16l-1.8-5L5 9.2l5.2-1.8L12 2z"/>'
        '<path d="M19 14l.9 2.6L22.5 17l-2.6.9L19 20.5l-.9-2.6L15.5 17l2.6-.4L19 14z"/>'
        "</svg>"
    )


def link_chip(label, url):
    return (
        f'<a class="chip link" href="{esc(url)}" target="_blank" rel="noopener">'
        f"{esc(label)}</a>"
    )


def build_hero(d):
    h = d["header"]
    links = "".join(link_chip(l["label"], l["url"]) for l in h.get("links", []))
    contact = f'<a class="chip link" href="mailto:{esc(h["email"])}">{esc(h["email"])}</a>'
    if not PUBLIC and h.get("phone"):
        contact += f'<a class="chip link" href="tel:{esc(h["phone"])}">{esc(h["phone"])}</a>'
    return f"""
<section class="hero">
  <div class="bubble user">
    <div class="who">You</div>
    <div class="msg">Tell me about {esc(h['name'])}.</div>
  </div>
  <div class="bubble bot">
    <div class="avatar" aria-hidden="true"><span class="orb"></span>{sparkle(18)}</div>
    <div class="msg">
      <div class="who">{esc(IDENT['ai_id'])} <span class="model-chip">assistant</span></div>
      <h1 class="name">{esc(h['name'])}</h1>
      <p class="tagline">{esc(h['tagline'])} <span class="sep">/</span> {esc(h.get('current_role',''))}</p>
      <p class="loc">{esc(h.get('location',''))}</p>
      <p class="summary">{rich(d.get('summary',''))}<span class="cursor">▍</span></p>
      <div class="chips">{links}{contact}</div>
    </div>
  </div>
</section>
"""


def build_highlights(items):
    if not items:
        return ""
    cards = "".join(
        f'<div class="stat"><div class="stat-num">{esc(it["stat"])}</div>'
        f'<div class="stat-label">{esc(it["label"])}</div></div>'
        for it in items
    )
    return f"""
<section class="block">
  <div class="block-head">{sparkle()}<span>Key facts</span></div>
  <div class="stats">{cards}</div>
</section>
"""


def build_skills(skills):
    groups = "".join(
        f'<div class="skill-row"><span class="skill-group">{esc(g["group"])}</span>'
        + "".join(f'<span class="token">{esc(i)}</span>' for i in g["items"])
        + "</div>"
        for g in skills
    )
    return f"""
<section class="block">
  <div class="block-head">{sparkle()}<span>Skills</span></div>
  <div class="skills">{groups}</div>
</section>
"""


def build_experience(items):
    rows = []
    for x in items:
        if x.get("type") == "primary" and x.get("bullets"):
            body = "".join(f"<li>{rich(b)}</li>" for b in x["bullets"])
            body = f'<ul class="bullets">{body}</ul>'
        elif x.get("type") == "collapsed":
            body = f'<p class="card-blurb">{rich(x.get("paragraph", x.get("summary","")))}</p>'
        else:
            body = f'<p class="card-blurb">{rich(x.get("summary",""))}</p>'
        awards = ""
        if x.get("awards"):
            chips = "".join(
                f'<span class="award-chip">★ {esc(a)}</span>' for a in x["awards"]
            )
            awards = f'<div class="awards">{chips}</div>'
        rows.append(
            f'<article class="card"><div class="card-top">'
            f'<h3>{esc(x["role"])}</h3>'
            f'<span class="period">{esc(x["start"])} – {esc(x["end"])}</span></div>'
            f'<div class="card-sub">{esc(x["company"])} '
            f'<span class="role">· {esc(x.get("location",""))}</span></div>'
            f"{body}{awards}</article>"
        )
    return f"""
<section class="block">
  <div class="block-head">{sparkle()}<span>Experience</span></div>
  {"".join(rows)}
</section>
"""


def build_projects(projects):
    rest = [p for p in projects if not p.get("featured")]
    if not rest:
        return ""
    cards = []
    for p in rest:
        links = "".join(
            f'<a class="chip link" href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>'
            for l in p.get("links", [])
        )
        cards.append(
            f'<article class="card"><div class="card-top">'
            f'<h3>{esc(p["name"])}</h3>'
            f'<span class="period">{esc(p.get("period",""))}</span></div>'
            f'<div class="card-sub">{esc(p.get("subtitle",""))} '
            f'<span class="role">· {esc(p.get("role",""))}</span></div>'
            f'<p class="card-blurb">{rich(p.get("blurb",""))}</p>'
            f'<div class="chips">{links}</div></article>'
        )
    return f"""
<section class="block">
  <div class="block-head">{sparkle()}<span>Projects</span></div>
  {"".join(cards)}
</section>
"""


def build_speaking(w):
    if not w:
        return ""
    return f"""
<section class="block">
  <div class="block-head">{sparkle()}<span>Speaking</span></div>
  <article class="card"><div class="card-top"><h3>{esc(w['title'])}</h3>
  <span class="period">{esc(w.get('audience',''))}</span></div>
  <p class="card-blurb">{esc(w.get('blurb',''))}</p></article>
</section>
"""


def build_education(edu, certs):
    erows = "".join(
        f'<div class="edu-row"><span class="edu-school">{esc(e["school"])}</span>'
        f'<span class="edu-deg">{esc(e["degree"])}'
        f'{(" · " + esc(e["note"])) if e.get("note") else ""}</span>'
        f'<span class="edu-year">{esc(e["year"])}</span></div>'
        for e in edu
    )
    crows = "".join(
        f'<div class="edu-row"><span class="edu-school">{esc(c["name"])}</span>'
        f'<span class="edu-deg">Certification</span>'
        f'<span class="edu-year">{esc(c["year"])}</span></div>'
        for c in certs
    )
    return f"""
<section class="block">
  <div class="block-head">{sparkle()}<span>Education &amp; certifications</span></div>
  <div class="edu">{erows}{crows}</div>
</section>
"""


def build_footer(h):
    return f"""
<footer class="composer">
  <div class="composer-box">
    <span class="composer-hint">Ask a follow-up about {esc(h['name'])}…</span>
    <a class="send" href="mailto:{esc(h['email'])}" title="Email">{sparkle(16)} send</a>
  </div>
  <div class="foot-note">Generated from a single knowledge base · deterministic render · {esc(h['name'])}</div>
</footer>
"""


CSS = r"""
:root{
  --bg:#0a0a16; --ink:#ECECF6; --dim:#A9AAC4; --line:rgba(255,255,255,.08);
  --glass:rgba(255,255,255,.045); --glass2:rgba(255,255,255,.03);
  --v:#8B5CF6; --c:#22D3EE; --m:#EC4899; --grad:linear-gradient(135deg,#8B5CF6,#22D3EE 55%,#EC4899);
  --r:18px;
  --sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; color:var(--ink); font-family:var(--sans); font-size:14px; line-height:1.55;
  -webkit-font-smoothing:antialiased; background:#06060f; position:relative; overflow-x:hidden;
}
/* aurora mesh background */
.aurora{position:fixed; inset:-20% -10% auto -10%; height:80vh; z-index:-2; filter:blur(70px); opacity:.55;
  background:
    radial-gradient(40% 50% at 20% 30%, rgba(139,92,246,.65), transparent 60%),
    radial-gradient(40% 50% at 75% 20%, rgba(34,211,238,.55), transparent 60%),
    radial-gradient(45% 55% at 60% 70%, rgba(236,72,153,.5), transparent 60%);
  animation:drift 16s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate3d(0,4%,0) scale(1.05)}}
.grid-bg{position:fixed; inset:0; z-index:-1;
  background-image:radial-gradient(rgba(255,255,255,.05) 1px, transparent 1px);
  background-size:26px 26px; mask-image:linear-gradient(180deg,transparent,black 12%,black 88%,transparent)}

.wrap{max-width:880px; margin:0 auto; padding:28px 22px 40px}

/* chat bubbles */
.hero{display:flex; flex-direction:column; gap:14px; margin-bottom:20px}
.bubble{display:flex; gap:12px; align-items:flex-start}
.bubble.user{justify-content:flex-end}
.bubble.user .msg{background:var(--glass); border:1px solid var(--line); border-radius:16px 16px 4px 16px;
  padding:9px 14px; color:var(--dim); font-size:13.5px}
.bubble.user .who{display:none}
.bubble.bot{align-items:flex-start}
.avatar{position:relative; flex:0 0 44px; width:44px; height:44px; border-radius:14px;
  display:grid; place-items:center; color:#fff; background:var(--grad);
  box-shadow:0 10px 30px -10px rgba(139,92,246,.7)}
.avatar .orb{position:absolute; inset:0; border-radius:14px; background:var(--grad); filter:blur(10px); opacity:.6; animation:pulse 3s ease-in-out infinite}
@keyframes pulse{50%{opacity:.95}}
.spark{filter:drop-shadow(0 0 6px rgba(255,255,255,.4))}
.bubble.bot .msg{flex:1; background:linear-gradient(180deg,var(--glass),var(--glass2));
  border:1px solid var(--line); border-radius:6px 18px 18px 18px; padding:16px 18px;
  backdrop-filter:blur(8px)}
.who{font-size:12px; color:var(--dim); margin-bottom:4px; font-weight:600; letter-spacing:.02em}
.model-chip{font-family:var(--mono); font-size:10px; padding:1px 7px; border-radius:20px;
  background:rgba(139,92,246,.18); color:#C4B5FD; border:1px solid rgba(139,92,246,.35); margin-left:6px}
.name{margin:2px 0 2px; font-size:34px; line-height:1.05; letter-spacing:-.5px; font-weight:800;
  background:linear-gradient(90deg,#fff,#C4B5FD); -webkit-background-clip:text; background-clip:text; color:transparent}
.tagline{margin:0; font-size:15px; font-weight:600;
  background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent}
.tagline .sep{opacity:.5}
.loc{margin:1px 0 8px; color:var(--dim); font-size:12.5px}
.summary{margin:0 0 12px; color:#D7D8EC; font-size:13.5px}
.cursor{color:var(--c); animation:blink 1.1s steps(1) infinite; font-weight:700}
@keyframes blink{50%{opacity:0}}

.chips{display:flex; flex-wrap:wrap; gap:7px}
.chip{font-size:12px; padding:5px 11px; border-radius:20px; border:1px solid var(--line);
  background:var(--glass); color:var(--dim); text-decoration:none; transition:all .18s ease}
.chip.link:hover{color:#fff; border-color:transparent; background:var(--grad); transform:translateY(-1px)}

/* blocks */
.block{margin:18px 0}
.block-head{display:flex; align-items:center; gap:8px; color:#fff; font-weight:700; font-size:13px;
  letter-spacing:.04em; text-transform:uppercase; margin:0 0 10px}
.block-head .spark{color:var(--v)}

.stats{display:grid; grid-template-columns:repeat(3,1fr); gap:10px}
.stat{border:1px solid var(--line); border-radius:14px; padding:12px 14px;
  background:linear-gradient(180deg,var(--glass),var(--glass2))}
.stat-num{font-size:19px; font-weight:800; background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent}
.stat-label{font-size:11.5px; color:var(--dim); margin-top:2px}

.card{border:1px solid var(--line); border-radius:16px; padding:15px 16px; margin:10px 0;
  background:linear-gradient(180deg,var(--glass),var(--glass2)); backdrop-filter:blur(6px)}
.card.featured{border-color:transparent; position:relative;
  background:linear-gradient(180deg,rgba(139,92,246,.12),rgba(34,211,238,.05));
  box-shadow:0 0 0 1px rgba(139,92,246,.4), 0 24px 60px -34px rgba(34,211,238,.5)}
.card-top{display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap}
.card-top h3{margin:0; font-size:16px; color:#fff}
.badge{margin-left:9px; font-size:10px; text-transform:uppercase; letter-spacing:.1em;
  padding:2px 8px; border-radius:20px; color:#06060f; background:var(--grad); font-weight:800; vertical-align:middle}
.period{font-size:11.5px; color:var(--dim); font-family:var(--mono)}
.card-sub{font-size:12.5px; margin-top:2px; background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent}
.card-sub .role{color:var(--dim); -webkit-text-fill-color:var(--dim)}
.card-blurb{margin:8px 0 0; color:#CFD0E6; font-size:12.8px}
.bullets{margin:8px 0 0; padding-left:18px}
.bullets li{margin:5px 0; color:#CFD0E6; font-size:12.8px}
.bullets li::marker{color:var(--c)}
.awards{margin-top:9px; display:flex; flex-wrap:wrap; gap:6px}
.award-chip{font-size:11.5px; padding:4px 10px; border-radius:20px; color:#F4D58D;
  border:1px solid rgba(244,213,141,.4); background:rgba(244,213,141,.08)}

/* tool-call styling for the AI suite */
.tool-calls{margin-top:10px; display:flex; flex-direction:column; gap:6px}
.tool-call{display:flex; gap:8px; align-items:baseline; padding:7px 10px; border-radius:10px;
  background:rgba(0,0,0,.25); border:1px solid var(--line)}
.tool-call .fn{font-family:var(--mono); font-size:11.5px; color:#7DE3F4; white-space:nowrap}
.tool-desc{font-size:12px; color:#C7C8DE}
.subtools{display:flex; flex-wrap:wrap; gap:6px; margin-top:9px}
.subtool{font-family:var(--mono); font-size:11px; padding:3px 8px; border-radius:8px;
  background:rgba(139,92,246,.14); border:1px solid rgba(139,92,246,.3); color:#C4B5FD}

/* skills */
.skills{display:flex; flex-direction:column; gap:7px}
.skill-row{display:flex; flex-wrap:wrap; gap:6px; align-items:center}
.skill-group{font-size:11.5px; color:var(--dim); min-width:118px; font-weight:600}
.token{font-size:11.5px; padding:3px 9px; border-radius:8px; border:1px solid var(--line);
  background:var(--glass); color:#D7D8EC}

/* education */
.edu{display:flex; flex-direction:column; gap:5px}
.edu-row{display:grid; grid-template-columns:1fr auto auto; gap:10px; align-items:baseline;
  padding:7px 0; border-bottom:1px dashed var(--line); font-size:12.5px}
.edu-school{color:#fff; font-weight:600}
.edu-deg{color:var(--dim)}
.edu-year{color:#7DE3F4; font-family:var(--mono); font-size:11.5px}

/* composer */
.composer{margin-top:22px}
.composer-box{display:flex; align-items:center; justify-content:space-between; gap:12px;
  border:1px solid var(--line); border-radius:30px; padding:10px 10px 10px 18px;
  background:var(--glass); backdrop-filter:blur(8px)}
.composer-hint{color:var(--dim); font-size:13px}
.send{display:inline-flex; align-items:center; gap:6px; text-decoration:none; color:#fff;
  font-size:12.5px; font-weight:700; padding:9px 16px; border-radius:22px; background:var(--grad)}
.foot-note{text-align:center; color:var(--dim); font-size:11px; margin-top:12px; opacity:.8}

@media (max-width:640px){
  .stats{grid-template-columns:1fr 1fr}
  .skill-group{min-width:auto; width:100%}
  .edu-row{grid-template-columns:1fr auto}
  .edu-deg{display:none}
}
@media (prefers-reduced-motion:reduce){
  .aurora{animation:none} .avatar .orb{animation:none} .cursor{animation:none}
}

/* print: keep the look but flatten to 1 A4 with readable contrast */
@media print{
  @page{size:A4; margin:9mm}
  body{background:#fff; color:#14141f; font-size:9.3px; line-height:1.32}
  .aurora,.grid-bg{display:none}
  .wrap{max-width:none; padding:0}
  .hero{gap:6px; margin-bottom:8px}
  .bubble.user{display:none}
  .avatar{box-shadow:none}
  .bubble.bot .msg{background:#fff; border:none; padding:0; backdrop-filter:none}
  .name{font-size:21px; color:#1c1130; -webkit-text-fill-color:#1c1130}
  .tagline,.card-sub,.stat-num{-webkit-text-fill-color:#6d28d9; color:#6d28d9}
  .summary,.card-blurb,.bullets li,.tool-desc{color:#26263a}
  .block{margin:7px 0}
  .block-head{color:#1c1130; margin-bottom:4px}
  .block-head .spark{color:#6d28d9}
  .card{margin:5px 0; padding:7px 9px; border:1px solid #e5e2f0; background:#fff;
    box-shadow:none; backdrop-filter:none; break-inside:avoid}
  .card.featured{border:1px solid #c4b5fd; box-shadow:none}
  .stat{border:1px solid #e5e2f0; padding:6px 9px; background:#fff}
  .tool-call{background:#f6f5fc; border:1px solid #ece9f7; padding:3px 7px}
  .tool-call .fn{color:#0e7490}
  .token,.subtool,.chip{border:1px solid #e5e2f0; background:#f7f7fb; color:#33334a}
  .award-chip{border:1px solid #e7d9a8; background:#fbf6e6; color:#7a5c12}
  .edu-year,.tool-call .fn{color:#0e7490}
  .cursor{display:none}
  .composer{display:none}
  a{color:#6d28d9; text-decoration:none}
}
"""


def main():
    global PUBLIC, IDENT
    PUBLIC = "--public" in sys.argv[1:]
    data = condense(json.loads(PROFILE.read_text(encoding="utf-8")))
    IDENT = identity(data["header"])
    h = data["header"]
    projects = data.get("projects", [])
    body = (
        build_hero(data)
        + build_highlights(data.get("highlights", []))
        + build_skills(data.get("skills", []))
        + build_experience(data.get("experience", []))
        + build_projects(projects)
        + build_speaking(data.get("workshop"))
        + build_education(data.get("education", []), data.get("certifications", []))
        + build_footer(h)
    )
    doc = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{esc(h['name'])} \u2014 {esc(h['tagline'])}</title>\n"
        f'<meta name="description" content="{esc(data.get("summary","").replace("**", "")[:155])}"/>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>\n'
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        '<div class="aurora" aria-hidden="true"></div>\n'
        '<div class="grid-bg" aria-hidden="true"></div>\n'
        f'<main class="wrap">\n{body}\n</main>\n'
        "</body>\n</html>\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = IDENT["slug"]
    if PUBLIC:
        out_file = OUT_DIR / f"{slug}_resume_ai_public.html"
    else:
        out_file = OUT_DIR / f"{slug}_resume_onepage_ai.html"
    out_file.write_text(doc, encoding="utf-8")
    print(f"Wrote {out_file}  ({len(doc):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
