# FAO manuscript: single-run procedure – pronoun and heading scan, citation cross-reference audit, comment-sheet triage and editor change list (JWGD)

Reusable template. Replace every `{{...}}` before running. Run it once per manuscript. For several manuscripts, loop over them with separate files for each and one combined chat summary at the end.

This prompt replaces the two earlier prompts `FAO_pronouns_headings_crossref_consolidated_prompt_JWGD.md` and `FAO_comment-sheet_triage_and_crosscheck_prompt_JWGD.md`. Nothing has to be run before or after it.

| Placeholder | Meaning | Example |
|---|---|---|
| `{{REF}}` | Job reference number | REF1790868738 |
| `{{Pn}}` | Manuscript code | P3 |
| `{{LABELLED_MD}}` | Labelled markdown export (editor_tool form: `[N]` paragraph labels, `⟦N\|…⟧` tokens, `[SPECIAL]` tags, `[^N]` footnotes, References section). Needed for the paragraph-level CSV and for label mapping. Preferably the review export of the final DOCX (`editor_tool.py --export --review`), which also carries page numbers, tables and a table/figure inventory, so `{{DOCX}}` is not needed | `REF…_P3_final_for_review.md` |
| `{{MD}}` | `_final_Edited.md` conversion of the final DOCX. The editor searches and replaces in this text. If `{{LABELLED_MD}}` is the only markdown attached, use it for both roles | `REF…_P3_final_Edited.md` |
| `{{DOCX}}` | The DOCX the markdown was converted from. Used for page numbers and the table inventory only, so attach it only when `{{LABELLED_MD}}` is not a review export | `REF…_P3_final.docx` |
| `{{SHEET}}` | Editor's comment sheet (TSV/CSV/XLSX/paste; columns such as `#`, `Position` or `Page`, `Issue`, `Comment`). Optional | `Comments_sheet_P3.tsv` |
| `{{OUT}}` | Output folder | `/home/claude/out/` |

---

## J – Job

Process manuscript `{{Pn}}` (`{{REF}}`) in one run, from intake to delivery, and produce the files listed under **D – Done means**. The three source files (`{{LABELLED_MD}}`, `{{MD}}`, `{{DOCX}}`) and `{{SHEET}}` are read-only throughout; work on copies and write every proposed change to the output files.

**Inputs**

1. `{{LABELLED_MD}}` and/or `{{MD}}` as described above.
2. Page numbers and the table/figure inventory: from the review export (`<!-- page N -->` lines, `TABLE` blocks, `INVENTORY` block), or, if `{{LABELLED_MD}}` is not a review export, from `{{DOCX}}` (`w:lastRenderedPageBreak`).
3. `{{SHEET}}` – optional. It may use `[n]` labels instead of page numbers, and it may be stale against the current file.
4. Project files: `house-style.md`, `citations-rules.md` (142 FAOSTYLE rules), `cb8081en.pdf` (FAOSTYLE English, Nov 2024), `conflicts.md`, `recommended-words.md`, `fao_termlist.json`, `nocs_lookup.json`.

**Stages** (run in this order; each uses the output of the one before)

1. **Intake and preflight.**
   - Record a checksum or modification time for every source file.
   - Locate the References boundary, the footnotes, `[SPECIAL]` lines and `⟦N|…⟧` tokens in `{{LABELLED_MD}}`.
   - Build the paragraph-to-page map and the inventory of tables and figures: from the review export if it is one, otherwise from `{{DOCX}}`.
   - If `{{SHEET}}` is attached, parse every row and map each `[n]` label to a paragraph by text match.
   - State at once any missing input and what it limits (G20).
2. **Detection scans** (read-only; findings only, no corrections yet). Give every finding an ID, a paragraph label, the quoted text and the rule.
   - **2a.** Pronouns and headings (G5–G6).
   - **2b.** Citations in both directions, plus instruments, events, named works, quotations and reference-list checks (G8–G11).
   - **2c.** Foreign-language terms, abbreviations, tables and figures, spelling and style slips (G13–G16).
