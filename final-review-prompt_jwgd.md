```markdown
# Final Dutch quality review prompt (EN→NL manual translations)

Replace `<FILE>` with the filename before sending. Attach the file in the same message.

---

**Task:** Final pre-delivery review of the Dutch column in `<FILE>` against its English source column. Work in two passes over the whole file:

- **Horizontal (EN→NL), row by row.** Compare each Dutch cell against its English cell. Look for: mistranslation; reversed or misscoped negation; information dropped or added; wrong names, dates, figures or organisations; English left untranslated; cells duplicated from an adjacent row or left empty; grammatical errors in Dutch (duplicated verbs, wrong inflection, broken word order); changed or corrupted embedded markup and HTML entities (`<power switch>`, `&lt;`, `&gt;`).
- **Vertical (NL only), top to bottom.** Read the Dutch column as one continuous document, with the English covered. Look for: terminology drift (the same source term rendered differently in different rows); register drift (formal `u` vs `je`, imperative vs declarative); inconsistent capitalisation, quotation style, hyphenation, heading case, and formatting of units/abbreviations (`12V` vs `12 V`, `gps` vs `GPS`); recurring formula phrases rendered differently across rows; duplicated cells.

Read every row. Do not sample or spot-check.

**Dutch naturalness standard (applies to every cell):**

This is a technical manual; the Dutch must read as if written natively in Dutch, not translated from English. Apply these checks in order:

1. **Passive → active.** Whenever the agent is recoverable (usually the reader/user, the device, or a named party), prefer the active voice: `kan worden opgemaakt` → `kunt u opmaken`; `is niet gegarandeerd` → `u kunt er niet op rekenen` / `kunnen wij niet garanderen`; `worden vervangen door nieuwe` → `nieuwe opnamen vervangen de bestaande`; `kan worden gekalibreerd` → `kunt u kalibreren`. Keep a passive only when it genuinely has no actor in the source and none can be inferred.
2. **Impersonal constructions.** Replace impersonal `het is … dat` phrasings when an active alternative is natural in Dutch: `het is niet toegestaan` → `mag u niet`; `het is niet mogelijk` → `kan … niet`.
3. **Nominalisations → finite verbs.** Prefer verbs over noun phrases: `bij gebruik van` → `wanneer u … gebruikt`; `ter controle van` → `om … te controleren`.
4. **No calques from English.** Reject word-for-word borrowings of English structure: `in het geval dat` → `als`; `met betrekking tot` → `over/voor`; `uitvoeren`/`plaatsvinden` where a plain verb fits; English `-ing` postmodifiers → Dutch relative clauses; English `of`-chains → Dutch compounds or naturally ordered prepositional phrases.
5. **Word order and concord.** Check Dutch sentence brace structure (verb-final subordinate clauses), placement of adverbs (`ook`, `echter`, `wel`), separable verbs, and agreement of articles/pronouns with their antecedent.
6. **Terminology and register.** One consistent term per concept across the whole file (e.g., `rijrecorder`, `stand van de verkeerslichten`); use the formal `u` consistently; imperatives for instructions.

**Scope of what to raise:**

- If a change is needed for accuracy, for Dutch naturalness under the standard above, for consistency, or for conformity to any attached style guide, flag it.
- If the change would swap one acceptable rendering for another equally acceptable one, leave it alone. Preference-level rewrites bury the findings that matter.
- If the defect is in the English source itself (typo, missing verb, one sentence split across two rows), flag it and describe it in `notes`. If the Dutch cannot be corrected until the source is fixed, put `(no change — see note)` in `to_replace`.
- If the same issue recurs across many rows, file it once as a single pattern finding: quote one representative row in `original_translation` and list every affected row in `row_ref`. Filing the same pattern twenty times obscures the rest.
- If a proposed correction rests on outside knowledge rather than on the source (a legal term, a company name, a statutory title), say so in `notes` instead of presenting it as a straight translation fix.

**Why:** This is the last check before delivery to the client, so it needs a bird's-eye view across the full document that catches what row-by-row translation cannot: drift between batches, and errors that only become visible when the Dutch is read on its own.

**Guardrails:**

- Do not modify `<FILE>`. Write the findings to a separate file.
- `original_translation` is copied verbatim from the Dutch cell, and long enough to be located by a unique search.
- `to_replace` is a drop-in replacement for that exact string — same information, nothing added, nothing removed. Preserve embedded markup and HTML entities exactly.
- Every finding cites its row number.
- Before delivering, verify programmatically that each `original_translation` string actually occurs in the source file, and report the result.

**What the output looks like:** One CSV, `<FILE>_findings.csv`, with these columns, in this order:

`"row_ref","severity","original_translation","to_replace","notes"`

- `severity` is one of:
  - **RED** — meaning is wrong or content is missing: wrong name, date or figure; reversed negation; omitted, duplicated or untranslated content; a Dutch grammar error that breaks the sentence (e.g., duplicated verb); changed or corrupted markup.
  - **AMBER** — meaning holds but the Dutch is unidiomatic or inconsistent: passive where active is required, impersonal construction with a natural active alternative, calque, nominalisation, terminology drift, register drift, deictic anchoring.
  - **GREEN** — cosmetic or mechanical: whitespace, trailing spaces, punctuation, hyphenation, capitalisation, heading case, unit/abbreviation formatting.
- Sort RED first, then AMBER, then GREEN; within each, by row number.
- `notes`: one or two sentences — what is wrong and why the replacement is right. Where the point is a translation one, quote the English word or phrase at issue. Where it is a consistency one, cite the rows that disagree.

Return the CSV. In chat, list only the RED findings, one line each, and nothing further.
```
