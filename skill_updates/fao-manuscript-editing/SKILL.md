---
name: fao-manuscript-editing
description: Complete FAO house-style editorial pipeline for technical manuscripts, end to end — intake of labeled markdown (_final_for_ai.md) plus, when supplied, the unedited source DOCX kept for handoff; LANG-EVAL pre-edit baseline; locked editing passes (001NM1, 001NM2, 001NM2B, 001NM3, 001WRR, 002ThV); FAO author-date citation validation and gap analysis; consolidation (final text, author checklist, technical review, executive summary); references rectification; comment sheets; DOCX handoff by round-trip import into the unedited DOCX (scripts/editor_tool.py, original formatting retained); pre-/post-edit acronym (ACR-DEF-001) and foreign-language audits. Use when the user hands over an FAO manuscript for editing, mentions a pass code or fao_editor/fao_citation_agent/fao_project_manager, or asks for FAOSTYLE checking, sentence-length or repetition scanning, NOCS country names, citation validation or gaps, LANG-EVAL, references rectification, comment sheets, the author action checklist, or editor_tool export/import.
---

# FAO manuscript editing — master pipeline

A locked, multi-phase editorial pipeline for FAO information products. The output is a
publication-ready manuscript plus an auditable trail separating what was fixed
editorially from what the author still has to supply.

The pipeline is deliberately conservative. Its value is predictability: the same
manuscript run twice produces the same edits, and every edit traces to a rule ID.
Locked mode forbids creative rewriting, which would destroy that property.

## Operating defaults

- **Base model:** the session model. The pipeline is deterministic (rule IDs, lookup
  tables, candidate-generator regexes, 20-line windows, objective checkpoints), so no
  specific model is required. Judgement-heavy phases (001NM2B split accept/reject,
  citation gap analysis, editor discussion notes) are the escalation candidates if a
  checkpoint fails twice on the session model; escalation means the user reruns that
  one phase in a new session, not an in-session handoff.
- **Locked mode binds every phase:** `forbid_paraphrasing`, `forbid_rephrasing`,
  `forbid_synonym_substitution`; word-count drift ≤ 8 percent; content outside a
  logged edit stays byte-identical; every change carries an ID and a rule reference;
  20-line processing window (citation phase and the standalone audits excepted —
  they need full-text context).
- In practice: fix what is *wrong*, leave what is merely *not how you would have
  written it*. Phrase-level repair is permitted where the phrase is genuinely awkward
  or incorrect; sentence-level rewriting is not.

## Label integrity (import contract) — hard rule

Manuscripts carry stable paragraph labels `[n]` (including `[Empty Paragraph]`
placeholders and reference-list entries). They are the import key for the client's
DOCX pipeline and override every other consideration, including reference-list rules.

- The edited manuscript must contain **exactly the same label set as the source, in
  the same order**. Never add, renumber, reorder or delete a label — this binds
  headings and reference entries too.
- Text under a label may change freely; the label itself is untouchable.
- Protected tokens `⟦N|…⟧` (editor_tool v3 exports) stand for live Word content:
  reference-manager citations, cross-references, SEQ numbers, images, equations.
  Keep every token exactly once, unchanged, in its own paragraph; it may move
  within that paragraph. The importer refuses a paragraph whose tokens were
  dropped, duplicated or copied from another paragraph, and that paragraph's edits
  are then lost. The text after `|` is display-only — Word regenerates it, so edits
  there are ignored — and a label ending in `…` is truncated, not wrong. If the
  content behind a token needs correcting (a field citation with the wrong year, a
  cross-reference to the wrong table), keep the token and log the correction as an
  EDITOR TASK row in the DOCX action sheet.
- Deletions: never remove a labelled paragraph — strike it through instead
  (`[83] ~~entry text~~`). Uncited reference entries are struck in place, not removed.
- Insertions: never invent a label. Park new content (reference entries, headings)
  in the author action checklist — the author supplies or approves it; once
  supplied, the editor-side application at the DOCX stage is tracked as an INSERT
  row in the DOCX action sheet (`references/docx-action-sheet.md`).
- Verify before every delivery: extract `^\[(\d+)\]` from source and edited files;
  the sequences must be identical. Use `scripts/check_labels.py`.
- Binds every phase; the highest-risk spot is reference-list work — re-ordering,
  splitting or pruning happens only via labels, never by restructuring the list.

## Project assets and encoding check

