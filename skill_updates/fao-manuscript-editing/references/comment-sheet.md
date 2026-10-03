# Comment sheet & author-query round (Phase 8)

The comment sheet is the single document the author receives. It consolidates
everything that needs the author — nothing editorial (already fixed) is in it, and
nothing blocking is left out. It is built from the parked actions accumulated in
Phases 1–7: `[Author to provide]` blockers, `[Author to confirm]` queries, struck
reference entries earmarked for "Further reading", and the rectification report's
parked author actions — **plus every issue only the author can resolve that the
editing passes surfaced** (the locked pipeline must not fix these editorially; they
are judgement calls about the author's meaning, facts, or intent).

## The routing test (mandatory, row by row)

Before a candidate comment enters the sheet, classify it: **who must act?**

- **AUTHOR** — resolving it needs the author to *supply* (a source, a locator, a
  translation), *decide* (preferred wording, whether a repetition is intentional)
  or *confirm* (a fact, a year, a deletion). → comment sheet.
- **EDITOR** — resolving it is a mechanical task the editor performs, typically in
  Word at the DOCX stage: applying `[SPECIAL]`-skipped edits, correcting the
  content behind a `⟦N|…⟧` token (field citation, cross-reference), re-sorting the
  reference list, inserting author-supplied content, deleting author-confirmed
  struck entries, anything phrased "apply manually in Word", "at the DOCX stage",
  "the importer skips", "move/re-sort …". → DOCX action sheet
  (`references/docx-action-sheet.md`), never the comment sheet.
- **MIXED** — split it: the author-side kernel (supply/confirm/decide) stays as a
  comment-sheet row; the editor-side application step becomes an action-sheet row
  that references the same label(s). Example: "supply the missing URL (author);
  the entry is [SPECIAL], so the rectified text is applied in Word (editor)" is
  two rows, one in each sheet — never one row asking the author to do Word work,
  and never one row telling the editor to chase the author.

A comment addressed to the editor contaminates the author sheet (the author
cannot act on it, and it leaks process internals); a comment addressed to the
author contaminates the action sheet (the editor cannot resolve it and delivery
stalls). When in doubt, ask: *could this be closed without writing to the
author?* If yes, it is editor-side.

## Sheet structure

Tab-separated values (TSV), one row per comment, with exactly these columns:

| Column | Content |
|---|---|
| `#` | Running comment number |
| `Position` | The paragraph label(s): `[N]`, and `[N], [M]` when one issue spans several labelled paragraphs (repeat the label for each occurrence, e.g. `[18], [18], [18]`). Labels are the canonical position because the sheet is built from the labeled markdown; use page numbers only when the sheet is built from the DOCX (post-edit round), or page + label together when both are known |
| `Issue` | Concise problem headline — a short neutral label naming the problem, not a full sentence of description (e.g. `Trustee count contradiction: "seven (8) trustees"`) |
| `Comment` | The full comment: what was found (with a short quotation where it carries weight), why it matters, and the concrete request — ending in the decision the author must make |

The author reads this sheet without the manuscript beside them: every row is
self-contained. Labels are stable across the whole pipeline (the import key for
the client's DOCX round-trip), so a label reference stays valid from first sheet
to final DOCX — page numbers can shift during layout.

## Issue categories to cover

Build the sheet by scanning for all of the following — the list is a checklist, not
a menu. Real sheets mix several categories:

- **Missing content (blockers first):** missing abstract; missing reference entries
  for cited sources; missing sources for legal/statistical/scientific/event claims.
- **Reference-list queries:** uncited or duplicate entries (cite / delete / move to
  further reading); conflicting years between in-text citation and list entry;
  `et al.` where the full author list is needed (rule 65); incomplete URLs/access
  dates. `[SPECIAL]`-tagged entries whose rectification did not reach the DOCX do
  NOT belong here — they are editor-side manual actions and go into the DOCX
  action sheet (`references/docx-action-sheet.md`), which stays with the editor.
- **Unclear actors and antecedents:** sentences where the acting body is unnamed or
  a term ("the Institution") has no clear antecedent — especially where naming the
  actor would let a passive sentence be written actively.
- **Internal contradictions:** word vs numeral ("seven (8) trustees"), statements in
  tension (levies called "voluntary" after being described as compelled), same fact
  stated two ways.
- **Chronology and logic:** an effect dated before its stated cause (established
  13 August "by virtue of" a resolution dated 27 September); an organisation
  described as "realising" a responsibility before it existed.
- **Duplication and near-verbatim repetition:** same content restated across
  sections (Preface vs Conclusion; narrative introduction vs dedicated objectives
  subsection) — ask whether the second instance should be shortened to a
  cross-reference, or whether the repetition is intentional.
- **Structural repetition:** parallel subsections repeating an identical formula —
  offer consolidation (one paragraph + table) vs standalone retention for
  compliance/audit purposes.
- **Process/description gaps:** a step in a described flow with no named actor
  unlike every other step; an unclear funding mechanism ("paid through
  beneficiaries"); a sentence that belongs to a different genre (annual-report
  progress note embedded in generic objectives text).
- **Wording the author must settle:** non-standard or likely erroneous words
  ("rigidified"; duplicated words "sectors of sectors" — suggest the probable
  intended form, ask for confirmation), phrases that do not logically connect
  ("benefits in liaison with role players").
- **Citation practice queries:** the same instrument cited in full twice — confirm
  whether the second instance shortens to "the Act".
- **Style exceptions needing sign-off:** abbreviation retained in a title (VGGT),
  non-standard locator formats, subheading numbering inconsistencies.

## Writing rules

- **Neutral, diagnostic, not accusatory.** Describe what the text does, not what
  the author did wrong. Quote the manuscript briefly where it carries weight.
- **End every comment with a concrete, answerable request** — the decision or the
  fact the author must supply. Where a choice exists, offer the options explicitly
  ("shorten to a cross-reference, or confirm the repetition is intentional";
  "consolidate into one paragraph with a table, or retain standalone subsections").
- **Say when no action may be needed.** If an apparent issue is plausibly
  intentional (a conclusion that opens with "To summarise"), say so — the author
  confirms rather than being ordered to change.
- **Do not convert what you cannot settle.** If the text itself does not resolve a
  query (a process flow that names no actor for a step), say so explicitly ("I have
  not converted this one because the process flow does not settle it") rather than
  guessing.
- **Suggest the probable fix, ask for confirmation.** For wording errors propose
  the likely intended form ("possibly intended as 'sectors of society'"); for
  missing actors name the candidates ("the NAMC, the Minister, or the transformation
  guidelines?").
- **Cross-reference related comments** by number when they interact (a duplicate
  entry under one number, the in-text citation that must follow the retained entry
  under another).
- **Blockers first**, then confirmations, then cosmetic queries.
- **No invented content.** The sheet asks; it never supplies facts.

## Merge and verify workflow

1. **Build** the sheet; save as `Comments_sheet_<MS>.tsv` (or `.csv` with UTF-8 BOM
   when Excel compatibility is required — same four columns either way).
2. **Merge responses.** When the author returns the sheet, produce
   `With author responses_<original sheet name>`: the response recorded against
   each comment number, each row marked implemented / pending / rejected-with-reason.
   Where several manuscripts share a review round, produce a merged workbook
   (`Comments_v2.xlsx`) with one sheet per manuscript.
3. **Verify.** Check every implemented response against the manuscript: does the
   promised change actually appear at the referenced position? Produce a verified
   TSV (`Comments_sheet_<MS>_verified.tsv`) recording the check per row.
4. **Implement in the deliverable.** Apply confirmed changes to the final DOCX
   (author-supplied abstracts and entries inserted without re-editing their
   substance — language editing only, logged).
5. **Re-flag leftovers.** Pending items return to the next round's sheet; declined
   items are recorded as accepted with the reason noted in the technical review
   report.

## After the round

Update the author action checklist (progress tracking per item), then proceed to
Phase 9 (DOCX handoff + post-edit audit). The final DOCX incorporates all
implemented responses; the verified TSV is the audit record that nothing was
dropped silently.