3. **Reconcile with `{{SHEET}}`** (skip if no sheet). Convert and rewrite its rows (G3), check each row against the manuscript (G18), classify every row and every scan finding as Editor, Author or Mixed (G4), and note which scan findings the sheet already covers.
4. **Build the deliverables.**
   - Author sheet: author comments only, chronological, with page numbers.
   - Editor action list, editor CSV `current,to_replace`, and basis file (G17).
   - Paragraph-level CSV for pronouns and headings (G7).
   - Reference-title translations CSV, if non-English titles exist (G13).
   - Cross-reference report and scan notes (G12).
5. **Verify** every written file and the manuscript's integrity (G19).
6. **Deliver** the files and the short chat summary (D).

---

## W – Why

- The author should be asked only what only the author can answer, once, in order of appearance, without editor jargon. Editor actions in an author sheet confuse the author and delay the return.
- The editor needs to apply changes quickly. Two import-ready CSVs, one paragraph-level and one find-and-replace with `current` strings known to exist, let that happen without hunting or re-reading.
- Cited-but-unlisted and listed-but-uncited sources are where most author queries come from, and comment sheets written by hand miss them. A systematic two-direction audit catches them, sends each to the person who can fix it, and keeps the author sheet complete.
- Missing reference data (authors, years, places, publishers, titles, series numbers, journal details, DOIs, URLs, pages, cited dates, expansions of acronyms) cannot come from the manuscript or the house style. Guessing it would put invented bibliographic data into an FAO publication.
- First-person pronouns and question-form or non-heading headings are the usual FAO style slips in a long manuscript.
- Comment sheets are often stale or contain errors, and the markdown export can drop tables or shift labels. Checking against the current file, and keeping a row-by-row audit trail, protects the editor from applying outdated or wrong changes. One run keeps the findings of all checks consistent with one another.

---

## G – Guidelines

### G1. Invariants
- No source file is modified, in whole or in part. All proposed changes go into the output files.
- Paragraph labels `[N]`, `[SPECIAL]` tags, `[^N]` footnote labels, `⟦N|…⟧` tokens and markdown prefixes (`#`, `##`, `###`) are copied exactly as they appear. A label that moves or changes breaks the import, and the importer refuses a paragraph whose tokens were dropped, duplicated or altered.
- Quoted text, titles, names and numbers are copied from the markdown, not retyped from memory.
- Never invent or silently supply reference data. If a value is needed and the document does not contain it, it becomes an author query. If the editor could verify it from a trustworthy source, mark it `Apply – verify` and say what to check.
- Never add a reference entry on the author's behalf.
- Never rephrase, paraphrase or swap synonyms in the manuscript text beyond the minimum a rule requires. Keep each replacement as short as the rule allows.

### G2. Positions, labels and page numbers
- Working files (cross-reference report, scan notes, basis file) report each position as the paragraph label read from the line prefix (`[N]`, `[^N]`). Never report a file line number. The author sheet and the editor action list report page numbers (see below), with no `[n]` label.
- Read the References boundary from the first line matching `[N] #+ References`. Treat a following line with no `[N]` prefix (for example a wrapped URL) as part of the previous entry.
- Lines tagged `[SPECIAL]` are scanned. If a fix lands in one, mark it manual in Word, because the importer skips those lines.
- A `⟦N|…⟧` token is a live Word object: a reference-manager citation, cross-reference, caption number, image, chart or equation. Its label shows the text Word displays and may be cut short with `…`. Scan citation tokens like any in-text citation. If a fix lands inside a token, it cannot be made through the markdown: list it in the editor action list as a manual Word task (for a reference-manager citation, correct the record and refresh).
- Page of a paragraph = the page on which its first non-empty text segment starts. In a review export it is given by the nearest `<!-- page N -->` line above the paragraph; otherwise read it from the `w:lastRenderedPageBreak` markers in `{{DOCX}}` (a marker at the very start of a paragraph means the paragraph begins on the next page). Both reflect Word's last layout of the file. If the review export says `NO PAGE INFORMATION`, ask for the DOCX opened and saved in Word, re-exported. A LibreOffice PDF render is a cross-check only.
- If the DOCX appears to have been repaginated after the comment sheet was written, say so and flag the page column for remapping.
- Label-to-paragraph mapping: map `[n]` labels in the sheet to paragraphs through `{{LABELLED_MD}}` or the DOCX paragraph order, and confirm by matching the comment's quoted text to the paragraph. When a label and the text disagree, the text wins; state the discrepancy.