Resolve at intake: project-supplied copies (typically the project's upload/mount
folder) are the live versions; use them over any bundled fallback. Check every text
asset for double-encoded UTF-8 (mojibake) before trusting it — count matches of
`[ÃÂ][\x80-\xBF]|â€`; non-zero means repair with `scripts/fix_encoding.py` first.
Full asset inventory, paths, the styleguide-source rule (the official markdown
styleguide replaces the PDF guide) and the conflict-precedence decisions are in
`references/project-assets.md` — read it during Phase 0.

## Pipeline

Run the phases in order. Each phase emits named markers; a checkpoint that finds
markers or artifacts missing reruns **only the missing items**, then halts if they
are still absent. Never proceed past a failed checkpoint; never present a partial
run as complete.

```
Phase 0  intake & asset verification
Phase 1  LANG-EVAL pre-edit baseline (analysis only)
Phase 2  [optional] pre-edit acronym & foreign-language audit (flag list only)
Phase 3  fao_editor1        001NM1 → 001NM3
  ↓ checkpoint_editor1_done        [001NM1_marker, 001NM3_marker]
Phase 4  fao_editor2        001NM2 → 001NM2B → 001WRR → 002ThV
  ↓ checkpoint_editor2_done        [001NM2_marker, 001NM2B_marker, 001WRR_marker, 002ThV_marker]
Phase 5  fao_citation_agent validate_and_format_citations → identify_citation_gaps
  ↓ checkpoint_citation_agent_done [FAO_citation_marker, FAO_citation_gap_marker] + 4 artifacts
Phase 6  consolidation      final text + author checklist + technical review + executive summary
Phase 7  references rectification (FAOSTYLE author-date)
Phase 8  comment sheet & author-query round
Phase 9  DOCX handoff + post-edit acronym/foreign-language audit (flag list only)
```

Pass parameters, decision sequences, exact regexes and phase receipts are in
`references/passes.md` — read it before running Phases 3–4 and when a checkpoint
fails.

### Phase 0 — Intake

- Obtain the labeled markdown (`*_final_for_ai.md`) and — whenever the client can
  supply it — the **unedited source DOCX**; keep the DOCX untouched for the Phase 9
  import. If only the DOCX is supplied, export the markdown with
  `scripts/editor_tool.py --export <MS>.docx` (preserves `[N]` paragraph-index
  labels, `⟦N|…⟧` protected tokens, `[SPECIAL]` tags, `[Empty Paragraph]` placeholders and footnotes; it is
  the only export whose labels are guaranteed to match paragraph indexes on
  re-import — do not substitute another converter).
- Check the first line of a supplied labeled markdown. `<!-- editor_tool v3 export -->`
  means it is current. An older header still imports, but its `[SPECIAL]` tags also
  freeze every heading with a bookmark and every hyperlinked reference entry; if the
  source DOCX is available and editing has not started, re-export with v3 (labels
  stay identical) so far fewer edits need manual Word work.
- Read `references/project-assets.md`; locate assets; run the mojibake check; state
  which asset set is in use.

### Phase 1 — LANG-EVAL pre-edit baseline

Analysis only — no manuscript text changes. The preset definition, settings,
detectors, scoring, output files and quality gates are in
`references/lang-eval-preset.md` — follow it to produce the five baseline artifacts
(`LANG-EVAL_report.md`, `LANG-EVAL_findings.csv`, `LANG-EVAL_compliance.tsv`,
`LANG-EVAL_metrics.json`, `LANG-EVAL_metrics.csv`). Save the metrics as the baseline
for the optional post-edit delta. Emit `LANGEVAL_marker`.

### Phase 2 — Pre-edit acronym & foreign-language audit (optional)

Standalone flag-list-only audit before editing: acronym definition per ACR-DEF-001
(chapter-scoped client override) and foreign-language italics/translation compliance.
Defaults and the never-invent constraint are in `references/acronym-foreign-check.md`
(pre-edit mode). Produce the flag list and stop; apply edits only on explicit
follow-up authorization.

### Phase 3 — fao_editor1 (001NM1 → 001NM3)

- **001NM1** — phrase correction and close-range repetition. CSV `original,replacement`
  plus edited text. No sentence rewriting, no synonym swaps.
- **001NM3** — verification only: genuine errors, QA checklist. Not a second editing
  pass; emits findings, no text.
- Emit `001NM1_marker`, `001NM3_marker`; pass `checkpoint_editor1_done`; verify label
  sequences identical (`scripts/check_labels.py`).

