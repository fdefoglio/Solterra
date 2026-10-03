# DOCX action sheet — editor-side manual actions (Phase 9)

A TSV listing every item that must be actioned **by the editor, manually, in the
DOCX** because the `editor_tool.py` round-trip cannot carry it. This sheet is the
editor's own worklist — it stays with the editor and is **never merged into the
author comment sheet** (`references/comment-sheet.md`), which goes to the author.
The two sheets answer different questions: the comment sheet asks the author to
*decide or supply*; the action sheet tells the editor to *do*.

Produce it in Phase 9 **after** the import, from a diff of the imported DOCX
against the rectified labeled markdown: anything present in the markdown but
absent (by design) from the DOCX is a row.

## What goes in

Scan for all of the following — checklist, not menu:

- **`[SPECIAL]` paragraphs whose text changed** between the source export and the
  final rectified markdown. The importer skips them, so the DOCX still shows the
  source text. Typical cases: table-of-contents or list-of-tables entries,
  multi-paragraph footnotes, entries of a reference-manager bibliography, and — in
  exports made with editor_tool v2 — reference entries with hyperlinks. Action:
  REPLACE the paragraph text in Word with the rectified text. If the paragraph
  belongs to a Zotero/EndNote/Mendeley bibliography, the action is to correct the
  record in the reference manager and refresh, because a Word-side edit is
  overwritten on the next refresh; say so in Notes.
- **Paragraphs the importer reported as left unchanged** (the "need attention in
  Word" list printed by the import) that could not be fixed in the markdown and
  re-imported. Action: REPLACE with the rectified text, keeping the live
  citation/cross-reference fields in place.
- **Corrections behind protected tokens.** A `⟦N|…⟧` token is a live Word field,
  so its displayed text cannot be edited through the markdown. Action: EDITOR TASK
  — e.g. "correct the year of this citation in the reference manager and refresh",
  "re-point this cross-reference to Table 4".
- **Parked insertions.** Content the pipeline could not insert because labels may
  never be invented (new reference entries, new headings, author-action-checklist
  items marked "insert at DOCX stage"). Action: INSERT at the stated position.
- **Author-confirmed deletions.** Only after the author confirms: struck-through
  (`~~…~~`) entries the author agrees to remove. Action: DELETE. Never list a
  deletion before confirmation — struck text is what the DOCX shows until then.
- **Logged re-sorts.** Reference-list mis-sorts the pipeline detected but was
  forbidden to fix in the markdown (re-ordering is forbidden under label
  integrity). Action: REORDER in Word — editor's discretion, at layout stage.
- **Routed editor comments.** Any editor-addressed item the Phase 8 routing test
  diverted from the comment sheet that does not fit the categories above (e.g. a
  figure caption to finalize at layout, a cross-reference to re-check after
  pagination). Action: describe the concrete Word-side task in one imperative
  sentence.

## Format

File: `<MS>_docx_action_sheet.tsv` (plus an `.xlsx` rendering for convenience).
Columns, tab-separated, header row included:

```
# | Label | Location | Action | Text to apply | Notes
```

- **Label** — the `[N]` label, or `—` for insertions (which have no label; the
  Location column says between which labels the content goes).
- **Action** — one of `REPLACE`, `INSERT`, `DELETE (after author confirmation)`,
  `REORDER`, `EDITOR TASK` (routed from Phase 8; the Text to apply column carries
  the imperative task description).
- **Text to apply** — the exact markdown text, markers included: `**…**` = bold,
  `*…*` = italic, `~~…~~` = strikethrough. The editor applies that formatting in
  Word. For REPLACE rows on hyperlink-bearing entries, add a Notes reminder to
  re-create the URL as a live link.
- **Notes** — why the round-trip could not carry it, and any formatting caveat.

If the scan finds nothing, still deliver the file with the header and a single
`No DOCX-stage manual actions.` row — an absent sheet is indistinguishable from a
forgotten one.

## Verification and cross-references

- Every `[SPECIAL]` label whose text differs from the source export, and every
  paragraph in the importer's "need attention in Word" list that was not re-imported
  successfully, must appear as a row; count rows against that diff and that list,
  not against memory.
- Note the action count in the technical review report and surface the sheet in
  the executive summary — the DOCX is "near final", and this sheet is precisely
  what stands between it and final.
- Remove or cross-reference any equivalent item in the author action checklist so
  the editor is not told to do the same thing twice.
