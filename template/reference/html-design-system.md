# HTML Design System (terminal / OLED theme)

Derived from `ui-ux-pro-max` `--design-system` for a developer terminal portfolio.
Implemented in `scripts/build_html.py`. Edit tokens there (the `CSS` `:root` block).

## Tokens

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0F172A` | OLED-dark background |
| `--surface` | `#111A2E` | cards / terminal body |
| `--fg` | `#F8FAFC` | primary text |
| `--fg-dim` | `#94A3B8` | secondary text, prompts |
| `--accent` | `#22C55E` (override via `header.theme.accent`) | CTAs, prompt user, stats |
| `--blue` | `#38BDF8` | paths, skill chips |
| `--border` | `#1F2A40` | hairlines |
| font | JetBrains Mono | terminal/monospace mood |

## Principles (from ui-ux-pro-max quick reference)

- Dark-mode only; WCAG AAA contrast; minimal glow (`text-shadow: 0 0 ~16px`).
- SVG icons only — no emoji as icons.
- Hover transitions 150–300ms; visible focus states; `cursor: pointer` on clickables.
- Respect `prefers-reduced-motion` (typewriter + reveal disabled).
- Responsive at 375 / 720 / 1024 / 1440; single-column on mobile.
- Print stylesheet: white background, dark text, chrome hidden, URLs expanded.

## Motifs

- Terminal window chrome (traffic lights + `<handle>: ~/resume` titlebar + nav,
  where `<handle>` comes from the profile header).
- Each section opens with a shell prompt line (`$ cat about.md`, `$ ls skills/`,
  `$ git log experience/`, `$ ./run projects --all`).
- Hero typewriter types a `whoami` command. Metrics render as stat cards.
- Scroll-reveal via IntersectionObserver.

## To restyle

Change the `:root` variables and/or the prompt commands in `build_html.py`, then
re-run it. The theme is data-light and fully regenerable.
