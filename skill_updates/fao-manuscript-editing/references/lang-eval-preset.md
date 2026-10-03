# LANG-EVAL preset (v1.3N — Neutral) — Phase 1 baseline

First-pass language analysis/triage for academic/scientific documents. Neutral
defaults so it can be applied to any client, any journal, any quotation request.
Language, client tags and citation style default to AUTO detection; numeric vs
author–date is inferred; percent/numbering styles are AUTO; house styles can be
passed via inputs.

**Mode: analysis only — no manuscript text is changed.** `phase=pre`,
`save_baseline=true`.

## How to run

Point the preset at the labeled markdown produced in Phase 0:

```
run LANG_EVAL with { doc_path="<Article>_final_for_ai.md" }
```

Key settings: `language="auto"`, `language_variant="auto"`, `numeric_style="auto"`,
`wr_mode="001WRR-S"`, `analysis_only=true`, `citation_style_target="auto"`,
`author_date_flavour="auto"`, `phase="pre"`, `save_baseline=true`.

## The preset (verbatim)

```dsl
define_preset LANG_EVAL {
  task="academic_language_analysis";
  version="1.3N";
  description="Neutral, journal-agnostic language analysis with auto detection for language variant and citation style; supports pre/post delta metrics and quotation categorisation.";

  inputs = {
    doc_path: "<required: path to .docx/.pdf/.md>",
    cover_letter_path: "<optional>",
    instructions: "<optional: free-text editorial instructions from client>",
    client_tags: [],
    language="auto",
    language_variant="auto",
    numeric_style="auto",               # auto | namc_percent_symbol_nbsp | fao_percent_word
    wr_mode="001WRR-S",                 # 001WRR-S (section) or 001WRR-P (page)
    analysis_only=true,
    citation_style_target="auto",       # auto | author_date | numeric
    author_date_flavour="auto",         # auto | Harvard_comma | Chicago_no_comma
    phase="pre",
    save_baseline=true,
    baseline_metrics_path="",           # when phase=post, path to pre metrics
    section_heading_regex="^#{1,3}\\s|^(?:Abstract|Introduction|Methods|Methodology|Results|Discussion|Conclusion|References)\\b"
  };

  spelling_variant_lock=(language != "auto");
  typography = {
    spaces_around_percent = (numeric_style == "namc_percent_symbol_nbsp");
    percent_word = (numeric_style == "fao_percent_word");
  };

  detectors = {
    long_sentence_threshold=34;
    this_verb_openers=true;
    there_verb_openers=true;
    repetition_001WRR=true;
    mixed_english_variant=true;
    article_determiner_omission=true;
    passive_voice_ratio=true;
    nominalisation_density=true;
    cohesion_markers_scan=true;
    tense_consistency=true;
    inline_citation_conformity=true;
    figure_table_caption_style=true;
    numeric_citation_detected = (citation_style_target == "numeric"
                                 || (citation_style_target == "auto" && detect_numeric_citations()==true));
    author_date_detected = (citation_style_target == "author_date"
                            || (citation_style_target == "auto" && detect_author_date_citations()==true));
    square_bracketed_author_year = author_date_detected;
  };

  scoring_axes = { grammar=0.30, structure=0.20, cohesion=0.20, tone_register=0.15, consistency=0.10, readability=0.05 };
  scoring_notes="Export both /10 and %; deltas computed when baseline provided.";

  edit_intensity_map = [
    {score_min: 8.5, label: "Light",        lines_percent: "≤15%"},
    {score_min: 7.0, label: "Medium",       lines_percent: "20–40%"},
    {score_min: 5.5, label: "Medium-Heavy", lines_percent: "35–55%"},
    {score_min: 0.0, label: "Heavy",        lines_percent: "≥60%"}
  ];

  quotation = {
    threshold_percent=85;
    label_high="Standard language editing";
    label_low="Intermediate–Heavy language editing";
    embed_in_report=true;
    report_line_template="Quotation category: ${label} (${score_percent}% ${operator} ${threshold_percent}%)";
  };

  modules = {
    phase1="001NM1,001NM2,001NM3";
    phase2="001WRR,002ThV,001NM2B";
    paraphrase_sentence=false;
    rephrase_sentence=false;
    rephrase_phrase=true;
    genuine_error_rephrase=true;
  };

  rules = [
    { id: "CIT-AD-001", enabled: author_date_detected,
      description: "Author–date citations must use parentheses, not square brackets.",
      pattern: "\\[(?:[A-Z][A-Za-z\\-]+[^\\]]*?\\d{4}[a-z]?[^\\]]*?)\\]",
      exclude_if: "numeric_citation_detected",
      message: "Author–date citation detected in square brackets. Use parentheses for author–date.",
      suggest: "Replace […] with (…). Then harmonise commas per selected flavour." },
    { id: "CIT-AD-002", enabled: (author_date_detected && (author_date_flavour == "Chicago_no_comma")),
      description: "Chicago author–date (no comma).",
      pattern: "\\(([^()]+?),\\s*(\\d{4}[a-z]?)\\)", replace: "(\\1 \\2)",
      message: "Drop the comma between author and year for Chicago author–date." },
    { id: "CIT-AD-003", enabled: (author_date_detected && (author_date_flavour == "Harvard_comma")),
      description: "Harvard author–date (comma).",
      pattern: "\\(([^()]+?)\\s+(\\d{4}[a-z]?)\\)", replace: "(\\1, \\2)",
      message: "Insert a comma between author and year for Harvard author–date." },
    { id: "CIT-AD-004", enabled: author_date_detected,
      description: "Unify multi-citations separator to '; '.",
      pattern: "\\)\\s*,\\s*\\(", replace: "; ",
      message: "Use '; ' between multiple citations inside the same parentheses." },
    { id: "CIT-AD-005", enabled: author_date_detected,
      description: "Normalise page locators: '(Author Year, 45–47)'.",
      pattern: "\\(([^()]+?),\\s*(\\d{4}[a-z]?)\\s*[:|,]\\s*([\\d–\\-]+)\\)",
      replace: "(\\1 \\2, \\3)",
      message: "Move page range after the year, separated by comma." }
  ];

  outputs = {
    report_md_path="LANG-EVAL_report.md";
    findings_csv_path="LANG-EVAL_findings.csv";
    compliance_tsv_path="LANG-EVAL_compliance.tsv";
    metrics_json_path="LANG-EVAL_metrics.json";
    metrics_csv_path="LANG-EVAL_metrics.csv";
    include_rules_checklist=true;
    include_scores_table=true;
    include_edit_intensity=true;
    include_quotation_category=true;
    include_citation_policy_note=true;
    delta_csv_path="LANG-EVAL_delta.csv";
    delta_report_md_path="LANG-EVAL_delta.md";
  };

  metrics_schema = [
    "overall_score_10","overall_score_percent","grammar","structure","cohesion","tone_register","consistency","readability",
    "sentences_total","mean_sentence_len","long_sentences_gt34","long_sentences_gt40",
    "this_there_openers","passive_flags","nominalisation_per100w","root_repetition_sentences",
    "mixed_en_variants_count","cohesion_paragraph_starters","figures","tables","bracket_citations_count",
    "quotation_category","edit_intensity_label","edit_lines_percent_est",
    "citation_style_detected","author_date_flavour_detected"
  ];

  quality_gates = {
    min_overall_increase=0.5,
    max_long34_reduction=0.30,
    target_this_there=0,
    target_mixed_variants=0,
    nominalisation_delta=-0.5,
    citation_brackets_zero=(author_date_detected),
    pass_text="Ready to deliver ✔",
    fail_text="Needs another pass ✖"
  };

  report_sections = [
    "1. Executive Summary",
    "2. Scores & Edit Intensity",
    "2a. Quotation category (auto-generated)",
    "3. Key Issues (ranked)",
    "4. Detailed Findings (with examples + fixes)",
    "5. Style/Convention Checks (auto-detected/overridable)",
    "6. Reviewer-alignment check (if cover_letter_path provided)",
    "7. Rules enforced (checklist) & next steps"
  ];

  delta_sections = [
    "A. Summary of improvements (score, intensity, quotation category)",
    "B. Metric deltas table (before → after → Δ)",
    "C. Issue reductions (long sentences, This/There, repetition, mixed variants)",
    "D. Quality gates result (pass/fail with reasons)",
    "E. Per-section highlights (optional, if headings detected)"
  ];

  reviewer_alignment = {
    enabled=true,
    requires_cover_letter=true,
    checks=[
      "Claims addressed linguistically (clarity/transition)",
      "Abstract/objective clarity vs paper body",
      "Terminology harmonised post-revision"
    ]
  };

  behaviour = {
    limit_examples_per_issue=2;
    sample_fix_length="1–2 sentences";
    preserve_author_voice=true;
  };
}
```

