# Pass definitions and phase receipts

Transcribed from `FAO_AGENTS_CONFIG_UPDATED.yaml` (v2025-11-03) pass_definitions and
the receipts of proven runs (P8, P14, P16, 2026-08). Read before running Phases 3–5
and when a checkpoint fails.

## Table of contents

1. Global settings
2. 001NM1 — phrase correction
3. 001NM2 — long-sentence detection
4. 001NM2B — sentence splitting
5. 001NM3 — verification
6. 001WRR — repetition scan
7. 002ThV — openers and length validation
8. Checkpoint configuration
9. Citation agent configuration
10. Proven-run benchmarks (what "normal" looks like)

## 1. Global settings

- window_size_lines: 20 (all editing passes; citation phase uses full text)
- language: British English (FAO -ize preference); style: UK
- locked mode: no paraphrasing, no rephrasing, no synonym substitution
  (001WRR's `replace_with_synonym` is that pass's own documented last-resort fix)
- word-count drift between original and edited ≤ 8 percent
- spelling enforcement variant: British_FAO (`marginalised` → `marginalized`,
  `realising` → `realizing`, general `([A-Za-z]+?)ise` → `\1ize` with exceptions
  analyse/paralyse/catalyse/dialyse/hydrolyse — and see the protected-words rule in
  project-assets.md §5)

## 2. 001NM1 — phrase correction

- step_by_step: true; rephrase_sentence: false; rephrase_phrase_if_awkward_incorrect: true
- detect_close_range_repetition: true
- output: final version + CSV (`original,replacement`)
- enforce_word_count_similarity: true, max gap 8 percent
- dashes: en dash, spaced parenthetical asides (em dashes converted)
- Scope discipline: fix what is wrong; leave correct-but-clumsy sentences untouched.
  Typical fixes: typos and concatenations, citation ampersands → "and" (rule 23),
  multi-author citations → "et al." (rule 28), serial-comma removal, "Sub-Saharan" →
  "sub-Saharan", percent word form, NOCS country names, acronym definitions at
  chapter starts, **Title Case headings → sentence case (FAOSTYLE §8.1)**: every
  heading level keeps capitals only on the initial letter and proper names; the
  first word after a colon is capitalized; headings based on a conference,
  workshop, government programme, project or journal name keep the published
  capitalization, as do defined proper terms used in the manuscript (e.g. a
  capitalized programme role carrying an acronym). Heading case normalization is
  part of 001NM1 so every downstream pass file and the DOCX round-trip inherit it.

## 3. 001NM2 — long-sentence detection

- find_sentences_longer_than: 34; list_longer_sentences: true; rephrase: false
- output: CSV `words,sentence`, csv_quote_all: true
- Detection only — no editing in this pass.

## 4. 001NM2B — sentence splitting

- split: true; rephrase: false; rephrase_at_split: true (rephrasing ONLY at the split point)
- resulting_split_worsen_sentence: false; accept_split_if_worsen: false;
  try_alternative_split: true
- fallback_to_no_split: true — mandatory for verbatim quotations of law/policy text
  (rule 42 forbids altering quoted law); log each fallback with its reason
- fallback_to_conditional_pattern: true
- validate_rule_002ThV: true; output_only_if_rule_002ThV_passed: true;
  halt_on_rule_002ThV_failure: true
- Logged exceptions observed in proven runs: official instrument titles kept whole
  (precision), enumeration lead-ins (allow_enum_leadin_exception). Three residual
  >34-word sentences with logged exceptions is a normal outcome — a short
  exceptions list in the technical review report, not a failure.

## 5. 001NM3 — verification

- final_review: true; final_version: false (emits findings, no text)
- include_only_genuine_errors: true; QA_checklist: true
- Not a second editing pass. Genuine-error QA checklist plus attribution queries
  logged as `[Author to confirm]`.

## 6. 001WRR — repetition scan

- mode: 001WRR-S (section; 001WRR-P page is the alternate)
- scope: sentence + consecutive bullets; use_lemmas: true
- exclusions: client terms, locked UI labels, technical necessities (topic terms
  such as the manuscript's subject keyword are technical necessities, not
  repetition), numbers count as repetition
