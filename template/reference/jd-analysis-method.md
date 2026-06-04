# JD Analysis Method

Turn a raw job description into a structured target before touching the resume.

## Steps

1. Save the JD to `data/target_jd.txt`.
2. Extract into four buckets:
   - **Must-haves** ("required", "you have", years, core stack).
   - **Nice-to-haves** ("bonus", "ideally", "familiarity with").
   - **Keywords / tools** (named tech: frameworks, DBs, cloud, protocols).
   - **Signals** (culture/role words: "high agency", "customer-facing",
     "production, not demos", "ship fast").
3. Identify the **team/sub-role** if the JD lists several distinct tracks and
   decide which one your evidence fits best.
4. Run `python3 scripts/keyword_audit.py data/target_jd.txt`.
5. Map each must-have to evidence in `profile.json`. Anything with no evidence
   is a **gap** -> `reference/gap-coverage-plan.md` (never fake it).

## Tailoring levers (edit profile.json, then re-render)

- Re-order `skills` groups so the JD's stack is first.
- Re-weight the `summary` opening sentence toward the role's core signal.
- Surface the most JD-relevant project bullets to the top of their list.
- Mirror the JD's exact keyword spelling where truthful (ATS match).

## Signals worth mirroring (when truthful)

production over demos · high agency · customer/stakeholder-facing · end-to-end
ownership · systems thinking (reliability, scale, failure modes) · measurable
impact · clear written communication. Mirror only the signals your evidence
actually supports.