### Phase 4 — fao_editor2 (001NM2 → 001NM2B → 001WRR → 002ThV)

- **001NM2** — list sentences over 34 words. Detection only; CSV `words,sentence`,
  all quoted.
- **001NM2B** — split them, rephrasing only at the split point; reject splits that
  worsen the sentence; validate every accepted split against 002ThV;
  `fallback_to_no_split` for verbatim legal/policy quotations (rule 42 forbids
  altering quoted law).
- **001WRR** — lemma-based repetition scan across sentences and consecutive bullets;
  CSV `ID,Page,Section,Description,Action,Completed revised`.
- **002ThV** — blocks `This/There + verb` openers (full expanded regex); targets
  18–28 words, hard cap 34. Corrected text, no change log.
- Emit all four markers; pass `checkpoint_editor2_done`; verify labels.

### Phase 5 — fao_citation_agent

Runs with full document context (a 20-line window produces false gaps). Tasks:
`validate_and_format_citations` then `identify_citation_gaps`. Density target
2.0–5.0 with the denominator fixed as *in-text citations ÷ body-text sentences ×
100*; publish the raw counts and per-chapter distribution; above-band density on
legal-policy analysis manuscripts is reported as a note, not an error.
Checkpoints require both markers plus four artifacts under `reports/`:
`FAO_citation_report.tsv`, `intext_citation_map.tsv`, `FAO_citation_gap_analysis.txt`,
`FAO_citation_editorial_note.tsv`. Editorial notes use the labelled TSV trail
(`[Implemented editorially]`, `[Author to provide]`, `[Author to confirm]`,
`[Flagged — no change]`) — never merge the standalone audit's flag lists into it.

### Phase 6 — Consolidation

Produce: final consolidated edited text (whole manuscript, all accepted edits —
never close a run with reports only); author action checklist with progress
tracking; technical review report (phase receipts, word-count drift, checksum
statement, label-integrity verification, conflicts hit); short executive summary.

### Phase 7 — References rectification

Rectify the References/Bibliography section to FAOSTYLE author-date style on the
edited (not source) file. Rules, entry templates, APA-residue conversions, the
label-integrity contract and the escalation-to-author-action list are in
`references/references-rectification.md` with the full rule set in
`assets/references_formatting_rules.json`. Never invent URLs, DOIs, access dates;
use placeholders and log. Verify labels before and after.

### Phase 8 — Comment sheet & author-query round

Build the comment sheet for the author from the parked actions: every `[Author to
provide]` blocker, every struck reference entry earmarked for "Further reading",
every query needing author confirmation — plus every author-only issue the editing
passes surfaced (unclear actors, internal contradictions, chronology errors,
near-verbatim duplication, wording only the author can settle). **Apply the
routing test to every candidate row before it enters the sheet:** author must
supply/decide/confirm → comment sheet; editor must act (Word-stage mechanics,
`[SPECIAL]` application, corrections behind `⟦N|…⟧` tokens, re-sorts, importer
artifacts) → DOCX action sheet;
mixed → split into one author row and one editor row. A final sweep verifies no
editor-addressed row remains in the author sheet. Column structure
(`# | Position | Issue | Comment`, TSV), the routing test, the full issue-category
checklist, tone rules and the merge/verify workflow are in
`references/comment-sheet.md`.

### Phase 9 — DOCX handoff (editor_tool round-trip) + post-edit audit

Deliver the near-final DOCX by importing the rectified labeled markdown into the
unedited source DOCX kept since Phase 0:

```
python3 scripts/editor_tool.py --import <MS>_final_FAO_edited_refs_rectified.md <MS>.docx
```

The tool maps `[N]` labels to paragraph indexes and patches only changed
paragraphs (unchanged paragraphs stay byte-for-byte; in changed ones, unchanged
words keep their run formatting; heading styles survive). It applies markdown
bold/italic/strikethrough, keeps fields, citations, links, bookmarks and images
live, round-trips footnotes, and writes `<MS>_v1.docx` — it never overwrites. Rules:

- The import source is the rectified **labeled** file. Never hand off a
  label-stripped or freshly generated (e.g. pandoc-converted) DOCX: the round-trip
  exists precisely to retain the client's original formatting.
- Import with editor_tool v3 or later. A v3 export imported by an older copy
  writes the `⟦N|…⟧` tokens into the DOCX as literal text.