### G3. Converting and rewriting sheet comments
- Order rows by position in the manuscript (page, then paragraph), not by the original order.
- Professional, concise, courteous; no internal shorthand, no "rectification report", no bare `[107]` labels, no "editor should construct…".
- Keep FAOSTYLE rule numbers (e.g. "rule 22").
- Merge duplicates into one comment (list the pages). Renumber from 1 and recompute any internal cross-reference ("see comment 3") after sorting; numbers in the source sheet are not reliable.
- Each comment says what is wrong or missing, where, and what the author is asked to supply. Quote the relevant fragment when it helps the author find it.
- Write full sentences to the end; never truncate.
- Final columns: `#`, `Page`, `Issue`, `Comment`.

### G4. Classification: Editor, Author, Mixed
Applies to every sheet row and every scan finding.
- **Author** if resolving it needs anything not in the document or the house style: reference entries or their missing parts, places, titles, series numbers, journal details, citations, URLs, cited dates, the source or page of a quotation, whether a claim is supported, the author's intent, or the referent of an ambiguous "we".
- **Editor** only when the editor can be sure of the fix from the document and the house style alone: spelling, capitalization, abbreviation handling, italics, punctuation, in-text author forms, cross-reference fixes, ordering of entries, a/b lettering, moving an entry to Further reading, and correcting an internal inconsistency where the correct form appears elsewhere in the manuscript. If there is real doubt, classify as Author or `Apply – verify`, never as a confident editor item.
- **Mixed**: split into an editor part and an author part, each written so it stands alone.
- A names-but-no-citation case, such as a special issue whose contributions are named without in-text citations or reference entries, is an **Author** query: "The author must search for them and implement them here as in-text citations as well as reference entries." Contributor names in such an issue are not author–date citations.
- The author sheet holds author comments only. Editor actions, editor-action clauses and internal references are removed from it.

### G5. Pronoun scan (2a)
- Scan every paragraph for first-person pronouns (I, me, my, we, us, our, ours).
- Count only genuine pronouns. Skip Roman numerals ("Phase I", "Declaration I"), author initials ("I." in references), quoted titles, song lines and direct quotations. A pronoun inside a quotation stays as written, because quotations follow the original (rule 42).
- Choose the replacement from the actor the manuscript already names: "the project team", "the authors", "the article", "the study", or the project or organization by name. Do not invent a new actor.
- If "we" or "our" could refer to different actors and the text does not settle it, leave the paragraph unchanged in the CSV and send the question to the author.
- Keep each replacement minimal. Sentences stay at or under 34 words; word count stays within 8 percent of the original paragraph (short headings are exempt from the 8 percent test, because one word is a large share); no new sentence opens with "This" or "There" plus a verb.

### G6. Heading scan (2a)
- A heading is a short noun phrase or statement in sentence case, with no final full stop and no question mark. FAO style avoids abbreviations in headings except FAO and COVID-19, and uses an en dash between a title and a subtitle.
- If a heading is a question, rewrite it as a statement or noun phrase that keeps the subject.
- If a "heading" is a poster or image caption, a full sentence or running text, rewrite it as a heading only when the section's content makes the heading obvious. If not, send the question to the author.
- Write the fix into the CSV only when the document settles it. Report without changing: a bare `#` heading, an orphan heading with no body, unnumbered headings inside a numbered sequence, and abbreviations in a title that the manuscript expands elsewhere. These are editor or author decisions the run should not guess.
- Captions embedded in image paragraphs are flagged for manual handling.

### G7. Paragraph-level CSV specification
- Header row exactly `current_para_+label`,`to_replace_w/label`. UTF-8 with BOM. Every field quoted.
- One row per changed paragraph. Both columns carry the full paragraph text, label and markdown prefix included. The columns differ only where the fix applies.
- A manuscript with nothing to fix gets a header-only file, which is a valid result.
- File name `{{Pn}}.csv`. Without `{{LABELLED_MD}}` this file cannot be built; say so, list the findings in the scan notes, and mark the file pending.
- Style rules in G16 apply to every replacement.

