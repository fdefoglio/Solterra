```markdown
# Final Dutch quality review prompt (EN→NL manual translations)

Replace `<FILE>` with the filename before sending. Attach the file, and the client's approved terminology list (`terminology.csv`), in the same message.

---

**Task:** Final pre-delivery review of the Dutch column in `<FILE>` against its English source column. Work in two passes over the whole file:

- **Horizontal (EN→NL), row by row.** Compare each Dutch cell against its English cell. Look for: mistranslation; reversed or misscoped negation; information dropped or added; a hedge lost or added (*may*, *can* stated as fact, or a flat statement hedged); wrong names, dates, figures or organisations; English left untranslated; cells duplicated from an adjacent row or left empty; grammatical errors in Dutch (duplicated verbs, wrong inflection, broken word order); changed or corrupted embedded markup and HTML entities (`<power switch>`, `&lt;`, `&gt;`).
- **Vertical (NL only), top to bottom.** Read the Dutch column as one continuous document, with the English covered. Look for: terminology drift (the same source term rendered differently in different rows); register drift (formal `u` vs `je`, imperative vs declarative); inconsistent capitalisation, quotation style, hyphenation, heading case, and formatting of units/abbreviations (`12V` vs `12 V`, `gps` vs `GPS`); recurring formula phrases rendered differently across rows; duplicated cells.

Read every row. Do not sample or spot-check.

**Client terminology (binding):**

The attached `terminology.csv` is the client's approved list. Every entry is binding, whether it was mandated by the client or standardised by the translator; the list decides over the Translation Memory, over earlier batches and over your own preference.

- Match case-insensitively on whole words, longest entry first. An inflected form or an inserted article is not a deviation (*het voorgaande voertuig*, *de 12V-batterij*).
- A Dutch cell that renders a listed English term with anything other than the listed Dutch is a finding, even when the alternative reads well.
- Naturalness never overrides terminology: do not swap a listed term for a synonym to improve flow or to avoid repetition. Recast the sentence around the term instead.
- If a listed entry itself looks wrong (meaning error, truncated or malformed row), raise it in `notes` as a question for the translator; do not "correct" the term in the Dutch.
- If no term is listed and the file renders one concept in competing ways, propose one form, cite the rows, and say which form the majority uses.

**Dutch naturalness standard (applies to every cell):**

This is a technical manual. There is no fixed house style, but the Dutch must read as if written natively in Dutch, not translated from English. Apply these checks in order:

1. **Passive → active (judgment check).** A passive that mirrors the English is the commonest sign of translationese in these manuals. Where a clear agent exists — the reader (`u`), the system, or a named device — and the active reads better, recast: `kan worden opgemaakt` → `kunt u opmaken`; `worden vervangen door nieuwe` → `nieuwe opnamen vervangen de bestaande`; `wanneer de batterij wordt losgekoppeld` (by an accident) → `wanneer de batterij loskomt` (an intransitive verb is often the cleanest active form when nobody acts deliberately).
   Keep the passive when:
   - the agent is unknown or irrelevant (a list of display states: *Het scherm wordt weergegeven*);
   - recasting would break a short UI string, label or heading;
   - the text is a legal notice or disclaimer, where the impersonal register is deliberate;
   - the only possible subject would be *je*, *men*, or an agent the source does not name (do not introduce *wij*, *de fabrikant*, *Toyota* or *SUBARU* as subject unless the English does).
2. **Impersonal constructions.** Replace impersonal `het is … dat` phrasings when an active alternative is natural and the agent is the reader: `het is niet toegestaan` → `mag u niet`; `het is niet mogelijk` → `kan … niet`. Leave guarantees and liability statements impersonal: `het is niet gegarandeerd dat` may be tightened to `er is geen garantie dat`, but not turned into a promise by a named party.
3. **Keep the modality.** A recast must carry the source's hedge across: *may* → `kan` / `mogelijk`. Losing a hedge in a safety or guarantee sentence is RED, not AMBER.
4. **Nominalisations → finite verbs.** Prefer verbs over noun phrases: `bij gebruik van` → `wanneer u … gebruikt`; `ter controle van` → `om … te controleren`.
5. **No calques from English.** Reject word-for-word borrowings of English structure: `in het geval dat` → `als`; `met betrekking tot` → `over/voor`; `is ontworpen om` → `is bedoeld om`; `uitvoeren`/`plaatsvinden` where a plain verb fits; `zal` for English *will* where Dutch uses the present; English `-ing` postmodifiers → Dutch relative clauses; English `of`-chains → Dutch compounds or naturally ordered prepositional phrases.
6. **Word order and concord.** Check Dutch sentence brace structure (verb-final subordinate clauses), placement of adverbs (`ook`, `echter`, `wel`), separable verbs, and agreement of articles/pronouns with their antecedent.
7. **Repetition within a cell.** A content word repeated in one sentence reads as clumsy in Dutch. Prefer elimination (gapping, a compound, `ervan`/`daarvan`, a relative clause) over a synonym, and never synonymise a listed term. An anaphor (`deze`, `die`, `ervan`) is acceptable only if its nearest preceding noun phrase is the antecedent and gender and number agree.
8. **Register.** Formal `u` throughout; imperatives for instructions (`Tik op …`, `Raadpleeg …`).

The annex at the end of this prompt shows the standard with bad → good pairs. Use it as a calibration of the level expected, not as a list of the only patterns to catch.

**Scope of what to raise:**

- If a change is needed for accuracy, for terminology, for Dutch naturalness under the standard above, for consistency, or for conformity to any attached style guide, flag it.
- If the change would swap one acceptable rendering for another equally acceptable one, leave it alone. Preference-level rewrites bury the findings that matter.
- If the defect is in the English source itself (typo, missing verb, truncated sentence, one sentence split across two rows), flag it and describe it in `notes`. If the Dutch cannot be corrected until the source is fixed, put `(no change — see note)` in `to_replace`.
- If the same issue recurs across many rows, file it once as a single pattern finding: quote one representative row in `original_translation` and list every affected row in `row_ref`. Filing the same pattern twenty times obscures the rest.
- If a proposed correction rests on outside knowledge rather than on the source (a legal term, a company name, a statutory title), say so in `notes` instead of presenting it as a straight translation fix.

**Why:** This is the last check before delivery to the client, so it needs a bird's-eye view across the full document that catches what row-by-row translation cannot: drift between batches, terminology slipping from the approved list, and errors that only become visible when the Dutch is read on its own.

**Guardrails:**

- Do not modify `<FILE>` or `terminology.csv`. Write the findings to a separate file.
- `original_translation` is copied verbatim from the Dutch cell, and long enough to be located by a unique search.
- `to_replace` is a drop-in replacement for that exact string — same information, nothing added, nothing removed. Preserve embedded markup, HTML entities, placeholders and conditional-text markers (`<power switch>`) exactly.
- Every finding cites its row number.
- Before delivering, verify programmatically that each `original_translation` string actually occurs in the source file, and that every `to_replace` keeps the listed terms of the string it replaces, and report the result.

**What the output looks like:** One CSV, `<FILE>_findings.csv`, with these columns, in this order:

`"row_ref","severity","original_translation","to_replace","notes"`

- `severity` is one of:
  - **RED** — meaning is wrong or content is missing: wrong name, date or figure; reversed negation; lost or added hedge; omitted, duplicated or untranslated content; a listed client term replaced by another word; a Dutch grammar error that breaks the sentence (e.g., duplicated verb); changed or corrupted markup.
  - **AMBER** — meaning holds but the Dutch is unidiomatic or inconsistent: passive where an active with a clear agent reads better, impersonal construction with a natural active alternative, calque, nominalisation, repetition within a cell, drift between rows for a term that is not on the list, register drift.
  - **GREEN** — cosmetic or mechanical: whitespace, trailing spaces, punctuation, hyphenation, capitalisation, heading case, unit/abbreviation formatting.
- Sort RED first, then AMBER, then GREEN; within each, by row number.
- `notes`: one or two sentences — what is wrong and why the replacement is right. Where the point is a translation one, quote the English word or phrase at issue. Where it is a terminology one, quote the list entry. Where it is a consistency one, cite the rows that disagree.

Return the CSV. In chat, list only the RED findings, one line each, and nothing further.

---

## Annex — naturalness standard: bad → good

Each pair shows the level expected. The bad version is grammatical but reads as translated; the good version is what a Dutch technical author would write.

**Passive → active (clear agent)**

| English | Bad (translated) | Good (native) |
| --- | --- | --- |
| If it cannot be ascertained from the recording … | Als dit niet uit het beeld kan worden opgemaakt … | Als u dit niet uit het beeld kunt opmaken … |
| … an impact may not be detected correctly | … wordt een botsing mogelijk niet correct gedetecteerd | … detecteert de rijrecorder een botsing mogelijk niet correct |
| If the 12-volt battery is disconnected due to a traffic accident … | Als de 12V-batterij door een verkeersongeval wordt losgekoppeld … | Als de 12V-batterij door een verkeersongeval loskomt … |
| When the vehicle is started after … | Wanneer het voertuig wordt gestart nadat … | Wanneer u het voertuig start nadat … |
| … the clock will require resetting … | … zal de klok opnieuw moeten worden ingesteld … | … moet u de klok opnieuw instellen … |

**Passive kept (correctly)**

| English | Keep | Why |
| --- | --- | --- |
| The guide lines are not displayed | De geleidingslijnen worden niet weergegeven | Display state; no agent |
| … is not liable for any damages … | … is niet aansprakelijk voor schade … | Disclaimer; impersonal by design |

**Impersonal, calque and future**

| English | Bad (translated) | Good (native) |
| --- | --- | --- |
| It is not allowed to use recordings … | Het is niet toegestaan om opnamen te gebruiken … | U mag opnamen niet gebruiken … |
| The drive recorder is designed to record … | De rijrecorder is ontworpen om op te nemen … | De rijrecorder is bedoeld om op te nemen … |
| The light will illuminate. | Het lampje zal gaan branden. | Het lampje gaat branden. |
| In the event that the system … | In het geval dat het systeem … | Als het systeem … |
| Adhere to local laws when using … | Houd u aan lokale wetten bij het gebruik van … | Houd u aan de plaatselijke wetgeving wanneer u … gebruikt. |

**Hedges and meaning**

| English | Bad (translated) | Good (native) |
| --- | --- | --- |
| … may infringe upon the privacy … | … maken inbreuk op de privacy … | … kunnen inbreuk maken op de privacy … |
| … voice guidance may be made early or late. | … worden de gesproken instructies in een vroeg of laat stadium gegeven. | … kan de stembegeleiding te vroeg of te laat klinken. |

**Repetition within a cell**

| English | Bad (translated) | Good (native) |
| --- | --- | --- |
| … obtain the latest map data when the USB memory containing the latest map data is inserted. | … wanneer de USB-stick met de nieuwste kaartgegevens met de nieuwste kaartgegevens … | … door een USB-stick aan te sluiten waarop deze gegevens staan. |
| … the route will be recalculated (after leaving the route). | … van de route afwijkt, wordt de route opnieuw berekend. | … van de geplande route afwijkt, wordt die opnieuw berekend. |
| … the shadow of the vehicle under the vehicle … | … schaduwen van het voertuig onder het voertuig … | … schaduwen onder het voertuig, waaronder de eigen schaduw … |

**Terminology over flow**

| English | Bad (reads well, wrong term) | Good (listed term) |
| --- | --- | --- |
| route guidance | routebegeleiding | routegeleiding |
| voice guidance | gesproken instructies | stembegeleiding |
| road conditions | wegomstandigheden | rijomstandigheden |
```