- `[SPECIAL]` paragraphs are **skipped on import**: edits under a `[SPECIAL]`
  label do not reach the DOCX. In v3 exports the tag marks only entries of a field
  that spans several paragraphs — table of contents, lists of tables/figures, a
  bibliography generated by Zotero/EndNote/Mendeley — and multi-paragraph
  footnotes. Hyperlinked reference entries are not `[SPECIAL]` in v3 and import
  normally.
- Read the import report. Every line under "need attention in Word" is a
  paragraph or footnote the importer left unchanged. If the cause is a token lost
  or duplicated in the markdown, restore the token and re-import into the unedited
  source DOCX; if not (an edited TOC entry, a multi-paragraph footnote), it becomes
  a DOCX action sheet row. "link target updated" lines are informational.
- Skipped `[SPECIAL]` edits, reported paragraphs and any other content the
  round-trip cannot carry (parked insertions, confirmed deletions) go into the
  **DOCX action sheet**
  (`<MS>_docx_action_sheet.tsv`, the editor's own worklist, separate from the
  author comment sheet; spec in `references/docx-action-sheet.md`). Note the
  action count in the technical review report and surface the sheet in the
  executive summary.
- If the labeled markdown was not produced by `editor_tool.py --export`, do not
  import — labels would not match paragraph indexes.
- Verify after import: paragraph count matches the label count; spot-check one
  edited body paragraph, one edited paragraph containing a token (the citation or
  cross-reference is still a live field in Word), one rectified reference entry
  (bold authors, italic title; if it has a URL, the link opens the new URL) and,
  if the export had any, one `[SPECIAL]` paragraph (unchanged).

Then run the post-edit acronym/foreign-language audit on the imported DOCX — flag
list only, no edits offered (see `references/acronym-foreign-check.md`, post-edit
mode).

## Editor action vs author action

**Fix editorially, do not report:** spelling variants, en-dash type and spacing,
`Fig.` → `Figure`, caption punctuation, `%` → `percent` in running text, thousands
separators, unit spacing, acronym redefinition at chapter starts, NOCS country
names, close-range repetition, reference-list formatting and ordering,
year-suffix normalization, whitespace, **headings and subheadings to sentence case
(FAOSTYLE §8.1)** — capitals only for the initial letter of the heading and any
proper names, with the first word after a colon also capitalized; retain published
capitalization when a heading is based on a conference, workshop, government
programme, project or journal name, and for defined proper terms used in the
manuscript (e.g. a capitalized programme role carrying an acronym). This applies
to every heading level, at every stage of the chain — if intake headings are in
Title Case, normalize them in 001NM1 so all downstream files and the DOCX
round-trip carry sentence-case headings.

**Report — publication-blocking:** missing citations for legal, statistical,
scientific and event claims; sources cited in text with no reference entry;
undocumented government decrees or international-organization decisions;
unattributed stakeholder claims; sentences that cannot be split without a meaning
judgement only the author can make; factual inconsistencies; missing permissions or
credit lines for third-party material.

## Deliverables

Produce all of these unless the user narrows the scope: the LANG-EVAL baseline
artifacts; pass CSVs (001NM1, 001NM2, 001WRR); citation report, in-text map, gap
analysis, editorial note TSV; final consolidated edited text; rectified references;
author action checklist; comment sheet; DOCX action sheet; technical review report; executive summary;
final DOCX. Item "final consolidated edited text" is the one people actually need.

## Run checklist

- [ ] Assets located; stated whether project or bundled copies are in use; mojibake check passed
- [ ] Locked mode acknowledged; label integrity verified before every delivery
- [ ] Phase 1 complete, five baseline artifacts written
- [ ] Phase 3 complete, both markers emitted; checkpoint 1 passed
- [ ] Phase 4 complete, four markers emitted; every 001NM2B split validated against 002ThV; checkpoint 2 passed
- [ ] Phase 5 complete, both markers and all four artifacts; density denominator stated; checkpoint 3 passed
- [ ] Word-count drift ≤ 8 percent; checksum clean outside logged edits
- [ ] Phase 6: final text, checklist, technical review, executive summary delivered
- [ ] Phase 7: rectification done under the label-integrity contract; report written
- [ ] Phase 8: comment sheet produced with the routing test applied row by row (no editor-addressed rows remain); merged with author responses when returned
- [ ] Phase 9: DOCX produced by editor_tool round-trip import into the unedited source DOCX; import verification done; [SPECIAL]-skipped edits and importer-reported paragraphs listed in the DOCX action sheet; post-edit audit flag list produced
- [ ] Conflicts hit during the run noted in the technical review report
