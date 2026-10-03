# Acronym & foreign-language audit — standalone check (Phases 2 and 9)

A narrow audit that does exactly two jobs and nothing else:

1. Audit acronym/abbreviation definition against `ACR-DEF-001` (chapter-scoped).
2. Audit foreign-language words and names for italics and translation compliance.

It is independent of the editing passes: it does not run any of them and does not
touch citations, sentence length, NOCS, or spelling. Its flag lists are **not** the
same as the pipeline's editorial-note TSV and must not be merged into it silently —
state this at the top of every combined output.

Why a separate audit: the editing passes work in a 20-line window; acronym
definition and foreign-language translation are document-structural problems
("defined anywhere earlier in this chapter?") that need a whole chapter in view.

## The governing constraint — never invent

An expansion or translation is a factual claim. Getting it wrong — even plausibly
wrong — is worse than leaving it unresolved. Draw an expansion/translation from
exactly two sources, in this order, and no others:

1. Found elsewhere in the document itself (reuse verbatim).
2. Found in project reference material — `fao_termlist.json`, `house-style.md`, other
   project glossaries (reuse verbatim).

If neither has it, do not construct one from general knowledge, however confident
the guess feels. Insert a placeholder in the exact spot the expansion/translation
belongs (`[EXPANSION NEEDED] ACRONYM` / `[TRANSLATION NEEDED] (*foreign title*)`)
**and** add a corresponding line to the output flag list. Placeholder and flag
always travel together.

## Run modes — fixed defaults

### Pre-edit mode (markdown) — Phase 2

On the labeled markdown immediately after conversion from the editor's DOCX, before
fao_editor1 starts. **Default: produce the flag list and stop.** Do not apply edits
or output a new markdown in the same run. Edits happen only on a separate, explicit
follow-up request (e.g. "apply the approved changes") after the user has reviewed
the list — never bundle flagging and fixing into one run unless the user explicitly
asked for that up front.

Chapter detection, in order of preference:

1. Real markdown heading syntax (`#`, `##`, …) — the expected case; treated as
   reliable as DOCX-based detection.
2. Fallback — numbering-depth inference (only if no heading markup: `2. …` vs
   `2.1 …`). **Always state when this fallback was used** — it is inference, and
   chapter-boundary-dependent findings should be cross-checked against the DOCX
   before being treated as final.

`[N]` labels are never added, removed or renumbered; insertions go *within* labeled
paragraphs.

### Post-edit mode (DOCX) — Phase 9, always flag-list-only

On the DOCX when it is nearly ready, as an independent final check. Produce the
flag list and stop — full stop. No edit path exists in this mode; do not ask whether
to apply fixes. Chapter boundaries come from `pStyle="Heading1"`. This mode also
sees what markdown cannot: strikethrough state, run-level italics, page numbers.

## Part 1 — Acronym audit

Fixed rules:

- **Chapter = Heading 1 only** (confirmed against `fao_styleguide_schema.json`'s
  `"scope": "chapter"` — a documented client override of FAOSTYLE's softer
  advisory). Heading 2/3 subsections do not independently reset the requirement;
  only the true first substantive use in the chapter matters. The Abstract is its
  own stand-alone section.
- No periods in acronyms (`CFS`, not `C.F.S.`); plural without apostrophe (`NGOs`).
- Define in singular; plural is acronym + bare `s`, no re-definition within a chapter.

Step 1 — Segment the manuscript into chapters (per run mode above).
Step 2 — Find every acronym: tokens of 2+ consecutive capital letters, optional
trailing lowercase `s`. One list per chapter, then a deduplicated document-wide list.
Step 3 — Classify before judging (exemptions first; false positives erode trust):

- **Citation-shorthand** — bare acronym as in-text citation author (`(CILSS, 1994)`)
  is governed by citation rules; check the same acronym separately for substantive
  prose use in the chapter.