### G8. Extracting citations (2b)
- Parse parenthetical groups, split on semicolons, and handle leading "e.g.", "see", "cf.". Parse narrative forms "Author (year)" and "Author and Author (year)". Handle "et al." (italic or not), "n.d.", "forthcoming", a/b/c suffixes, pinpoints ("p. 73", "1958: 97–99") and personal communications.
- Strip leading sentence openers from narrative matches ("As Gómez and Graziano da Silva (2025)").
- A year on its own, a year range or a date in parentheses is not a citation: "(2012–2024)", "(approved in 2016)", "(from December 2020 to April 2025)".
- Scan footnotes, notes, tables (the `TABLE` blocks of a review export), figures, boxes and token labels as well as body text, and note any footnote with an anchor but no text.
- After the pattern scan, search the body for four-digit years that no pattern captured. Read each in context to catch citations in unusual forms.

### G9. Matching citations to entries (2b)
- Match by first-author surname for persons (accent-insensitive) and by full name or abbreviation for corporate authors, then by year including suffix.
- Corporate keys follow rule 64: alphabetize and cite by abbreviation, with the full name given once. Treat "Full name [ABBR]" in the text and "ABBR (Full name)" in the list as the same body, and flag the in-text form.
- Same author, different year: report a **year mismatch** and name the candidate entry. A one-year difference supports calling it a probable typo but never counts as a match. Note if a page range, series number or event date in the entry points to one year.
- No author match, but a same-year entry shares a distinctive word with the cited author: report an **author-name variant** and name the entry.
- Neither: the citation is **cited, not listed** (author comment).
- More than three authors: "et al." in text and all authors named in the list (rules 27–28). Flag "et al." used for three authors or fewer, and a full author list used in text for more than three. In text, "and" joins the last two authors; "&" belongs in the reference list only.
- Two entries sharing first author and year: check a/b lettering by order of first citation (rule 59). If one is single-author and the other multi-author, a clear distinction is needed; offer lettering as an option.
- Do not flag the order of citations inside one set of parentheses (FAOSTYLE 12.3.1 allows alphabetical, chronological or presentation order if consistent), or pinpoint pages (the guide asks for them only for quoted text).

### G10. Instruments, events, named works, quotations (2b)
- Laws, decrees, treaties, resolutions and policies cited by name and year, without an author–date citation, are not author–date citations. Before treating an uncited entry as uncited, search the body for its instrument name.
  - Named in text and has an entry → cited by name (table I-1).
  - Named in text and has no entry → table I-2, author query (rules 129–135 let the author add a legal or international-instruments subheading).
- Dated events, statistics, named reports and works named without any citation, and special-issue contributions named by author without a year or entry, are author queries even though no pattern matched. Report them.
- Every named author, work, instrument or event mentioned in running text without an author–date citation is checked.
- Quotations without a page locator (rules 22, 40) and quotations that do not follow the original (rule 42) are author queries (the source and page are not in the document).
- Personal communications are cited in text only (rule 3). Put them on the author-verify sheet for confirmation of name, role, date and permission. They need no entry.

### G11. Reference-list checks (2b)
- A struck-through entry (`~~…~~`) gets its own flag row and is excluded from matching.
- **Listed but not cited** (after the G10 instrument search) → **Editor** action: strike the entry from References and add it to **Further reading** (rule 60: Bibliography with subtitles "References" and "Further reading"), in its correct position (rules 57–58). If the manuscript has no Further reading subsection, say so in the basis file and create the heading in the same action.
  - Where the author may have meant a citation but mistyped the key (year mismatch, name variant), do not move the entry. Hold it (section B2) and raise an author query.