- fix_apply: true; fix_order: avoid_duplicate > keep_one > prefer_deletion >
  replace_with_synonym (last resort); fix_minimal: true
- output: CSV `ID,Page,Section,Description,Action,Completed revised`, header included
- revision_preserve_punctuation: true; preserve_numeral_spacing: true
- id_pattern: `001WRR-{mode}-{page_section_code}-NN`
- NOTE: the pass's own `thousands_spacing: thin_space` is overridden by the project
  conflict decision — NBSP (see project-assets.md §5)

## 7. 002ThV — openers and length validation

- target 18–28 words; hard_cap_words: 34
- opener_block_regex (full expanded pass regex — use this, not the short schema
  pattern):
  `^(?:This|There)\s+(?:is|are|was|were|has|have|should|must|could|may|might|will|would|can|cannot|does|do|did|seems|appears|shows|suggests|indicates|examines|argues|illustrates|presents)\b`
- split_policy: prefer_split_over_34_unless_enum_or_precision;
  allow_enum_leadin_exception: true
- preserve_punctuation: true; respect_client_locks: true; avoid_synonym_drift: true;
  merge_split_only_when_essential: true; paragraph_flow_preserve: true
- output: corrected text, no change log
- Openers are warnings, not automatic errors: substitute a concrete subject only
  where the meaning is unchanged.

## 8. Checkpoint configuration

| Checkpoint | Expects | Fail action |
|---|---|---|
| checkpoint_editor1_done | 001NM1_marker, 001NM3_marker | auto_rerun_missing_only; halt if still missing |
| checkpoint_editor2_done | 001NM2_marker, 001NM2B_marker, 001WRR_marker, 002ThV_marker | auto_rerun_missing_only; halt if still missing |
| checkpoint_citation_agent_done | FAO_citation_marker, FAO_citation_gap_marker + 4 artifacts under reports/ | auto_rerun; halt if still missing |

require_phase_receipt: true; require_zero_diff_receipt_ok: true;
audit_trail_mode: verbose. A checkpoint that fails twice → halt and report which
markers/artifacts are missing.

## 9. Citation agent configuration

- style: FAO Author-date; version 2.0; tasks: validate_and_format_citations,
  identify_citation_gaps (gap analysis is mandatory, not optional)
- verify in-text citations, reference-list presence, crosslink references,
  normalise suffixes
- author matching: strip punctuation, ignore case; corporate aliases
  (FAO., Food and Agriculture Organization of the United Nations, Food & Agriculture
  Organization; The World Bank, World Bank Group); fuzzy year tolerance 1
- gap analysis: priority categories critical / high_priority / recommended;
  include line references; suggest citation types; flag unsupported paragraphs;
  check per-chapter distribution
- claim categories requiring citations: legal/policy references (critical),
  specific dated events (critical), statistical claims (critical), empirical claims
  (high), scientific claims (critical), historical facts (high), programme
  descriptions (recommended), causal claims (high)
- artifacts: reports/FAO_citation_report.tsv, reports/intext_citation_map.tsv,
  reports/FAO_citation_gap_analysis.txt, reports/FAO_citation_editorial_note.tsv
- density target 2.0–5.0, denominator fixed as in-text citations ÷ body-text
  sentences × 100; publish raw counts; above-band density on legal-policy analysis
  manuscripts is a note, not an error

## 10. Proven-run benchmarks

Reference points from the 2026-08 runs (use to sanity-check a new run, not as quotas):

- P16 (~5.4k words): 001NM1 = 35 spelling conversions + 3 percent + 7 range dashes
  + 2 NBSP + 4 numerals + 3 predate forms + 1 serial comma; 001NM2 = 48 sentences
  >34; 001NM2B = 49 splits accepted; 001WRR = 5 rows; 002ThV = 0 opener violations;
  citation = 30 entries, 58 in-text instances, 5 critical + 4 high + 2 recommended
  gaps; drift +3.4 percent.
- P8 (single self-standing article): 001NM1 = 34 paragraphs edited; 001NM2 = 65
  >34; 001NM2B = 31 splits, 24 fallbacks to no_split (verbatim legal quotations).
- Normal residual: a small number of >34-word sentences under logged exceptions
  (official titles, enumeration lead-ins, verbatim law).
