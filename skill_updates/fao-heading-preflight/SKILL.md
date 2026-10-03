---
name: fao-heading-preflight
description: >-
  Pre-edit structural check of a manuscript's headings and document architecture, run before
  any FAO editorial pass. Use this skill when the user hands over a manuscript (markdown
  export, .docx, or a GitHub repo path) and asks about headings, titles, hierarchy, heading
  levels, ToC structure, or says the headings look "too long", "not heading-like", or that the
  hierarchy is wrong — and as the first step whenever a new paper in an FAO series arrives for
  editing, before fao-editorial-workflow runs. It produces two deliverables: a
  `original,to_replace` CSV of mechanical heading fixes, and a comment-sheet TSV of the
  structural questions only the author can settle.
---

# FAO heading preflight

## Why this runs first

Heading defects are cheap to fix before editing and expensive afterwards. A wrong heading
level propagates into the table of contents, the running heads, the ToC entries FAOSTYLE
§2.1.3.4 requires, and — in a multi-paper series — into inconsistency between papers that a
reader sees at a glance. Once copyediting has started, every heading change also invalidates
the page and paragraph references already written into the comment sheet.

So this pass runs on the incoming manuscript, before `fao-editorial-workflow`, and it touches
headings and document architecture only. Body text is out of scope here.

## What the output is

Two deliverables, and the split between them is the whole point of the check:

| Deliverable | Holds | Test |
|---|---|---|
| `{{doc}}_heading_replacements.csv`, columns `original,to_replace` | Mechanical, unambiguous fixes the editor makes on their own authority | Applying it changes no meaning and needs no author knowledge |
| `CommentSheet_{{doc}}_headings.tsv` | Structural questions and anything meaning-bearing | The right answer depends on what the author intended |

If an item could go either way, put it in the TSV and leave the manuscript alone. A structural
change made silently is the one thing the author cannot audit later.

Heading-level changes are not string swaps, so encode them in the CSV as markdown markers in
both columns (`# Heading` → `## Heading`). If the source is .docx rather than markdown, state
the change as a style name instead (`Heading 1` → `Heading 2`) and flag that it has to be
applied through Word styles, not direct formatting.

## Step 1 — build the heading inventory

Run `scripts/extract_headings.py <file>`. It handles the editor_tool v2 markdown export
(`[N] # Heading` lines, plus bold-only paragraphs, which are frequently a title or a heading
that lost its style) and .docx (paragraphs with a Heading style, plus bold-only paragraphs).

Read the output as a table of position, level and text before judging anything. Most of the
findings below are visible only in the set — a heading that reads fine alone breaks
parallelism with its siblings.

If the file is in project knowledge rather than on disk, retrieve it with
`project_knowledge_search` and build the inventory by hand; the checks are the same.

## Step 2 — the checks

Work through these against the inventory. Each names where it belongs.

**Architecture**

1. **Is the title a heading?** A title set as bold body text leaves the document with no
   top-level heading, so every section renders level with the title. → CSV.
2. **Are levels contiguous?** Flag a jump (H2 → H4) or a flat run where everything sits at one
   level. → CSV, unless the flattening looks deliberate, in which case ask.
3. **More than four levels?** FAOSTYLE §2.2.3 caps the hierarchy at four including parts and
   chapters. → TSV; collapsing levels is an author decision.
4. **End-matter headings numbered?** Under author–date, the list is titled *References*
   (§2.1.5.1) and carries no section number. → CSV.
5. **Section numbering consistent with the series?** FAOSTYLE §2.2.3 discourages numbered
   subheadings unless cross-referencing needs them, but an established series precedent
   outranks that preference — check a delivered paper before stripping numbers. → TSV if the
   manuscript departs from its own series.

**Wording**

6. **Vague quantifiers.** FAOSTYLE §3.1 lists *a few, some, many, enough, several, a number of*
   as conveying no useful information; in a heading they also mislead about the section's
   weight. → CSV.
7. **Sentence case.** FAO headings take sentence case; flag capitalised content words
   mid-heading. Proper nouns and instrument names stay as they are. → CSV.
8. **Parallelism across siblings.** Headings at one level under one parent should take the same
   grammatical shape. A single odd one out is usually the error. → CSV if the fix is a word or
   two; TSV if it means rewriting the set.
9. **Length.** §2.2.3 asks for headings "as concise as possible", and running heads have to
   survive shortening (§2.2.2). Anything past about a dozen words, or carrying a subordinate
   clause, is worth flagging. → TSV, since shortening involves deciding what to drop.
10. **Not heading-like.** A finite-verb sentence, a question, or terminal punctuation means the
    line is doing the work of a topic sentence. → TSV with a proposed noun phrase.
11. **Subtitle punctuation.** FAO sets subtitles off with a spaced en dash rather than a colon
    (FAOSTYLE Box 2.1 examples). If the manuscript is destined for a journal with its own
    convention, query rather than change. → TSV when the destination is a journal, CSV when
    it is an FAO information product.
12. **Duplicate or near-duplicate headings** in different sections. → TSV.

**Balance**

13. **Section length against the heading count.** A section running many paragraphs while its
    siblings run two or three usually contains an unmarked shift of subject. Say where the
    shift falls, offer split / sub-heading / leave-as-is, and make no change. → TSV.
14. **Orphan headings** — a heading immediately followed by another heading with no text
    between, or a lone sub-heading with no sibling. → TSV.
15. **Missing structural elements** the series uses elsewhere: abstract, keywords, references.
    Report as an observation, not a defect, unless the paper type calls for them. → TSV.

## Step 3 — the comment sheet

Match the project's existing comment-sheet layout rather than inventing one.
`assets/comment_sheet_template.tsv` holds it:

- Row 1: empty cell, `Linguistic revision`, `Document name:`, `{{document name}}`, empty cell
- Row 2: empty
- Row 3: `#` · `Position` · `Issue` · `Comment` · `Remarks`
- Rows 4+: one issue each, `Remarks` left empty for the author

Conventions that keep the sheet usable:

- `Position` takes page numbers when the author works in Word. For a markdown export with no
  pagination, use the `[N]` paragraph numbers and say so in the covering note, so the author
  knows why the column looks unfamiliar.
- `Issue` is a short diagnosis; `Comment` carries the proposal, the grounds and the request. If
  a finding rests on several distinct grounds, number them within the cell so the author can
  accept one and reject another.
- Cite the FAOSTYLE section for each judgment call. A rule number turns a matter of taste into
  a matter of record.
- Where no change was made pending the author's decision, say so in the `Comment` cell.
- Keep tabs and newlines out of the cells; the sheet is round-tripped through spreadsheet
  tools that split on them.

Finish with a short chat summary: the inventory as a table, the findings in priority order, and
anything that blocks the editorial pass.

## Constraints

These hold regardless of what the check turns up:

- Never alter `[N]` paragraph numbers in the markdown export, and leave `[SPECIAL]` lines
  untouched — they carry Word fields, images or hyperlinks that are re-imported verbatim.
- Body text is out of scope. If a heading fix implies a body change (a cross-reference to a
  renumbered section), record it in the TSV rather than making it.
- Renumbering sections changes every cross-reference in the paper and, in a series, the
  numbering readers see across papers. It needs author sign-off.
- Do not propose a heading that asserts something the section does not support. The heading is
  the author's claim about their own text.
