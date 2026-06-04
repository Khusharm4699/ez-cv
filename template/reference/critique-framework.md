# Critique Framework

Independent, fresh-eyes review of the generated resume. Run in a clean pass.

## Five reader personas

1. **ATS bot** — does it parse? are JD keywords present with exact spelling?
2. **Recruiter (6-second scan)** — name, role, top company, 2–3 metrics jump out?
3. **Hiring manager** — does the impact match the seniority and the role's needs?
4. **Domain expert** — are the technical claims precise and believable?
5. **Skeptic** — which line would I challenge in the interview? is it defensible?

## Eight scoring dimensions (1–5 each)

| Dimension | Looks for |
|---|---|
| Relevance | Tailored to this JD's must-haves |
| Impact | Quantified outcomes, not duties |
| Clarity | Plain language, scannable |
| Credibility | Claims match level; provenance solid |
| Keyword fit | ATS coverage of JD terms |
| Voice | Human, not AI-generated feel |
| Structure | Hierarchy, ordering, length |
| Differentiation | Stands out vs a generic candidate |

## Output

- Score table + the 3 highest-leverage fixes.
- Flag every line a skeptic would challenge, with a suggested defensible rewrite.
- Re-run `keyword_audit.py` and the AI-fingerprint 12-item scan as part of the pass.
