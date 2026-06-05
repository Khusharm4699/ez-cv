#!/usr/bin/env python3
"""Scaffold a personal resume skill from the EZ-CV template.

Copies `template/` into a new per-user skill directory, drops in the user's
`profile.json`, personalizes the skill name, and renders every output once.

    python3 scripts/scaffold.py --name "Maya Iyer" --profile /path/to/profile.json
    python3 scripts/scaffold.py --name "Maya Iyer" --profile p.json --dest ~/cv-skill
    python3 scripts/scaffold.py --name "Maya Iyer" --profile p.json --no-render

The result is a self-contained skill: edit its `data/profile.json`, re-run its
build scripts, and all resume formats update. EZ-CV never hosts or pushes
anything; publishing is a separate, explicit step.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "template"
_IGNORE = shutil.ignore_patterns("output", "__pycache__", "*.pyc")


def slugify(value, sep="_"):
  """Lowercase and collapse non-alphanumerics to `sep`."""
  out = re.sub(r"[^a-z0-9]+", sep, str(value).lower()).strip(sep)
  return out or "resume"


def personalize_skill_md(skill_md, full_name, skill_name):
  """Rewrite the template SKILL.md frontmatter name + title for this user.

  Args:
    skill_md: Path to the copied SKILL.md.
    full_name: The person's full name (for the title line).
    skill_name: The lowercase-hyphen skill id to set in frontmatter.
  """
  text = skill_md.read_text(encoding="utf-8")
  text = text.replace("name: PERSONAL_RESUME_SKILL", f"name: {skill_name}")
  text = text.replace(
      "# Personal Resume Skill (EZ-CV)",
      f"# {full_name} — Resume Skill (built with EZ-CV)",
  )
  skill_md.write_text(text, encoding="utf-8")


def render_all(dest):
  """Run every build script once so the skill ships with fresh outputs."""
  scripts = dest / "scripts"
  commands = [
      ["build_html.py"],
      ["build_html.py", "--compact"],
      ["build_html.py", "--public"],
      ["build_html_ai.py"],
      ["build_html_ai.py", "--public"],
      ["build_html_editorial.py"],
      ["build_html_editorial.py", "--public"],
      ["build_html_sidebar.py"],
      ["build_html_sidebar.py", "--public"],
      ["build_text.py"],
      ["build_text.py", "--compact"],
  ]
  for command in commands:
    result = subprocess.run(
        [sys.executable, str(scripts / command[0]), *command[1:]],
        capture_output=True, text=True, check=False,
    )
    label = " ".join(command)
    if result.returncode != 0:
      print(f"  [FAIL] {label}\n{result.stderr.strip()}")
      return False
    print(f"  [ok] {label}")
  return True


def main():
  """Parse args, clone the template, write the profile, render outputs."""
  parser = argparse.ArgumentParser(description="Scaffold a personal resume skill.")
  parser.add_argument("--name", required=True, help="Full name of the person.")
  parser.add_argument("--profile", required=True,
                      help="Path to the user's profile.json.")
  parser.add_argument("--dest", default=None,
                      help="Destination dir (default ~/.cursor/skills/<slug>-resume).")
  parser.add_argument("--no-render", action="store_true",
                      help="Skip rendering outputs after scaffolding.")
  args = parser.parse_args()

  profile_path = Path(args.profile).expanduser()
  if not profile_path.is_file():
    print(f"Profile not found: {profile_path}")
    return 1
  try:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
  except json.JSONDecodeError as error:
    print(f"Profile is not valid JSON: {error}")
    return 1

  slug = slugify(args.name, "-")
  dest = Path(args.dest).expanduser() if args.dest else (
      Path.home() / ".cursor" / "skills" / f"{slug}-resume")
  if dest.exists():
    print(f"Destination already exists: {dest}\nChoose a different --dest.")
    return 1

  shutil.copytree(TEMPLATE, dest, ignore=_IGNORE)
  (dest / "data").mkdir(parents=True, exist_ok=True)
  (dest / "data" / "profile.json").write_text(
      json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
  personalize_skill_md(dest / "SKILL.md", args.name, f"{slug}-resume")

  print(f"Scaffolded {slug}-resume at:\n  {dest}")
  if args.no_render:
    print("Skipped rendering (--no-render). Run the build scripts when ready.")
    return 0

  print("Rendering outputs:")
  if not render_all(dest):
    print("Rendering failed. Fix profile.json and re-run the build scripts.")
    return 1
  print(f"\nDone. Outputs in {dest / 'output'}")
  print("Next: run `python3 scripts/humanize_scan.py` and fix any hard FAIL.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
