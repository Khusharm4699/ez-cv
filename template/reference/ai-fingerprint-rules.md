# AI-Fingerprint Rules (write like a human)

Adapted from ARPeeketi/claude-resume-kit (`resume_builder/support/ai_fingerprint_rules.md`).
Run `scripts/humanize_scan.py` to check these deterministically before declaring done.

## 1. Banned words

**Tier 1 — dead giveaways (never use):** delve, tapestry, multifaceted, pivotal,
realm, synergy, paradigm, holistic, nuanced, foster, embark, leverage (verb),
utilize, harness, spearhead, cornerstone, landscape (metaphorical), journey
(metaphorical), cutting-edge, groundbreaking, innovative (unless quoting a JD).

**Banned adjectives -> replacement:** robust -> strong/reliable; comprehensive ->
thorough/broad; pivotal -> key/central; meticulous -> careful/precise; diverse ->
varied; extensive -> broad/deep.

**Banned verbs -> replacement:** leverage -> use/apply; utilize -> use; harness ->
apply; spearhead -> lead/start; foster -> support/grow; facilitate -> run/enable;
showcase -> show; underscore -> highlight; bolster -> strengthen.

**Banned adverbs:** meticulously, notably, subsequently (use "then"/"later"),
remarkably, seamlessly, thereby.

Technical exceptions: "landscape" when literal (threat landscape); "novel" when
quoting a JD verbatim.

## 2. Banned phrases

"in today's...", "at the forefront of", "it is worth noting that", "this experience
has taught me", "uniquely positioned to", "in an era of", "proven track record",
"passionate about", "excited to apply", "demonstrated ability to", "strong
foundation in", "well-versed in", "adept at", "at the intersection of X and Y".

## 3. Structural rules

- **No "-ing" analysis endings on bullets — the #1 AI marker.** A bullet must end on
  a concrete result, metric, or object, not "...enabling X" / "...improving Y".
  Ending with a metric ("...a 15% drop") is fine.
- **No reframe pattern:** never "It's not X, it's Y".
- **No rhetorical question + answer.**
- **No gerund-fragment stacking** (3+ "-ing" phrases in a row).
- **Max 2 em-dashes per document.** Prefer commas, periods, parentheses, colons.
  Use the same rule for role-title and education separators.
- **Vary sentence length:** mix 8-12 word sentences with 20-30 word ones. Three
  consecutive same-length sentences flag as AI.
- **Triplets (<=2 per document):** avoid "X, Y, and Z" in more than 2 sentences.
  Lists of named tools/entities are fine (they are a positive human marker); the
  cap targets abstract/adjective triplets.

## 4. Positive human markers

Specific numbers and named entities; front-loaded specifics; short connectors
("so", "but", "then") over "consequently"/"additionally"; first-person "I built"
over "was responsible for"; deliberate sentence-length variety; occasional "And"/
"But" openers; one concrete detail over generic framing.

## 5. The 12-item scan (gate before sending)

`scripts/humanize_scan.py` enforces items 1-8 deterministically (banned words,
banned verbs/adverbs, banned phrases, em-dash count, -ing bullet endings, abstract
triplets, sentence-length variety, passive-voice ratio). The remaining manual
checks:

9.  Titles / dates / companies exactly correct?
10. Every claim has provenance (verified / estimate / placeholder)?
11. Reads aloud like a person talking, not a brochure?
12. Would a skeptical senior engineer believe every line?

If any hard item fails, fix it in `data/profile.json` and regenerate. These are
detectable AI patterns, not optional polish.
