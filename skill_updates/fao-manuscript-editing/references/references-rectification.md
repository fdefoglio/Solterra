# References rectification — FAOSTYLE author-date (Phase 7)

Rectify the References/Bibliography section of an already-edited manuscript to
FAOSTYLE author-date bibliographic style. Work on the EDITED file (post-Phase 6),
never the source `_for_ai.md`. Designed for autonomous execution; every judgement
call is pre-decided here or parked as an author action.

## Sources of truth (in order)

1. FAOSTYLE §12.6–12.8 (including the Table 12.1 example list) — now in the
   markdown styleguide `fao_styleguide.md`.
2. The client-supplied exemplar of accepted FAO formatting (`References_e76e2b681_CORRECTED.md`
   in the project files) — where FAOSTYLE text is ambiguous, follow the exemplar.
3. Project `citations-rules.md` rules 54–138.
4. The full rule set for this task: `assets/references_formatting_rules.json`
   (bundled; includes exemplar-derived REF-CASE-002/003, REF-PUB-004) — check every
   entry against every rule ID in it.

## The label-integrity contract (CRITICAL — overrides everything here)

The `[n]` labels are the import key for the client's DOCX pipeline; if the label set
changes, the rectified manuscript cannot be imported and the work is worthless.

- The edited file must contain EXACTLY the same label set as the source, same order,
  one per line start. Never add, renumber, reorder, merge, split or delete a label.
- Everything after `[n] ` is editable; `[n] ` itself — brackets, number, the single
  space — is untouchable.
- Labelled headings keep both label and heading text unchanged (do not retitle
  "Bibliography"/"References" unless instructed — for these manuscripts both are
  correct for their content).
- DELETIONS ARE FORBIDDEN: an entry that must go is struck through in place under
  its own label (`[82] ~~entry~~`); already-struck entries are left exactly as they
  are — do not reformat, do not unstrike.
- INSERTIONS ARE FORBIDDEN: no new entries, no invented labels. Missing content
  (URLs, access dates) is marked with placeholders INSIDE the existing entry and
  logged.
- RE-ORDERING IS FORBIDDEN: the list is already alphabetized; a suspected mis-sort
  is logged, not fixed by moving.
- Mandatory verification BEFORE writing output and AGAIN after all edits: extract
  `^\[(\d+)\]` from source and edited files (`scripts/check_labels.py`); sequences
  must be identical. On mismatch: STOP, revert the offending edit, redo, and record
  the incident in the rectification report.

## Global constraints

- Quoted/foreign titles stay as published: never "correct" spelling inside a title
  (keep "-ise" in a published title); French titles keep French capitalization;
  translate nothing.
- NEVER invent URLs, DOIs, access dates, page numbers or publishers. Missing locators
  get `[URL to be supplied by author.]` / `[Access date to be supplied by author.]`
  plus a log line.
- In-text citations: do not touch, EXCEPT year-suffix normalization when two entries
  end up with the same author+year — then update both the list AND every affected
  in-text instance, and log each.
- Bold authors: bold is mandatory for all author names in every reference list,
  wrapping the entire author string up to and including the period after the final
  author: `**Author, A.B. & Author, C.D.** Year. ...`
- Case: sentence case for ordinary titles; (a) first word after a colon or en dash
  is capitalized; (b) official titles that are proper names keep published
  capitalization (VGGT, named strategies/policies/acts); (c) article and chapter
  titles are never italicized; book/journal/report/website titles always are.
- Place–publisher: `Place, Publisher.` (comma, never colon). Omit the country when
  the city is a capital. Omit the publisher entirely when identical to the author
  (`FAO. 2012. *Title*. Rome.`). Multiple locations: one per publisher
  (`Rome, FAO & Paris, CIRAD`). `Washington, DC` keeps the comma and DC.
- Ranges take en dashes (`pp. 295–311`; `25–29 March 2019`).

## Entry-type templates