- Duplicates: the same title under different author keys, or the same DOI, volume, article number or URL under different titles. The first may be one work cited under two keys; the second is a data error the author must resolve. For a true duplicate entry, the editor keeps one, carries any more complete data across, and deletes the other.
- Report an in-text title that differs from the entry title for the same source.
- Report open placeholders (`[… to be supplied by author]`, `[EXPANSION NEEDED]`, `[Struck: …]`) and entries that lack a place, publisher, URL, DOI, page range or series number with no placeholder, because a placeholder scan alone misses them.
- Check list order (rules 57–58, 64): alphabetical by first-author surname, corporate authors by abbreviation, single author before multi-author with the same first author, then ascending year. Report an adjacent pair only if it is out of order under every reasonable key. A report on a doubtful pair goes in the secondary section.
- Trailing full stops after DOIs and URLs, and angled brackets around URLs, are editor actions (rules 77–80).
- Detection and correction stay separate: what was found, then what was done or asked.

### G12. Cross-reference report and scan notes
`{{Pn}}_citation_crossref_report.md` is the working record. Its author-facing findings are carried into the author sheet in stage 4, so no finding lives only in the report.
- **Summary** counts.
- **A, author-verify:** citations with no entry, sources described but not cited, personal communications. Columns: ID, Para, In-text citation, Context, Issue, Author action, Author response (blank).
- **I-1 / I-2:** instruments named in text, with and without an entry.
- **B, Further reading:** entries with no in-text citation: a table with the entry copied verbatim (including open author queries), then a paste-ready block in alphabetical order. Mark `[SPECIAL]` entries for manual movement in Word. If B is empty, say so and give the reason.
- **B2, held:** entries that look like the intended source of a year mismatch or duplicate, kept out of Further reading until the flag is resolved.
- **C, other flags:** year mismatches (a same-author entry exists, so the citation is not "unreferenced"), name variants, author-list and "&" format, title mismatches, duplicates, struck entries, empty footnotes, same-first-author-and-year pairs, in-text corporate form.
- **C-order / C-open:** list order, open placeholders, missing locators.
- **D, audit table:** every reference entry with status (Cited, Cited by variant, Cited by instrument name, Held, Uncited, Struck) and the paragraphs where it is cited.
- **Notes and method:** parsing and matching rules used, what was not flagged, limits of the run.

`{{Pn}}_scan_notes.md`: items reported but not changed (G6), pronoun false positives skipped and why, `[SPECIAL]` paragraphs needing manual handling, and the paragraph-level CSV rows with the check of sentence length and word count.

### G13. Foreign-language terms and non-English titles (2c) – FAOSTYLE, house-style §6.4, §9.1
- Italicize foreign words that are not naturalized in English. Naturalized words (e.g. machismo, ad hoc, cosmovision) stay roman. Foreign proper nouns are not italicized.
- Give the English term first with the foreign term in parentheses (italic), unless the foreign term is the subject of discussion.
- Organization names: use the official English translation if one exists; otherwise keep the original with a bracketed or parenthetical translation at first mention.
- Titles of non-English sources in the reference list get a bracketed English translation after the title (rule 89); use the official translation if one exists (rule 87). Do not add translations to legal-instrument titles. Words not copied from the source, such as "first edition", stay in English.
- Where a translation is not certain, put it in the translations CSV with status `Apply – verify`; do not guess an official name.
- Italics in the CSVs use `_x_`, as in the markdown.

### G14. Abbreviations (2c) – house-style §7, ACR-DEF-001
- Define at first mention in each chapter or self-standing section; define the singular form; common nouns lower case when expanded; no re-expansion once defined within the same chapter; avoid abbreviations in titles except FAO and COVID-19.
- Check singular/plural consistency ("VGGTs" → "the VGGT" where the guidelines are meant) and that the full VGGT title is italicized (project convention).
- Avoid "ibid."; replace it with the explicit citation or a paragraph/section number, and flag the case for checking where the target is not obvious.
- An expansion that the manuscript never gives is not editor-resolvable: mark `Apply – verify` or send to the author.

### G15. Tables and figures (2c)
- Confirm which tables and figures exist from the `INVENTORY` block of a review export, or from `{{DOCX}}` if no review export is attached. A plain export does not contain tables.
- Every table needs a number and a caption and must be referred to by number in the narrative. A table without a caption, or never mentioned in the text, is an **author** query (the author supplies the caption and decides where it is discussed) and, once the number is known, an **editor** cross-reference fix (HOLD until the author answers).
- Confirm a "not referenced" finding by searching the narrative for the table number and for descriptive mentions.

