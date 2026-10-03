# Project assets — inventory, resolution and precedence

## Table of contents

1. Resolving asset paths
2. Asset inventory
3. Mojibake check
4. Styleguide source
5. Conflict-resolution precedence (decisions already taken)

## 1. Resolving asset paths

Project-supplied copies are the live versions; bundled snapshots are a fallback
dated October 2025. Resolve at Phase 0 and state which set is in use. In this
project the live set lives in the project's upload/mount folder (historically
`/mnt/agents/upload/`); the job card may reference `/mnt/project/` — if that path
does not exist, use the upload folder and note it in the technical review report.

## 2. Asset inventory

| File | Read it when |
|---|---|
| `house-style.md` | Any spelling, punctuation, number, capitalization, naming, caption, publication-structure, or footnote/endnote question — FAOSTYLE §2–§11 in full |
| `recommended-words.md` | A specific word's preferred form isn't obvious — full A–Z list (FAOSTYLE Appendix 2, ~1 100 entries). Check **before** applying the -ise → -ize regex or any other blanket spelling rule |
| `citations-rules.md` | Validating or formatting citations; building a reference list; quoting a rule number to the author (142 rules, by category) |
| `conflicts.md` | Two sources disagree; before applying any number, percent, dash or -ise rule; §10 for encoding caveats |
| `nocs_lookup.json` | 866 keys → FAO short country name (NOCS enforcement) |
| `fao_termlist.json` | Acronym expansions and term translations for the standalone audit |
| `fao_recommended_words.json` | Same ~1 100 entries as recommended-words.md, structured for programmatic lookup |
| `fao_styleguide_schema.json` | Authoritative `scope` field for ACR-DEF-001 |
| `fao_styleguide.md` | The official styleguide in markdown — replaces the PDF guide (see §4) |
| `FAO_AGENTS_CONFIG_UPDATED.yaml` | Job card: agent roster, pass definitions, checkpoint configuration, citation-gap-analysis categories and artifact paths |
| `editor_tool.py` | The client's DOCX ⇄ labeled-markdown bridge. Phase 0 export (if only the DOCX is supplied) and Phase 9 import (edited labeled markdown → unedited DOCX, formatting retained). A project-supplied copy wins over the skill's bundled `scripts/editor_tool.py`, unless it is older than v3 (a v3 copy contains the string `editor_tool v3 export`): then use the bundled copy and say so, because an older importer writes v3 `⟦N|…⟧` tokens into the DOCX as literal text |

The unedited source DOCX is itself an intake asset: when the client supplies it
alongside the labeled markdown, keep it untouched for the Phase 9 import.

FAOSTYLE §1 (scope) and Appendix 1 (external links) are low-value for automated
editing and are not needed. Appendices 3–4 (Word shortcuts, Zotero setup) are
software how-tos, not editorial rules.

## 3. Mojibake check

Project text assets have been observed double-encoded (UTF-8 decoded as cp1252 and
re-encoded), which puts corrupted strings such as `CÃ´te dâ€™Ivoire` into the
*preferred* field — the pipeline would then write that into the manuscript as the
correction. Before trusting any asset, count matches of `[ÃÂ][\x80-\xBF]|â€` in each
text asset; non-zero means repair first with `scripts/fix_encoding.py`, then
regenerate anything derived from the asset. Detail and residual-content caveats are
in `conflicts.md` §10. Record the check result in the technical review report.

## 4. Styleguide source

The official styleguide is maintained in markdown (`fao_styleguide.md`) and
**replaces the PDF guide** (`cb8081en.pdf`). In normal use the transcribed reference
files above suffice and the styleguide should not need to be opened; consult it only
to verify wording or when a project copy contradicts the transcription — report the
discrepancy rather than silently picking one. Some historical project copies of the
PDF arrived as plain text despite the extension; if a PDF copy must be consulted,
read it with `grep`/`sed`, not a PDF library.

## 5. Conflict-resolution precedence (decisions already taken)

These decisions are settled for this project — apply them, and note in the technical
review report that they were hit:

- **Year ranges:** FAOSTYLE takes precedence over the schema's compact-year example
  → full years ("2017–2018", not "2017–18").
- **Thousands separators:** non-breaking space (U+00A0) for Word manuscripts; the
  001WRR preset's thin-space setting loses.
- **-ise → -ize:** the regex is a candidate generator only — protect "analyse",
  "paralyse", "catalyse", "dialyse", "hydrolyse" and words like "promise",
  "expertise", "supervised"; never touch quoted/published titles.
- **002ThV opener regex:** use the full expanded pass regex (27-verb superset), not
  the short schema validation pattern.
- **Acronym scope (ACR-DEF-001):** client override of FAOSTYLE's softer advisory —
  define abbreviations at first substantive mention in each chapter (Heading 1) or
  self-standing section. Heading 2/3 subsections do not reset the requirement. FAO
  and COVID-19 are exempt from definition by name — never flag or expand them.
- **Percent:** `%` → "percent" in running text (FAOSTYLE §10.2); the schema's
  "per cent" override permits but does not require the two-word form.
- **Number spell-out:** both sources agree above ten; boundary cases involving
  "ten" itself are decided per `conflicts.md` §1.