| Type | Template |
|---|---|
| Journal article | `Author, A.B. & Author, C.D. Year. Article title: Capitalized subtitle. *Journal Name*, volume(issue): first–last. https://doi.org/...` |
| Book or report | `Author, A.B. Year. *Title in sentence case: Capitalized subtitle*. Series title, No. X. Place, Publisher. URL-if-any` |
| Author is publisher | `FAO. Year. *Title*. Series, No. X. Rome.` |
| Chapter in edited book | `Author, A.B. Year. Chapter title. In: Editor, A.B. & Editor, C.D., eds. *Book title*. Place, Publisher, pp. xx–yy.` |
| Newspaper article | `Author or Outlet. Year. Article title. *Outlet*, DD Month YYYY. Place-if-known. [Cited DD Month YYYY]. URL` |
| Webpage | `Author. Year or n.d. Page title. In: *Website identity*. Place. [Cited DD Month YYYY]. URL` |
| Legislation | KEEP CURRENT AUTHOR STRINGS ('Government of Uganda', 'République du Mali', etc.) — country-as-author conversion (REF-LEG-001/DP-3) is NOT approved. Legislation titles stay roman (no italics). |
| Conference paper | `Author, A.B. Year. Paper title. Paper presented at Conference Name, Place, DD–DD Month YYYY.` |
| Thesis | `Author, A.B. Year. *Title*. Place, University. PhD dissertation.` |
| Dataset/database | `Author. Year of last update. *Name of database*: Name of dataset. [Accessed on DD Month YYYY]. URL. Licence: ...` |
| Year suffixes | Same author + same year: `Author. 2025a.` / `Author. 2025b.` — and update in-text citations to match. |

## APA-residue conversions

| Pattern | Action | Result |
|---|---|---|
| `Surname, A. B. (2000).` | remove parentheses around year; close up initials | `Surname, A.B. 2000.` |
| `(2020, July 30)` | full date → move to outlet position | `Author. 2020. Title. *Daily Monitor*, 30 July 2020.` |
| `Place: Publisher` | colon → comma | `Place, Publisher` |
| `Retrieved from URL` / `Retrieved [date] from` | → cited-date + URL form | `[Cited DD Month YYYY]. URL` |
| `Journal, 54(3), 421–456` | comma before pages → colon; italicize journal | `*Journal*, 54(3): 421–456` |
| `Surname, A. B., & Surname, C. D.` | drop comma before &; close up initials | `Surname, A.B. & Surname, C.D.` |

`et al.` in the list is allowed only if >10 authors (list first 7); otherwise name
all authors.

## Decision procedure

0. LABEL CHECK: extract `^\[(\d+)\]` from the source and store the sequence.
1. Read the whole reference section once; classify each entry by type.
2. Apply global constraints and the matching template, entry by entry under its
   label; touch nothing outside the reference section.
3. Check each entry against every rule ID in `assets/references_formatting_rules.json`.
4. Verify detector-generated flags against the actual entry text before applying;
   also fix anything the detector missed.
5. Re-extract labels before/after and confirm identical; confirm zero APA residue;
   confirm italic coverage; confirm no fabricated locators.
6. FINAL LABEL CHECK; only then write the per-manuscript rectification report:
   entry label → what changed (rule IDs) + parked author actions.

## Park as author action (never decide unilaterally)

- Missing URL/DOI/access date (including all empty "Available at: ." placeholders).
- `et al.` with ≤10 authors where the full list cannot be determined from the manuscript.
- Unverifiable place or publisher.
- Anything requiring a meaning judgement (e.g. which of two editions was cited).

## Known pitfalls (from proven runs)

- Never -ize-normalize inside quoted titles — titles are quoted material.
- Switching corporate authors to abbreviation-led form can create author+year
  collisions (two "MLHUD 2023") — resolve with a/b suffixes AND update in-text.
- Do not decapitalize official titles (VGGT keeps published capitalization;
  REF-CASE-003).
- `Rome, FAO.` is wrong when FAO is also the author — write `Rome.` (REF-PUB-004).
- In editor_tool v3 exports, entries with hyperlinks are ordinary entries: rectify
  them normally. If the URL is the link's own text, changing it also updates the
  link target, so keep each URL as one unbroken string (no inserted spaces or line
  breaks) for the link to follow.
- Entries carrying a `[SPECIAL]` tag are skipped by the DOCX importer: their
  rectified text lives only in the markdown. In v3 this happens when the list is a
  bibliography generated by Zotero/EndNote/Mendeley (then every entry is
  `[SPECIAL]`); in v2 exports, also for entries with hyperlinks. Count them in the
  rectification report and list them in the Phase 9 DOCX action sheet
  (`references/docx-action-sheet.md`) — not the author comment sheet.

## Validation checklist (all must pass before delivery)

- Label sequences identical before/after (same numbers, order, count, `[n] ` formatting).
- Zero `(year)` APA patterns; zero "Retrieved from"; zero `Place: Publisher` colons.
- Every book/journal/report/website title italic; zero italic article/chapter titles.
- Capital after every colon inside titles; official titles capitalized.
- Every `&` preceded by no comma; every range an en dash.
- No entry invented; every missing locator parked as `[Author to provide]` with placeholder.
- Struck entries untouched; in-text citations untouched except logged suffix normalization.