### G16. Spelling and style (2c, and for every replacement)
- British English; FAO spelling policy: -ize endings (marginalized, realizing); keep -yse verbs (analyse, paralyse, catalyse); official names that use "s" keep it; "percent" in running text; sentence-case headings; en dashes as the project preset sets them; no angled brackets around URLs.
- Where the house style and FAOSTYLE conflict, follow `conflicts.md`. Do not change recommended-words choices without a rule behind the change.
- The aim is a change list for the cases found, not a rewrite. Any rephrasing respects the 34-word sentence cap and the 8 percent word-count limit.

### G17. Editor outputs
**`{{Pn}}_editor_changes.csv`**
- Exactly two columns, header `current,to_replace`; all fields quoted.
- Every `current` string occurs in `{{MD}}` as written, long enough to be unique where possible. For a deliberate replace-all, state the occurrence count in the basis file.
- A `current` string never contains a `⟦N|…⟧` token or text from a comment line (`page`, `TABLE`, `INVENTORY`), because that text is not in the document's paragraphs. If a change falls inside a token or a table, list it in the editor action list as a manual Word task instead.
- Verification: normalize the markdown (remove `**` and `~~`; `\[`→`[`, `\]`→`]`, `\_`→`_`, `\.`→`.`), then count each `current` string. A count of 0, or one that does not match the intended number, is fixed before delivery.
- Deleting a struck or duplicate entry: `current` is the entry text without the strike markers; `to_replace` is empty.
- Moving an entry to Further reading: one row to delete it from References and one to insert it in Further reading, or a clear note in the basis file when the insertion point has to be made by hand.
- Overlap with `{{Pn}}.csv`: choose `current` strings outside the span a paragraph-level fix changes. If that is impossible, fold the change into the paragraph replacement and drop the row; record the case in the basis file.
- Rows that depend on an author answer are not in the CSV. List them as **HOLD** in the basis file with the trigger ("after the author supplies …").

**`{{Pn}}_editor_actions.tsv`** – the full editor list in manuscript order (page, action, rule), including actions already done and optional clarifications, clearly marked.

**`{{Pn}}_editor_changes_basis.tsv`** – for each CSV row: ID, group (acronym, instrument, foreign term, duplicate, Further reading, spelling, other), status (`Apply`, `Apply – verify`, `HOLD`), rule or source, occurrence count, note. Also the check items still open.

### G18. Reconciling with `{{SHEET}}`
- Read every row of the sheet. Map each scan finding to a row and mark it **covered**, **editor-only** or **author-only and missing**. Add each author-only missing finding to the author sheet as a new comment, merged with related findings and split by topic when one row would cover many unrelated entries.
- Check every sheet row against the manuscript. If a row is factually wrong (for example it says a source has no entry when an entry with a different year exists), correct it in the author sheet, cross-refer the corrected point, and report every such correction in the chat summary.
- Every original row is accounted for in the classification file: none lost, none duplicated. The original sheet itself is never edited, and the author sheet is a new file.
- If there is no sheet, the author sheet holds only the findings from the scans, and the classification file is omitted.

### G19. Verification before delivery
- Re-open every file written. Check row and column counts, quoting, no truncated cell, every sentence ends, `#` values consecutive, internal cross-references match, and the XLSX opens with wrapped cells.
- Confirm each flag by reading both places in the manuscript (the citation and the entry, or the sentence and the heading). Pattern matching alone produces false positives (abbreviation-keyed entries such as TAWLA, "Phase I", quoted titles).
- For every statement that a source is "not cited" or "missing", search the body again with accents removed and with the author's name alone.
- Re-count every `current` string in the markdown. If `{{DOCX}}` is attached, sample-check at least five page numbers against it, plus every page that has more than one comment. If the page numbers come from a review export, state in the chat summary that they reflect Word's last layout of the file.
- Re-run the pronoun scan on the replacement column of `{{Pn}}.csv` and confirm that no pronoun, over-length sentence or over-8-percent drift remains in a body paragraph.
- Confirm that each source file is unchanged (checksum or modification time).
- Anything not verifiable is listed as an open check item, never reported as done.