## FAO-specific operating notes (added by this project)

- Auto-detection results for FAO manuscripts settle typically as: British English with
  FAO -ize preference; author–date with Harvard-like comma; `numeric_style` resolved
  per `conflicts.md` (percent as word; NBSP thousands separators).
- Citation density uses the pipeline's fixed denominator: in-text citations ÷
  body-text sentences × 100; publish raw counts and per-chapter distribution.
- FAO conflict decisions applied during analysis are listed in the report
  (year ranges, thousands separators, -ise candidate-generator treatment, 002ThV
  expanded regex, ACR-DEF-001 chapter scope).
- The report must separate `[Author to provide]` blockers from editorial fixes —
  this baseline drives the Phase 8 comment sheet.

## P1 baseline (2026-08-05, for benchmark comparison)

Overall 7.28/10 (72.8%); Medium intensity (20–40% of lines, central 30%);
quotation category Intermediate–Heavy. 4 083 body words, 165 sentences, mean 24.75
words; 25 sentences >34; 5 This/There openers; 43 passive flags; 8 close-range
repetition locations; 6 mixed-variant tokens; 38 author–date instances / 33 unique
sources / 54 reference entries / 15 apparently uncited; density 23.03 percent;
abstract missing. 36 findings; 30-rule compliance checklist (9 pass/N/A, 6
warnings, 15 fail).

## Post-edit delta (optional, Phase 9)

Re-run with `phase=post` and `baseline_metrics_path` pointing at the pre-edit
metrics to produce `LANG-EVAL_delta.csv` / `LANG-EVAL_delta.md` and evaluate the
quality gates. Suggested gates for FAO runs: overall increase ≥ 0.5; long-sentence
count reduced ≥ 30 percent; This/There = 0; mixed variants = 0; square-bracket
author–date citations = 0.