- **Legal/decree/instrument reference codes** — fragments inside formal numbering
  (`Decree No. 031/PCMT/PM/MAFDHU/SG/2022`) are not narrative acronyms.
- **Keywords lines and other metadata**, as distinct from running prose.
- **"Universally known" forms** — apply confidently to e.g. UN. For any *other*
  organization-specific acronym treated as exempt, record the assumption as an
  editor discussion note. **FAO and COVID-19 are named FAOSTYLE exceptions: exempt
  in every chapter and section — never flag, never expand.**

Step 4 — First use in each chapter:

- **Missing at true first use** → find and insert verbatim per the governing
  constraint, or insert `[EXPANSION NEEDED]` + flag (chapter, page in DOCX mode,
  acronym).
- **Redundantly re-expanded within the same chapter** → prune the later expansion
  (authorized, but in pre-edit mode still flag-only until follow-up authorization;
  in post-edit mode flagged only).
- **Correctly defined already** → no action, no flag.

Step 5 — Reference-list corollary: corporate/organizational authors alphabetized by
abbreviation must give their full name in the list too (rule 64). Same discovery
hierarchy; never invent.

## Part 2 — Foreign-language word and name audit

Step 1 — Find candidates: non-English words, phrases, titles, proper names.
Italicized runs are a starting point, not the whole set — also check plain-text
foreign terms that should be italicized.

Step 2 — Italics decision:

- **Not italicized:** foreign proper nouns, personal/company/organization names,
  currency names (e.g. `Centre de coopération internationale en recherche
  agronomique pour le développement (CIRAD)`); naturalized Latin borrowings
  (`ad hoc`, `de facto`, `per capita`).
- **Italicized despite the general rule:** `et al.` — a named carve-out; check
  `recommended-words.md` for others.
- **Italicized:** titles of foreign-language works, laws or instruments that are not
  organization names (e.g. `Code du Domaine National`).
- Keep diacritics regardless of the italics decision.

Step 3 — Translation necessity: if a foreign word/phrase/title/name is
comprehensible only to a reader of that language, it needs a translation at first
occurrence. Order: official translation → found elsewhere in document or project
reference material → neither: placeholder + flag. Never construct one.

Step 4 — Placement:

- **Non-abbreviated foreign title/name:** English translation leads, foreign form
  follows in italics inside round parentheses: `National Domain Law (*Code du Domaine
  National*)`; unresolved: `[TRANSLATION NEEDED] (*Code du Domaine National*)`.
  Scope: document-wide first occurrence only.
- **Abbreviated foreign term** (acronym-form): scope follows the acronym's own
  chapter scope from Part 1.

Step 5 — Capitalization: foreign institutional and title names take sentence case
(first word only). Before guessing, check whether the manuscript already has a
correctly-formed sibling name — an existing correct instance outweighs the general
rule.

## Output — always three sections

1. **Mechanical placeholder flags** — one line per `[EXPANSION NEEDED]` /
   `[TRANSLATION NEEDED]` (chapter, page in DOCX mode, term, insertion point).
2. **Standard violation flags** — rule-based fixes applied or proposed (missing
   definition where an expansion was found, redundant re-expansion, italics
   corrections, translations added from official/in-document sources).
3. **Editor discussion notes** — separate, always headed separately. Anything that
   was a call rather than a mechanical fix: "universally known" assumptions (not FAO
   /COVID-19 — their exemption is a named rule), conflicting forms found in two
   places (name both forms and where; let the editor decide), borderline
   italics/proper-name calls, ambiguous scope situations, anything less than fully
   confident. Each note: what was found, what call was made, why — enough for the
   editor to agree or overrule in one read.

Pre-edit mode: all three sections as flag/notes only unless edits were separately
authorized — then apply mechanical fixes (sections 1–2) preserving `[N]` labels;
section-3 items are never auto-applied. Post-edit mode: all three sections,
flag/notes only. Do not produce pipeline artifacts (citation reports, markers,
checkpoints).