### G20. Output handling and escalation
- Author-facing sheet: TSV (UTF-8, tab-separated, one row per comment) plus an XLSX copy with wrapped cells and sensible column widths. Some viewers and pastes cut cells at about 250 characters, so the XLSX is part of the delivery.
- Write files to `{{OUT}}` with consistent names. If a file from an earlier run exists, add `_v2` instead of overwriting.
- Keep tool names, regex patterns and internal machinery out of the files the author and editor receive.
- If an input is missing (no page information from either a review export or a DOCX, no `{{MD}}`, no `References` heading, no `[N]` labels), say so first, deliver what can be done, and mark the dependent column or file pending.
- Work out ambiguities from the files. Ask the user only when a wrong guess is costly and the inputs cannot settle it, for example when the sheet and the manuscript are clearly different versions.
- If this prompt conflicts with a project rule, follow `conflicts.md`. If the rule is silent, state the assumption in the basis file or report notes.

---

## D – Done means

**Files in `{{OUT}}`**

| File | Content |
|---|---|
| `{{Pn}}.csv` | Paragraph-level pronoun and heading fixes: header `current_para_+label`,`to_replace_w/label`, changed paragraphs only, full text. Header-only if nothing to fix |
| `{{Pn}}_scan_notes.md` | Items reported but not changed, skipped false positives with reasons, `[SPECIAL]` paragraphs needing manual handling |
| `{{Pn}}_citation_crossref_report.md` | Summary, A, I-1/I-2, B/B2, C, C-order, C-open, D, Notes |
| `{{Pn}}_comment_classification.tsv` | One row per original sheet comment: short original text, classification (Editor/Author/Mixed), one-line basis with rule number, disposition (author-sheet row / editor-list row). Only when a sheet was attached |
| `{{Pn}}_comment_sheet_author_only.tsv` and `.xlsx` | `#`, `Page`, `Issue`, `Comment`; chronological; deduplicated; no editor language; includes the audit findings that need the author |
| `{{Pn}}_editor_actions.tsv` | Editor action list in manuscript order |
| `{{Pn}}_editor_changes.csv` | `current,to_replace` only; every `current` string verified |
| `{{Pn}}_editor_changes_basis.tsv` | Status, rule, occurrence count and note for each CSV row, HOLD items with triggers, open check items |
| `{{Pn}}_reference_title_translations.csv` | Only if non-English reference titles exist: `current,to_replace` rows adding the bracketed English translation (rule 89); status in the basis file |

**Quality criteria**

1. Every genuine pronoun and every non-conforming heading is in `{{Pn}}.csv`, in the scan notes with a reason, or sent to the author.
2. Every in-text citation is matched, flagged or explained, and every reference entry has a status in section D. None is lost.
3. Both directions of the cross-reference audit were run, and every finding appears once, in the correct place: author sheet, editor files, or a false positive with a reason.
4. Every original sheet row is accounted for. The author sheet has no editor action, no `[n]` label, no internal reference, no truncated comment, and no query the editor could settle alone.
5. Every `current` string is present in the markdown the stated number of times; no row introduces a spelling or style inconsistency of its own, and no row conflicts with `{{Pn}}.csv`.
6. No reference data was invented. Every open value is an author query or a `verify` item.
7. Report positions are paragraph labels; author-sheet and editor-list positions are page numbers from the review export or the DOCX, with any doubt about repagination stated.
8. All files were re-opened and checked, and every source file is unchanged.

**Chat summary** (short, in this order; for several manuscripts, one block per manuscript)

1. Decisions needed from the user: ambiguous pronoun referents, HOLD items, `Apply – verify` items, ambiguous classifications, sheet rows found to be wrong.
2. Counts: comments received → Author / Editor / Mixed; paragraph-CSV rows; citations parsed; entries; author-sheet rows (of which added by the audit); editor-CSV rows; Further reading entries; held entries; other flags.
3. Anything that limits trust: stale sheet, repagination, `[SPECIAL]` lines, tables missing from the markdown, labels remapped by text, unresolved false-positive checks.
4. File list. Send the files with SendUserFile; do not paste their contents.
