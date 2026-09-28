# solterra-batch-translation

## Contents

1. `solterra-batch-translation/SKILL.md`
2. `solterra-batch-translation/transit_context.py`
3. `solterra-batch-translation/reference/translation-memory.csv`
4. `solterra-batch-translation/reference/terminology.csv`
5. `solterra-batch-translation/reference/patterns.csv`
6. `solterra-batch-translation/reference/units.csv`


---

## File: `solterra-batch-translation/SKILL.md`

---
name: "solterra-batch-translation"
description: >-
  Translate Subaru Solterra owner's-manual and automotive UI content from English into Dutch using a six-column CSV workfile. Trigger this skill whenever a CSV is supplied whose columns are, in order, English | Translation | Replacements | Terminology | Translation Memory | Notes — including rows carrying `TERMS: {...}` dictionaries or `[FUZZY nn%]` pre-fills. Also trigger when the user mentions "Solterra", "Subaru batch", "Solterra CSV", or EN→NL automotive manual translation with pre-matched terminology, even without naming the skill. Do NOT trigger for Honda diagnostic EN→NL work (HONDA_SENTINEL_V3), Dutch→English machinery content (agri-machinery-nl-en), or Afrikaans→English minutes (gsa-batch-translation).
---

Solterra Localisation: English → Dutch
=====================================

Client: Subaru Solterra (battery-electric vehicle). Content: owner's manual,
multimedia/navigation UI, safety notices, spec lines.

Operating Model
---------------

This skill is **never used alone**. It is always paired with a workfile CSV
(`output.csv` or equivalent) whose columns carry all segment-specific data.
The workfile is the primary source of truth; the bundled reference files
supply the client's standing glossary where a row's columns are empty.

**Never import Dutch terminology from the Honda work into this client.** The
two clients diverge on core vocabulary (Solterra: *batterij*,
*tractiebatterij*; Honda: *accu*). Solterra terminology comes from the
workfile columns first, then the master list (`reference/terminology.csv`),
and nowhere else. See The Master Terminology List below.

The CSV Contract
----------------

Six columns, in order. Read all six per row before translating. A context
file may accompany it — see The Context File below.

| Column | Content | Your obligation |
| --- | --- | --- |
| 1. English | Source string | Translate this, exactly as scoped |
| 2. Translation | Empty, or a `[FUZZY nn%]` pre-fill | **Your output goes here**; strip the tag |
| 3. Replacements | `TERMS: {...}` dict plus a `PATTERN: [...]` term list | Binding where the key matches the source |
| 4. Terminology | `"en" -> "nl"` pairs; same data as col 3 in display form | Binding |
| 5. Translation Memory | `en -> nl` pairs harvested from TM | Support only — adapt, never paste blindly |
| 6. Notes | Empty, or upstream fuzzy/mandatory remarks | Append your coded note (see Notes Taxonomy) |

An empty `TERMS: {}` means no terminology exists for the row: translate
fresh under this skill's style rules, check `reference/terminology.csv` for
a standing match, and mark the row `FRESH` in Notes.

`PATTERN: [Contactschakelaar] [Aan] [Indicatielampje]` is an unordered bag
of the same terms, **not a sentence skeleton**. Never build a sentence by
stringing the bracketed items together.

### Priority Hierarchy (strict)

1. **Context validity** — the translation must be correct for what the
   string *is* (UI label, caption, warning, spec line). A terminology match
   that produces nonsense in context is escalated with `HARMONISE:`, not
   applied silently.
2. **Replacements / Terminology columns and the master list** — exact
   matches are binding.
3. **Confirmed neighbouring segments** in the context file, where one is
   supplied (see below). A neighbour outranks the TM, but not the master
   list: where the list has an entry, a neighbour that differs is legacy
   drift.
4. **Translation Memory column**, then `reference/translation-memory.csv`.
5. **Patterns** — `reference/patterns.csv` and the structural patterns below.
6. **Fuzzy pre-fill / machine output** — lowest. A draft to be repaired,
   never evidence of correctness.

Where levels conflict, apply the higher level and record the conflict in
Notes with the `HARMONISE:` prefix.

The Master Terminology List
---------------------------

`reference/terminology.csv` is an unaltered copy of the user's master
list, kept on GitHub (`fdefoglio/Solterra`, `terminology.csv`): every
field quoted, CRLF line endings. The GitHub file is the master; the copy
exists only as a fallback. It holds client-
mandated terms and terms standardised locally by the user; only the user's
CAT tool shows which is which. Locally standardised terms are later
approved and mandated by the client, so treat **every entry as binding**.
It is the only terminology list for this client.

**Refresh before a batch.** If `bash_tool` has network access, fetch the
live list first, because the user adds to it between batches:

```bash
curl -sSL -o /tmp/terminology.csv https://raw.githubusercontent.com/fdefoglio/Solterra/main/terminology.csv
```

If the download succeeds and parses as two columns under an
`english,dutch` header, use it in place of the bundled copy. If it fails, use
the bundled copy and say so in one line of the reply, so the user knows newer
entries may be missing. Rows that do not parse into two columns are
skipped and listed for the user to fix on GitHub. Read the list; never
rewrite, re-quote or repair the bundled copy, so it stays identical to
GitHub.

**Matching.** Match case-insensitively on whole words, longest entry
first. A match survives inflection and an inserted article (*het
voorgaande voertuig*, *afstand tot de voorligger*); neither is a
deviation.

**Legacy TM.** Several translators have worked on this project over the
years, so confirmed segments can deviate from the list. The list decides:

* If the list has an entry and a confirmed segment in the window uses a
  different form, report it as house-term drift in the Outside-the-batch
  report, whatever the segment's status.
* If a confirmed segment matches the list, it is correct. Do not report
  the entry's wording as a defect, even where it reads unusually (*de
  zijradarsensoren vóór*); the user has already settled it.
* If an entry itself looks wrong (a meaning error, a truncated or
  malformed row), raise it as a question for the user rather than a
  defect, since it may be mandated.
* If the list has no entry and the TM or the window shows competing
  renderings, propose one standard with its evidence (TM majority, the
  pattern of related list entries, a quick web check for an OEM form) and
  say which segments would change. The user adds the agreed form to the
  list.

**Normalisation deliverable.** When the user asks to normalise segments to
the list or to an agreed standard, return a `"current","to_replace"` CSV
in a code block, one full segment string per row, so each replacement is
unambiguous in the CAT tool. Apply every rule of this skill to each
`to_replace` string, including Word Repetition: a replacement that
introduces a repeat is recast. Follow it with a short list of what changed
and why, phrased for the client note, and name any matching segments
deliberately left unchanged (for example, a term bound by a different
entry).

The Context File
----------------

The workfile is a filtered pull: only the segments needing work, order
incidental. A second file, `context_T1.csv` or equivalent, may be supplied
alongside it, rebuilding the translator's CAT view — every segment of the
language pair in **document order**, with the confirmed Dutch above and
below each batch segment. It is produced by `transit_context.py` from the
Transit `.ENU`/`.NLD` pair.

**Read it before translating any row, not as a lookup afterwards.** It is
read-only: nothing is ever written back to it, and the workfile remains the
sole delivery artefact.

| Column | Content |
| --- | --- |
| `Seg` | Transit segment number; document order |
| `Struct` | Innermost three document elements — `row/entry/p`, `note_body/note_para/title`, `att_list1_item/itemtxt` |
| `Status` | Segment status, decoded from Transit's own status field |
| `StatusCode` | Raw status code, for verifying the label |
| `Author` | Who last confirmed the segment |
| `EN` / `NL` | Source and target; `NL` is blank where the status is Not translated |
| `Batch` | Row number in the workfile, blank for context-only segments |

A `...` row with `(gap: n segments)` marks a break in the run. Rows either
side of it are **not** neighbours; never read them as consecutive.

Status values: *Translated* (confirmed, house style), *Not translated*
(the batch's own segments), *Not for translation* (markup and cross-
references copied through), *Edited, unconfirmed* (recently changed, not
yet confirmed — weaker evidence than *Translated*).

### What to take from it

* **House terms.** A confirmed neighbour outranks the TM column for
  terminology and register, because it is this document, this section.
  It does not outrank the master list: where the list has an entry, follow
  the list and report the neighbour as drift.
  Where a *full-segment* TM pair and a confirmed neighbour disagree on a
  whole string, apply the higher level but raise `HARMONISE:` rather than
  overriding silently.
* **Register and structure.** `Struct` says whether a string is a table
  cell, a list item, a heading or a footnote. Match the siblings: list
  items that are conditions stay plain present-tense statements; table
  cells stay nominal and article-free.
* **Referents.** What the previous segment left standing decides whether
  an anaphor is safe in this one — see the Word Repetition rules.
* **Revision traps.** A near-identical confirmed segment beside a batch
  segment is often the *previous revision* of the same sentence. Its Dutch
  is correct for the old English and is frequently what the fuzzy pre-fill
  was built from. Translate the delta and raise `HARMONISE:` if both
  versions now stand in the same list.
* **Stored form over earlier delivery.** Where the TM column or a fuzzy
  source shows a unit stored differently from what an earlier batch
  delivered, the reviewer has edited it since. Follow the stored form for
  sibling segments and say so under `CONSISTENCY:`.

Note the evidence in the row's Notes with the `CONTEXT:` prefix, giving the
segment numbers relied on.

### Limits

* Batch rows are matched to segments by exact English text. A row whose
  inline content was stripped during extraction — a cross-reference reduced
  to `()`, a button label to `“”` — will not match. Locate it from its
  neighbours instead, reproduce the empty placeholder exactly as column 1
  supplies it, and mark `INPUT-ERR:`.
* One workfile row may correspond to **two** Transit segments joined at a
  full stop. Say so in Notes so the delivery can be split on re-import.
* The window is counted in segment numbers, not structure, so it can cut a
  table in half. Absence of evidence in the window is not evidence of
  absence.

### Outside-the-batch report

Reading the window means reading confirmed Dutch that no one is reviewing
in this batch. Defects there ship unless someone mentions them, and noting
them costs little once the window has been read anyway. So when the window
shows any of the following, report it after the client-decision summary:

* **Meaning errors** — the Dutch says something the English does not: a
  reversed comparison or quantity (*3 or more* → *3 of minder*), the wrong
  object (*Bicycles* → *motoren*), a lost negation, a dropped clause, a
  dropped hedge (*may be displayed* → *wordt weergegeven*).
* **House-term drift** — a confirmed segment rendering a term differently
  from the master list, the workfile terminology, the TM, or its own
  neighbours (*stuurwiel*
  where the section uses *stuur*; two Dutch names for one function).
* **Defects a reviewer would correct on sight** — de/het errors, doubled or
  garbled words, a content word repeated three times.
* **Source-side faults** — the Dutch mirrors the English, but the English or
  its markup is broken: an unresolved placeholder such as `(→P.###)` where
  neighbouring segments carry a real `<xref>`, or a typo in the English that
  will reach print. These cannot be fixed on the Dutch side; report them so
  they can go to the client as a query.

Give each item one line: segment number(s), the problem, and the correct
form where it is obvious. Put meaning errors first, because they change
what the reader receives; drift and grammar follow. Untranslated segments
in the window are not reported: the user tracks them in the CAT tool, and
they reach a later workfile. If
a defect sits in an *Edited, unconfirmed* segment, say so, since the
translator may already be working on it.

The report covers what the window shows while you read it for the batch;
it is a by-product of that reading, not a separate audit, so a short list
is normal. Before omitting it, check every window segment that is not
*Not translated* against the categories above, including the user's own
*Edited, unconfirmed* segments. Those hold the user's edits since the last
delivery, and they are where drift from this batch's own decisions appears
most often: a term the batch standardised still in its old form in an
edited neighbour, or an element dropped in a rewording. If nothing
qualifies after that check, omit the section rather than writing "none".

The report is advisory. The context file stays read-only and the workfile
stays the sole delivery artefact: never edit or re-deliver a confirmed
segment on your own initiative, and never record these findings in the
Notes of workfile rows, which belong to their own segments.

A confirmed TM unit is changed only when the defect is real — a meaning
error, a lost hedge, a wrong term — never for preference; the user then
tells the client that the unit had to change. When the user accepts
reported items or asks for them to be resolved, follow the Resolution Map
below.

Head the section exactly:
**Outside the batch (the context file is read-only, so nothing was changed)**

### Resolution Map (resolving reported items)

Use this map every time the user accepts or asks to resolve reported items
(*accept*, *resolve them*, *Out: CSV block {'current','to_replace'}*), so
that each resolution has the same shape.

1. **Scope.** Take every item in the most recent Outside-the-batch report,
   plus any item the user adds. Items from earlier batches are reopened only
   when the user names them.
2. **Triage.** Sort each item into one of three kinds:
   * *Target-side defect* (meaning error, lost hedge, drift, on-sight
     defect): it gets a CSV row.
   * *Open choice the user has not settled* (for example *Als* against
     *Wanneer* across one list): apply the majority or house form, give it a
     CSV row, and say in its bullet that the majority was followed.
   * *Source-side fault* (the Dutch already mirrors the English; the fault
     is in the source or its markup, such as `(→P.###)`): no CSV row. List
     it after the bullets as a client query.
3. **Build each row.**
   * `current` is copied byte for byte from the context file's `NL`: the
     full segment, with inline tags, curly quotes and trailing spaces, so
     the CAT search finds it.
   * `to_replace` changes only the defect. Any other edit the user has made
     to that segment stays (a changed conjunction, a rewording).
   * Apply every rule of this skill to `to_replace`, including the master
     list and Word Repetition.
   * One segment per row. The same defect in several segments gets one row
     per segment.
   * Order the rows as the report ordered them: meaning errors first.
4. **Workfile rows already entered.** When a delivered workfile row is
   revised after the user has entered it in the CAT tool, give it a row too:
   `current` is the Dutch as delivered, `to_replace` the revision.
5. **Reply shape.** The reply contains these parts, in this order, and
   nothing else:
   1. the CSV in a code block: header `"current","to_replace"`, every field
      quoted;
   2. one bullet per row, or per group of rows with the same change:
      `* **5153:** what changed and why`, one or two sentences, phrased so
      it can go straight into the client note;
   3. when there are source-side faults: one short paragraph naming the
      segments and saying why no replacement is possible, framed as a
      client query.

   No verdict line, no file tag, no recap of the report.

Reading the Reference Columns Correctly
---------------------------------------

Three traps recur in this client's workfiles.

**Capitalisation artefacts.** Dictionary keys and values arrive title-cased
by the extraction script: `{'Rear': 'Achter', 'Vehicle': 'Voertuig',
'If equipped': 'Indien aanwezig'}`. The *lexical content* is binding; the
*casing* is not. Dutch running text keeps these lowercase mid-sentence —
*achter*, *voertuig*, *(indien aanwezig)*. Preserve capitals only for
genuine proper nouns and brand strings (SUBARU, SUBARU Care, ALL AUTO
(ECO), PCS, eAxle) and at sentence start.

**Single-word entries are glosses, not substitutions.** `'High': 'Hoog'`,
`'On': 'Aan'`, `'Off': 'Uit'` describe the concept, not the surface form
required in the sentence. *the possibility of a collision is high* is
*is de kans op een aanrijding groot*, not *…is hoog*. Apply the term where
it is genuinely the head word; otherwise use the idiomatic Dutch and note
`TERM-CONTEXT:`.

**Fuzzy pre-fills inherit upstream corruption.** The `[FUZZY nn%]` string in
column 2 was produced against the *similar* English sentence quoted in
Notes, sometimes after a botched term substitution. Two observed failures:

* `0.700 kg (1.54 lb.)` → pre-fill `0,720 kg` — wrong value, taken from a
  neighbouring segment. Correct: `0,700 kg` (the imperial conversion is
  dropped under the Measurement Localisation rule below, so here the
  pre-fill's omission happens to be right for the wrong reason).
* *…send an emergency call to the response center* → pre-fill
  *…een SUBARU Care-melding naar het responsecentrum te sturen* — the
  upstream source had *emergency call* overwritten by *SUBARU Care*.
  Correct: *een noodoproep naar het responscentrum te sturen*.

Procedure for every fuzzy row: diff the real English source (col 1) against
the quoted fuzzy source in Notes, translate the delta, restore anything the
pre-fill dropped **except material the Measurement Localisation rule removes**,
verify every number and unit against col 1, strip the `[FUZZY nn%]` tag, and
mark `FUZZY-REFINED`.

Style Rules (Dutch, owner's-manual register)
---------------------------------------------

* **No translationese.** The Dutch must read as if originally written by a
  native technical author. Fidelity is to meaning and function, never to the
  English word order, rhythm, or sentence boundaries — restructure freely.
  Test each string: would a Dutch manual writer, given only the meaning,
  produce this sentence? If the English shows through, rewrite.
* **Address the reader with *u***; never *je*. Instructions take the
  imperative (*Druk op…*, *Zorg ervoor dat…*, *Raadpleeg…*).
* **No future tense.** English *will* does not survive into Dutch technical
  text. Use the present for behaviour and facts: *the light will illuminate*
  → *het lampje gaat branden* / *brandt*, not *zal branden*. *Zal/zullen*
  appears only in genuine conditionals where the present would be wrong.
* **Keep the source's modality.** A hedge in the source (*may be
  displayed*, *may not operate*) tells the reader what the system does not
  guarantee; stating it as fact (*wordt weergegeven*) is a meaning error,
  not a style choice, and in safety text it overstates the system. Render
  *may* as *kan* or *mogelijk*, and do not hedge what the source states
  flatly. A doubled English hedge may collapse into one Dutch hedge:
  *operation may be possible* → *is werking mogelijk*.
* **Measurement localisation.** `reference/units.csv` is the client's own
  EN→NLD unit table and governs every measurement, number and quotation
  mark. Read it whenever a row contains a figure. The rules it encodes:
  * **Imperial is deleted, never converted.** mph, mile, lb., °F, in., ft.,
    qt., gal., psi, cu.in., lbf, ft·lbf go, whether standing alone or in a
    parenthesis beside the metric value: `0.700 kg (1.54 lb.)` → `0,700 kg`;
    `100 km/h (62 mph)` → `100 km/h`.
  * **Metric alternates are kept, and some are added.** Force `N (kgf, lbf)`
    → `N (kp)`; torque `N·m (kgf·m, ft·lbf)` → `N·m (kp·m)`; pressure
    `kPa (kgf/cm2 or bar, psi)` → `kPa (kgf/cm2 of bar)` — note *or* → *of*.
  * **Rotation takes an alternate the English lacks**: `rpm` → `rpm (min-1)`.
    Never *omw/min*, which belongs to a different client.
  * **Volume is lowercase**: `L` → `l`.
  * Keep the metric unit the source uses (`t` stays `t`); never convert
    between metric units. Where imperial is the *only* measurement given,
    convert to metric and show the conversion in the note.
  * Mark every such row `LOCALISED:`.
* **Numbers.** Decimal comma: `0.1` → `0,1`, `0.700 kg` → `0,700 kg`.
  Grouping mirrors the source's own choice: `1000` stays `1000` and `10000`
  stays `10000`, but `1,000` → `1.000` and `10,000` → `10.000`.
  `No.` → `Nr.`, `NO.` → `NR.`, preserving the source's spacing: `No.1` →
  `Nr.1`, `No. 1` → `Nr. 1`.
* **Punctuation.** Curly double quotes `“ ”` and the typographic apostrophe
  `’`; never their straight ASCII forms. No space before a colon.
* **Unit spacing**: space before the unit (`2 seconden`, `200 kPa`, `20 °C`);
  follow the Terminology/TM column where it shows a client convention.
* **Compounds close up**: *aircosysteem*, *stuurwielschakelaar*,
  *batterijpreconditionering*. Hyphenate only after an acronym, digit,
  brand, or vowel clash: *PCS-waarschuwingslampje*, *12 V-accupool*,
  *3D-kaart*, *SUBARU Care-abonnees*, *eco-airconditioningsmodus*.
* **Preserve byte-identically**: brand and system names with original casing
  (SUBARU, SUBARU Care, eAxle, ALL AUTO (ECO), PCS, RCD, POI, GPS as *gps*
  per glossary), model and part codes, footnote asterisks (`stoelverwarming*`),
  placeholders and cross-reference markers (`[*]`, `“”`), and any literal
  on-screen button or menu text carried untranslated in the TM.
* **Acronym expansions follow the TM's order.** Where TM gives
  *PCS (botswaarschuwingssysteem)*, keep that order rather than mirroring
  the English *Pre-Collision System (PCS)*.
* **de/het accuracy** is checked on delivery: *het voertuig*, *de
  schakelaar*, *het lampje*, *de accu*, *de batterij*, *het scherm*.

### Anglicisms and Calques (reject on sight)

| English | Wrong | Right |
| --- | --- | --- |
| make sure that | maak zeker dat | zorg ervoor dat |
| the system is designed to | het systeem is ontworpen om | het systeem stuurt … aan / het systeem is bedoeld om |
| will operate | zal werken | werkt / wordt aangestuurd |
| is high (probability) | is hoog | is groot |
| press and hold | druk en houd vast | houd … ingedrukt |
| if equipped | indien uitgerust | indien aanwezig |
| when the power switch is turned to ON | wanneer de contactschakelaar naar AAN wordt gedraaid | wanneer het contact wordt ingeschakeld |
| response center | responsecentrum | responscentrum |
| approximately 5 seconds | ongeveer 5 seconden (ok) — but never *circa 5 seconds* | ongeveer 5 seconden |

Also reject: English word order surviving into Dutch (verb-second and
verb-final violations), stacked prepositional strings where a compound is
idiomatic, and *deze* used where Dutch would repeat the noun.

**No *-functie* inside a bracketed qualifier.** English names a mode or
variant in brackets with *feature* or *function* (*Radar Cruise Control
(Map Integration Feature)*). In Dutch, *functie* after a technical term
and inside brackets reads heavy and clunky. Render the bracket with the
bare noun: *Cruisecontrol met radar (kaartintegratie)*, not *(kaartintegratiefunctie)*;
*kaartkoppeling* is equally acceptable. Apply the same form wherever the
feature name recurs in running text (*voorzorgsmaatregelen voor
kaartintegratie*). If a master-list entry itself contains *functie*
(*Functie voor vaart minderen in bochten*), the entry is binding: apply it
as it stands.

### Word Repetition Within a Segment

English tolerates repeating a content word inside one sentence; Dutch reads
it as clumsy, and it is corrected by hand on delivery. Remove it at source.

**Scope: within one segment only.** Repetition *across* segments is usually
correct and often mandatory — the same term must render identically
everywhere, which is what the Consistency Pass enforces. Never synonymise a
term to avoid repeating it in a neighbouring segment. Where the two pulls
conflict, consistency wins and the repetition stands.

Order of preference, strictest first:

1. **Keep one instance; eliminate the other.** Elimination beats
   synonymy every time. Try each of these against every repeated stem
   before concluding that the repetition has to stay — reaching for
   `DEDUP: retained` while an untried elimination exists is the common
   failure here:
   * gapping — of a verb (*ontgrendel eerst de portieren en daarna de
     aansluiting*), a preposition (*door een dealer, een reparateur of
     een hersteller*), or a head noun across coordinated modifiers
     (*een door SUBARU erkende of een andere betrouwbare reparateur*)
   * compounds — *laad- en ontlaadproces*, not *laadproces en
     ontlaadproces*
   * pronominal adverbs — *ervan*, *daarvan*, *daarmee*, *daarop*
   * relative subordination with *die/dat*, collapsing two clauses into one
   * zero anaphora where Dutch permits it and English does not
2. **Synonymise only if elimination fails**, and only on non-terminological
   words. A word used consistently across the project is not thereby a
   bound term: if it appears in neither `reference/terminology.csv` nor
   the row's own Terminology column, it is ordinary vocabulary and may be
   varied. Watch for synonyms that carry a regional marker or collide
   with a false friend in a neighbouring language of the review chain.
3. **Restructure the sentence** if neither works. Fidelity is to meaning,
   never to the English sentence boundary.

**Where the repetition sits matters as much as how often it occurs.** Two
instances falling close together, and especially in the closing phrase of
a sentence, read as clumsy; the same two spread across separate clauses
usually do not. Judge by weight and position, not by a word count — and
prioritise the end of the sentence, where Dutch expects the weight to
settle.

**Terminology is untouchable by default.** A term may be replaced by an
anaphor (*deze*, *dit*, *ervan*) only when all three hold:

* the antecedent is the **nearest** preceding noun phrase;
* gender and number agree (*deze schakelaar*, *dit lampje*);
* **no competing noun phrase** stands between anaphor and antecedent.

If any one fails, leave the repetition. *Deze* reaching back past another
candidate noun is a defect, not a fix. Where the repetition survives
deliberately, say so in Notes — a `DEDUP: retained` line marks it as a
decision rather than an oversight, so it is not re-examined by hand.

**Approved exception: *auto* for the reader's own vehicle.** Apply the
binding term 'Vehicle' → *voertuig* strictly: the client has confirmed it
takes precedence over the house usage *auto* found in confirmed
neighbours, so that difference on its own is not raised as `HARMONISE:`.
The one sanctioned departure is for repetition. If applying the term would
put *voertuig* (or *voertuigen*) twice in one segment, and elimination
under step 1 fails or would lose the reference point, render the
occurrence that refers to the reader's own car as *auto* (*de auto*, *uw
auto*) and keep *voertuig* for the other vehicles. This does more than
avoid a repeat: *auto* marks the reader's car against the others, the same
split the confirmed text already makes.

* *Er zijn geen naderende voertuigen in de buurt van het voertuig* →
  *Er zijn geen naderende voertuigen in de buurt van de auto*
* *(uw voertuig kan de voorligger of het voertuig naast u volgen)* →
  *(uw auto kan de voorligger of het voertuig naast u volgen)*

If *voertuig* occurs only once in the segment, keep it; the exception
resolves a repetition and is not a route back to *auto* in general. If
every occurrence refers to another vehicle, the exception does not apply
and the ordinary rules above govern. Mark the row `DEDUP:` and say that
*auto* was used for the own vehicle as the approved synonym. TM units
stored before this rule may still repeat *voertuig*; apply the exception
anyway and mark the row `TM-ADAPTED:`.

Never let deduplication alter meaning, drop a qualifier, weaken a safety
instruction, or break a UI string that must match on-screen text. **When in
doubt, no change.**

### Settled Term Decisions

These were settled with the client's reviewer. Apply them without raising
`HARMONISE:` again.

**"Lane or course" (LDA, LTA, OAA).** The English *course* has three
senses in this manual, and each needs its own Dutch:

* **Road sense** — the car deviates from, or drives on, its *lane or
  course*. The course is the road itself, whose edge the manual's footnote
  defines (asphalt against grass or soil, a curb, a guardrail). Render
  *rijstrook of weg*, adding the article the sentence needs: *van de
  rijstrook of de weg afwijken*, *op een smalle rijstrook of weg*. This is
  the standing entry `lane or course,rijstrook of weg` in
  `reference/terminology.csv`. A footnote asterisk stays on the noun it
  follows in the source: `course*` → `weg*`.
* **Recognition sense** — the system recognises or detects a *lane or
  course*. What it sees are lines and edges, so render *rijstrookmarkering
  of wegrand*, and mark the displaced entry `TERM-CONTEXT:`.
* **Heading sense** — a vehicle *changes course*. Render *van koers
  veranderen*, which is correct and idiomatic. The standing entry is keyed
  on the whole phrase *lane or course* precisely so that it does not fire
  here; never add *course* alone to the terminology.

Rejected renderings, so they are not proposed again: *koers* for the road
sense (it means heading; older LDA units in the TM still carry it, so
override them and mark the row `FUZZY-REFINED:` or `TM-ADAPTED:`);
*rijbaan* (correct but stiff); *berm* (the verge beyond the edge, where the
car ends up rather than what it deviates from); and *wegrand* with
*afwijken van* (deviating from an edge means moving away from it — *wegrand*
works only with recognition or crossing verbs).

**"Object" (*object* or *voorwerp*).** The choice follows the sense, not
the chapter:

* ***object*** — anything the vehicle's sensors or systems detect, track or
  react to: the ADAS target, the parking-assist obstacle, the thing the
  sonar measures the distance to. *Wanneer het systeem vaststelt dat een
  gedetecteerd object zich van het voertuig heeft verwijderd*.
* ***voorwerp*** — a physical item that a person handles, places, hangs or
  inserts, or that gets in the way mechanically: things hung on the
  back-door handles, a pin in the power outlet, a bicycle carrier on the
  back door, something obstructing the seat. *Hang geen voorwerpen aan de
  handgrepen van de bagageklep*.

Two borderline cases are settled. Something touching or held near the
steering wheel is *voorwerp*: the system registers contact, not a detected
target (*Wanneer een ander voorwerp dan de hand van de bestuurder het stuur
raakt*). A small item under the rear bumper that falsely triggers the
hands-free back door is *voorwerp* too, since it is an accidental
obstruction, not a detection target (*Wanneer een klein dier of voorwerp
zoals een bal onder de achterbumper beweegt*).

The phrase-level forms are in the client's terminology list, so they reach
the workfile as binding `TERMS:` entries: *detectable object* →
*detecteerbaar object*, *detected object* → *gedetecteerd object*, *target
object* → *doelobject*, *moving object* → *bewegend object*. Bare *object*
deliberately has no entry, because a single binding rendering would be wrong
for one of the two senses; decide it by the rule above and do not mark it
`TERM-CONTEXT:`. *Static object* and *stationary object* are both
*stilstaand object* (plural *stilstaande objecten*), also in the
terminology list: it is by far the most frequent form across the manual,
and the few *statisch* renderings are a stray from earlier translators. TM
units that still carry *statisch* are overridden and marked `TM-ADAPTED:`;
*statisch* in a confirmed segment is drift for the Outside-the-batch
report.

A sensor-detected thing rendered as *voorwerp*, or a handled item rendered
as *object*, in a confirmed segment is house-term drift for the
Outside-the-batch report.

### Structural Patterns

* **Cross-reference**: *For details on X, refer to the [*]* → *Voor meer
  informatie over X raadpleegt u de [*]* (or *zie de [*]* per TM).
* **Warning/consequence**: state the instruction first, consequence second;
  *possibly leading to an accident* → *wat kan leiden tot een ongeval*.
* **Conditional safety line**: *If the system determines that…* → *Als het
  systeem detecteert dat…* — *detecteren/bepalen* per TM, never *beslist*.
* **Spec line**: nominal, no invented articles or verbs; unit and number
  formatting normalised to Dutch.
* **UI label**: short and nominal; no added articles, no sentence
  punctuation.

Workflow
--------

0. **Read the context file first**, if one is supplied. Locate every batch
   segment in it, note which rows failed to match, and read the confirmed
   Dutch around each one before translating anything. Jot down anything
   that belongs in the Outside-the-batch report as you pass it, rather than
   re-reading the window for it later.
1. **Integrity check the whole file first.** Look for collapsed `""`
   escapes, unparseable `TERMS:` dicts, rows with the wrong field count, and
   truncated sources. Do not guess at mangled reference data — translate on
   the intact evidence and mark `INPUT-ERR:` with a one-line description.
   Note duplicate English sources now; they drive the Consistency Pass.
2. **Per row**: read columns 3–6 and the row's neighbourhood in the context
   file, establish what the string is, apply the Priority Hierarchy, write
   the finished Dutch into column 2.
3. **Note** every non-trivial decision using the taxonomy below. Routine
   exact-terminology application needs only `TERM-APPLIED`.
4. **Consistency Pass** over the whole file: group repeated and near-repeat
   English sources and verify identical Dutch renderings. `FRESH` rows lack
   anchors and are where drift appears. Mark any row changed
   `CONSISTENCY:`.
5. **Repetition Pass**, after the Consistency Pass so that terminology is
   already locked and visibly off-limits. Read each finished Dutch string on
   its own and flag any content word occurring twice. Function words and
   terminology are exempt from the flag. Apply the Word Repetition procedure
   above and mark the row `DEDUP:`, whether the repetition was removed or
   deliberately kept.
6. **Output**: write and verify the workfile as set out in Output Delivery
   Format below.
7. **Report** in the reply, in the order and shape set out in Output
   Delivery Format.

Notes Taxonomy (coded prefixes)
-------------------------------

| Prefix | Meaning |
| --- | --- |
| `TERM-APPLIED` | Exact terminology from cols 3/4 used as-is |
| `TERM-CONTEXT:` | Terminology present but inflected or displaced for idiom; state how |
| `TM-ADAPTED` | TM pair used but re-cast (state why) |
| `FUZZY-REFINED` | `[FUZZY nn%]` pre-fill repaired; state what was wrong |
| `LOCALISED:` | Imperial measurement dropped or converted; state which |
| `FRESH` | No terminology or TM; translated under skill rules |
| `CONSISTENCY:` | Changed in the Consistency Pass to match a sibling row |
| `CONTEXT:` | Decided on evidence from the context file; give the segment numbers |
| `DEDUP:` | Within-segment word repetition removed, or deliberately retained; state which and how |
| `HARMONISE:` | Conflict or source-side issue needing a client decision |
| `INPUT-ERR:` | Malformed reference data in this row; describe briefly |
| `SPLIT:` | Row joins two Transit segments; say where to split on re-import |

`HARMONISE:` and `INPUT-ERR:` rows must also be summarised in a short list
after the CSV, so they can be raised with the client without re-scanning the
file. Where a context file was supplied, the Outside-the-batch report (see
The Context File) follows that summary.

Output Delivery Format
----------------------

This section fixes the shape of every delivery, so the user can import the
file and act on the reply without reformatting either. Treat it as a format
contract, not a judgment call.

### The workfile

* **Name and place.** Deliver the workfile under its input filename
  (`output_T1b.csv` stays `output_T1b.csv`) in `/mnt/user-data/outputs/`,
  and present it with `present_files`. It is the only file delivered for a
  batch.
* **Byte shape.** Same encoding as the input (UTF-8; keep a BOM only if the
  input had one), CRLF line endings, the same header row, the same row
  order, six columns in every row. Write it with Python's `csv` module and
  default minimal quoting, never by hand, so commas, quotes and curly
  quotes inside fields survive.
* **Columns 1, 3, 4, 5** are carried over unchanged, character for
  character.
* **Column 2** holds the final Dutch and nothing else: no `[FUZZY nn%]`
  tag, no alternatives, no brackets of your own, no comments.
* **Column 6** keeps any upstream text first. Append ` | ` and then the
  coded notes for the row, each coded item separated by ` | `, on one
  line. Every row gets at least one coded note. Name the evidence inside
  the note (term pair, segment numbers, what the pre-fill got wrong), so
  the note stands on its own in an audit.

### Verification in code, before delivery

Run a script that re-reads both files and checks:

* row count and column count unchanged; columns 1, 3, 4, 5 identical;
* column 2 non-empty in every data row, with no `[FUZZY` left;
* no imperial units, no *zal/zullen*, no *je*;
* no decimal point between digits, no straight double quote, no space
  before a colon;
* no row with *voertuig* twice.

Print only the verdict and any flagged rows. Then print a compact review
pass — each row's English, the Dutch, and the fuzzy source quoted in
column 6 where there is one — and read it before replying. The review
pass is for you; it does not go into the reply.

### The reply

Keep it to flagged items and the file tag. The user reads the file itself,
so do not recap rows, restate translations, or narrate the process. Use
this order and these headings, and omit any section that has no items
(never write "none"):

1. **Verdict line**: `Quality gate: **PASS**` (or `**FAIL**` with the rows
   and the check that failed). Add one clause only when something about
   the run matters to the user, such as all rows located with no splits,
   or the bundled copy of the terminology used because the GitHub fetch
   failed.
2. **`**Client decisions**`**: one bullet per issue, grouping rows that
   share an issue (`* **Rows 3, 20:** …`). Covers `HARMONISE:` items
   (including doubtful list entries), proposed standards for terms not in
   the master list, `INPUT-ERR:` rows, `SPLIT:` rows, and rows that serve
   more than one segment. Each bullet says what the problem is and what
   was applied.
3. **`**Outside the batch (the context file is read-only, so nothing was
   changed)**`**: as set out under The Context File; one line per item,
   meaning errors first, with the suggested Dutch where it is obvious.
4. **File tag**: the delivered filename in backticks, as the last line.

Follow-up deliverables in the same conversation use the
`"current","to_replace"` format in a code block, followed by the short
client-note list: a normalisation set as set out under The Master
Terminology List, and resolved Outside-the-batch items by the Resolution
Map under The Context File.

Bundled Reference Files
-----------------------

Read these when a row's own columns are thin, or when checking consistency
across a batch. Workfile columns always outrank them.

| File | Contents | When to read |
| --- | --- | --- |
| `reference/terminology.csv` | Unaltered copy of the GitHub master list (about 2,000 EN→NL pairs, mandated and locally standardised; all binding) | Refresh from GitHub at the start of every batch (see The Master Terminology List); check every row and every window segment against it |
| `reference/translation-memory.csv` | Approved full-segment pairs | Sentence-level near-matches |
| `reference/patterns.csv` | Recurring phrase-level renderings | Cross-references, safety phrasing, boilerplate |
| `reference/units.csv` | Client EN→NLD unit, number and punctuation table | **Any row containing a figure, unit, `No.`, or quotation mark** |

A supplied context file is not one of these. It outranks the TM, pattern
and unit files for house terms and register, being drawn from the live
project. For terminology the master list outranks it, because the window
can carry legacy renderings from earlier translators.

Quality Gate (final check before delivery)
------------------------------------------

* ☐ Every binding terminology match applied, inflected with `TERM-CONTEXT:`, or escalated with `HARMONISE:`
* ☐ Batch and window checked against the master list (live copy if the fetch succeeded)
* ☐ No `[FUZZY nn%]` tags left in column 2
* ☐ Every fuzzy row diffed against col 1: numbers, units, parentheses, and dropped clauses restored
* ☐ No imperial units anywhere in column 2 (mph, mile, lb., °F, in., ft., qt., gal., psi, cu.in., lbf)
* ☐ Metric alternates present where `units.csv` requires them (kp, kp·m, min-1)
* ☐ Volume as `l`, rotation as `rpm (min-1)`, pressure parenthesis using *of*
* ☐ Decimal commas throughout; grouping mirrors the source; `No.` → `Nr.`
* ☐ Curly quotes `“ ”` and apostrophe `’`; no space before a colon
* ☐ No future tense; imperative used for instructions; *u* not *je*
* ☐ No anglicisms or calques from the table above
* ☐ Every source hedge (*may*, *can*) kept; nothing hedged that the source states flatly
* ☐ *Object* for sensor-detected things, *voorwerp* for handled or obstructing items, per Settled Term Decisions
* ☐ *Lane or course* rendered per Settled Term Decisions: road sense *rijstrook of weg*, recognition sense *rijstrookmarkering of wegrand*, heading sense *koers*
* ☐ No content word repeated within a segment, unless retained with a `DEDUP: retained` note
* ☐ Every anaphor used to eliminate a repetition has the nearest antecedent, agreeing gender and number, and no competing noun in between
* ☐ No translationese: every string passes the native-author test
* ☐ Compounds closed up; hyphens only after acronym, digit, brand, or vowel clash
* ☐ Brand, model, code, asterisk, and placeholder strings byte-identical to source
* ☐ de/het correct throughout
* ☐ Repeated English sources → identical Dutch
* ☐ Where a context file was supplied: every batch row located in it, house terms taken from confirmed neighbours, register matched to `Struct`, and unmatched rows marked `INPUT-ERR:`
* ☐ Workfile written and verified in code as set out in Output Delivery Format; delivered under its input filename
* ☐ Reply follows Output Delivery Format: verdict line, client decisions, outside-the-batch report, file tag; no recap
* ☐ Where the window showed meaning errors, term drift, on-sight defects or source-side faults in confirmed or edited segments (the user’s own *Edited, unconfirmed* segments included): Outside-the-batch report given, one line per item, severest first; context file untouched

---

## File: `solterra-batch-translation/transit_context.py`

```python
# -*- coding: utf-8 -*-
"""
transit_context.py - build a chronological context CSV from a Transit NXT
language pair (.ENU source + .NLD target).

Usage (Command Prompt):
    python transit_context.py A6790GEtoeuenvhch02.ENU A6790GEtoeuenvhch02.NLD
    python transit_context.py src.ENU tgt.NLD --out context_T1.csv
    python transit_context.py src.ENU tgt.NLD --batch output_T1.csv --window 15

Without --batch: every segment, document order.
With --batch:    only segments near a batch row (+/- --window), merged into
                 continuous runs, with a Batch column cross-referencing them.
"""
import argparse, csv, re, sys, xml.etree.ElementTree as ET

PUA = re.compile(r'([\ue000-\uf8ff])')
TAGNAME = re.compile(r'^<\s*/?\s*([A-Za-z_][\w.\-]*)')

# Status is a flag in the target file's Data attribute. Codes observed in the
# Solterra project; verify the labels against the colours in your own window.
STATUS = {
    ('\ue902', '\uee06'): 'Not translated',
    ('\ue902', '\uee0e'): 'Not translated',
    ('\ue90a', '\uee01'): 'Not for translation',   # markup/symbol copies
    ('\ue90a', '\uee05'): 'Translated',
    ('\ue908', '\uee05'): 'Translated (status 2)',
    ('\ue90a', '\uee0e'): 'Edited, unconfirmed',
    ('\ue90a', '\uee06'): 'Edited, unconfirmed',
}
S1 = ('\ue902', '\ue908', '\ue90a')
S2 = ('\uee01', '\uee05', '\uee06', '\uee0e')


def parse_data(data):
    """Split a Data attribute into (marker, payload) pairs."""
    parts = PUA.split(data or '')
    out, i = [], 1
    while i < len(parts):
        out.append((parts[i], parts[i + 1] if i + 1 < len(parts) else ''))
        i += 2
    return out


def read_pair(path):
    with open(path, encoding='utf-16') as f:
        return ET.fromstring(f.read())


def walk(root):
    """Yield (SegID, struct_path, text, Data) in document order."""
    body = root.find('Body')
    stack = []
    for el in body:
        if el.tag == 'Tag':
            t = el.text or ''
            m = TAGNAME.match(t)
            if not m:
                continue
            nm = m.group(1)
            if el.get('pos') == 'Begin' and not t.rstrip().endswith('/&gt;') \
                    and not t.rstrip().endswith('/>'):
                stack.append(nm)
            elif el.get('pos') == 'End' and nm in stack:
                while stack and stack.pop() != nm:
                    pass
        elif el.tag == 'Seg':
            yield (int(el.get('SegID')), '/'.join(stack[-3:]),
                   ''.join(el.itertext()), el.get('Data') or '')


def status_of(data):
    flags = {m for m, v in parse_data(data) if v == ''}
    a = next((c for c in S1 if c in flags), None)
    b = next((c for c in S2 if c in flags), None)
    label = STATUS.get((a, b), 'Unknown')
    code = '%s/%s' % (hex(ord(a)) if a else '-', hex(ord(b)) if b else '-')
    return label, code


def field(data, marker):
    for m, v in parse_data(data):
        if m == marker:
            return v
    return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source'); ap.add_argument('target')
    ap.add_argument('--out', default='context.csv')
    ap.add_argument('--batch', help='workfile CSV; column 1 = English source')
    ap.add_argument('--window', type=int, default=15)
    a = ap.parse_args()

    src = {i: (p, t) for i, p, t, d in walk(read_pair(a.source))}
    tgt = {i: (p, t, d) for i, p, t, d in walk(read_pair(a.target))}

    missing = set(src) ^ set(tgt)
    if missing:
        print('WARNING: %d segment IDs are not in both files: %s'
              % (len(missing), sorted(missing)[:10]), file=sys.stderr)

    ids = sorted(set(src) & set(tgt))

    keep, batch_no = set(ids), {}
    if a.batch:
        with open(a.batch, encoding='utf-8-sig') as f:
            rows = list(csv.reader(f))[1:]
        wanted = {r[0].strip(): n for n, r in enumerate(rows, 1) if r and r[0].strip()}
        hits = [i for i in ids if src[i][1].strip() in wanted]
        for i in hits:
            batch_no[i] = wanted[src[i][1].strip()]
        keep = set()
        for i in hits:
            lo, hi = i - a.window, i + a.window
            keep |= {j for j in ids if lo <= j <= hi}
        print('batch rows: %d | matched segments: %d | context segments: %d'
              % (len(rows), len(hits), len(keep)))
        if len(hits) < len(rows):
            unmatched = set(wanted) - {src[i][1].strip() for i in hits}
            print('UNMATCHED batch sources (%d):' % len(unmatched), file=sys.stderr)
            for u in list(unmatched)[:10]:
                print('   ', u[:70], file=sys.stderr)

    with open(a.out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, lineterminator='\r\n')
        w.writerow(['Seg', 'Struct', 'Status', 'StatusCode',
                    'Author', 'EN', 'NL', 'Batch'])
        prev = None
        for i in ids:
            if i not in keep:
                continue
            if prev is not None and i != prev + 1:
                w.writerow(['...', '', '', '', '', '(gap: %d segments)'
                            % (i - prev - 1), '', ''])
            label, code = status_of(tgt[i][2])
            nl = tgt[i][1]
            if label == 'Not translated':
                nl = ''          # target is only an untranslated copy of EN
            w.writerow([i, tgt[i][0], label, code,
                        field(tgt[i][2], '\uef09'), src[i][1], nl,
                        batch_no.get(i, '')])
            prev = i
    print('wrote', a.out)


if __name__ == '__main__':
    main()
```


---

## File: `solterra-batch-translation/reference/translation-memory.csv`

```csv
english,dutch
Rear seat heater operation,Werking van stoelverwarming achter
Engine speed and compressor operation controlled to restrict heating/cooling capacity.,Motortoerental en compressorwerking geregeld om verwarmings-/koelcapaciteit te beperken.
Electric motor speed (traction motor speed),Toerental van elektromotor (toerental van tractiemotor)
Engine speed and compressor operation controlled to restrict heating/cooling capacity.,Motortoerental en compressorwerking geregeld om verwarmings-/koelcapaciteit te beperken.
When the system determines that a passenger is in the front passenger seat,Wanneer het systeem detecteert dat er een passagier op de voorpassagiersstoel zit
"When a passenger is detected in the front passenger seat, the seat heater* and seat ventilator* will operate automatically.","Wanneer een passagier wordt gedetecteerd in de voorpassagiersstoel, worden de stoelverwarming* en stoelventilatie* automatisch aangestuurd."
```


---

## File: `solterra-batch-translation/reference/terminology.csv`

```csv
"english","dutch"
"AHB (Automatic High Beam)","AHB (automatisch grootlicht)"
"AHS (Adaptive High-beam System)","AHS (adaptief grootlicht)"
"BSM (Blind Spot Monitor)","BSM (dodehoekbewaking)"
"Hands Free Power Back Door","Handsfree elektrisch bedienbare bagageklep"
"LCA (Lane Change Assist)","LCA (rijstrookassistent)"
"LDA (Lane Departure Alert)","LDA (waarschuwing bij verlaten van rijstrook)"
"LTA (Lane Tracing Assist)","LTA (rijstrookassistent)"
"PCS (Pre-Collision System)","PCS (botswaarschuwingssysteem)"
"PDA (Proactive Driving Assist)","PDA (proactieve rijhulp)"
"PKSB (Parking Support Brake)","PKSB (remmen tijdens parkeren)"
"RCD (Rear Camera Detection)","RCD (detectie met camera achter)"
"RCTA (Rear Crossing Traffic Alert)","RCTA (waarschuwing bij achterlangs kruisend verkeer)"
"RSA (Road Sign Assist)","RSA (verkeersbordherkenning)"
"“Genuine Traction Battery Coolant”","“Genuine Traction Battery Coolant” «originele koelvloeistof voor tractiebatterij»"
"“restricted”","“beperkt”"
"“semi-universal”","“semi-universeel”"
"“SOS” button","“SOS”-knop"
"“SUBARU Super Coolant”","“SUBARU Super Coolant”"
"“SYNC” mode","“SYNC”-modus"
"“universal”","“universeel”"
"“vehicle specific”","“voertuigspecifiek”"
"12-volt battery","12V-batterij"
"12-volt battery-saving function","Spaarfunctie voor de 12V-batterij"
"12-volt battery condition","Staat van de 12V-batterij"
"12-volt battery exterior","Buitenkant van de 12V-batterij"
"12-volt battery precautions","Voorzorgsmaatregelen voor de 12V-batterij"
"2WD models","Modellen met tweewielaandrijving"
"4WD operation status","4WD-werkingsstatus"
"4WD operation status display","Weergave 4WD-werkingsstatus"
"A/C","Airco"
"A/C Auto switch operation","Automatische overschakeling van airco"
"ABS warning light","ABS-waarschuwingslampje"
"AC","AC"
"AC charging","AC-laden"
"AC charging cable","AC-laadkabel"
"AC charging cable types","Typen AC-laadkabel"
"AC charging connector lock function","Vergrendelfunctie van de AC-laadaansluiting"
"AC charging electricity","AC-laadstroom"
"AC charging inlet","AC-laadingang"
"ACC mode","ACC-modus"
"Acceleration setting","Acceleratie-instelling"
"Accelerator status","Status van het gaspedaal"
"Acoustic vehicle alerting system","Akoestisch voertuigwaarschuwingssysteem"
"Active Cornering Assist","Active Cornering Assist"
"Active steering function","Actieve stuurfunctie"
"Adaptive High-beam System","adaptief grootlicht"
"Adaptive High-beam System switch","Schakelaar voor het adaptieve grootlicht"
"adatvedelem@toyota-ce.com","adatvedelem@toyota-ce.com"
"Adding washer fluid","Ruitensproeiervloeistof bijvullen"
"Adjustable shoulder anchor","Verstelbare schoudergordelklem"
"Adjusting the mirror angle","De spiegel verstellen"
"Adjusting the seats","De stoelen afstellen"
"Adjusting the steering wheel and mirrors","Afstelling van stuur en spiegels"
"Adjustment precautions","Voorzorgsmaatregelen voor het afstellen"
"Adjustment procedure","Afstelprocedure"
"Aerosol cans","Spuitbussen"
"After changing a fuse","Na het vervangen van een zekering"
"After charging","Na het opladen"
"After charging is complete","Nadat het opladen is voltooid"
"After DC charging","Na het DC-laden"
"after reset","Na reset"
"after start","Na starten"
"AHB indicator","AHB-indicatielampje"
"AHS indicator","AHS-indicatielampje"
"Air conditioner filter","Aircofilter"
"Air conditioning","Airco"
"Air conditioning compressor","Aircocompressor"
"Air conditioning controls","Bedieningselementen voor de airco"
"Air conditioning filter","Aircofilter"
"Air conditioning refrigerant","Koudemiddel voor airconditioning"
"Air conditioning system","Aircosysteem"
"Air flow mode control switch","Schakelaar voor luchtstroommodus"
"Air flow to all the seats","Luchtstroom naar alle stoelen"
"Air flow to the front seats only","Alleen luchtstroom naar de voorstoelen"
"Air leaking from between tire and wheel","Luchtlekkage tussen de band en de velg"
"Air outlet layout and operations","Verdeling en werking van de luchtroosters"
"Air pressure gauge","Manometer"
"Air release cap","Dop voor luchtmondstuk"
"Airbag manual on-off switch","Handmatige aan/uit-schakelaar van airbag"
"Airbag manual on-off system","Systeem voor handmatig aan-/uitzetten van airbag"
"Airbag operating conditions","Voorwaarden voor activering van de airbags"
"Airbag precautions","Voorzorgsmaatregelen voor airbags"
"Airbag precautions for your child","Voorzorgsmaatregelen voor airbags bij aanwezigheid van kinderen"
"Airbag sensor assembly","Airbagsensoreenheid"
"Airbags","Airbags"
"Airflow mode control switch","Schakelaar voor luchtstroommodus"
"Airflow to all the seats","Luchtstroom naar alle stoelen"
"Airflow to the front seats only","Alleen luchtstroom naar de voorstoelen"
"Alarm","Alarm"
"Alarm-operated door lock","Portiervergrendeling door het alarm"
"Alert options","Waarschuwingsopties"
"Alert timing","Waarschuwingsmoment"
"ALL AUTO (“ECO”) control","ALL AUTO (“ECO”) regeling"
"ALL AUTO (ECO) control","ALL AUTO (ECO) regeling"
"ALL AUTO (ECO) switch","Schakelaar ALL AUTO (ECO)"
"ALL AUTO control","ALL AUTO regeling"
"Alphabetical index","Alfabetische index"
"Aluminum wheel precautions","Voorzorgsmaatregelen voor aluminium velgen"
"Aluminum wheels","Aluminium velgen"
"Ambient temperature","Omgevingstemperatuur"
"Antenna","Antenne"
"Antenna inside the luggage compartment","Antenne in de bagageruimte"
"Antenna location","Antennelocaties"
"Antenna outside the luggage compartment","Antenne buiten de bagageruimte"
"Antennas inside the cabin","Antennes in de cabine"
"Antennas outside the cabin","Antennes buiten de cabine"
"Anti-glare function","Antischitterfunctie"
"Anti-lock Brake System","Antiblokkeersysteem van de remmen"
"Appendix","Bijlage"
"Applying/releasing","Inschakelen/uitschakelen"
"Appreciable loss of power","Merkbaar vermogensverlies"
"Approach warning","Waarschuwing voor nadering"
"Approaching vehicle","Naderend voertuig"
"Approaching vehicle speed","Rijsnelheid naderend voertuig"
"Approaching vehicles","Naderende voertuigen"
"Approximate alert distance","Waarschuwingsafstand bij benadering"
"Approximate Distance","Afstand bij benadering"
"Approximate distance to obstacle","Afstand tot obstakel bij benadering"
"Area illuminated by the high beams","Gebied verlicht door het grootlicht"
"Area illuminated by the low beams","Gebied verlicht door het dimlicht"
"Armrest","Armleuning"
"Arrangements for data processing","Voorzieningen voor gegevensverwerking"
"Assist grips","Hemelhandgrepen"
"Audible symptoms","Hoorbare symptomen"
"Audio remote control switches","Afstandsbedieningsschakelaars voor het audiosysteem"
"Audio system-linked display","Weergave gekoppeld aan het audiosysteem"
"Audio system linked display","Weergave gekoppeld aan het audiosysteem"
"Audio system screen","Scherm van audiosysteem"
"Audio/video system","Audio-/videosysteem"
"Austria","Oostenrijk"
"AUTO","AUTO"
"Auto power off function","Functie voor automatische uitschakeling"
"Automatic adjustment of the mirror angle","Automatische afstelling van de hoek van de spiegels"
"Automatic air conditioning system","Automatisch aircosysteem"
"Automatic cancelation of the cruise control","Automatische uitschakeling van de cruisecontrol"
"Automatic cancelation of vehicle-to-vehicle distance control mode","Automatische uitschakeling van de modus voor regeling van de afstand tot de voorligger"
"Automatic cancellation of the speed limiter","Automatische uitschakeling van de snelheidsbegrenzer"
"Automatic car washes","Automatische wasstraten"
"Automatic check function","Functie voor automatische controle"
"Automatic door locking and unlocking system","Systeem voor automatisch vergrendelen en ontgrendelen van portieren"
"Automatic door locking and unlocking systems","Systemen voor automatisch vergrendelen en ontgrendelen van portieren"
"Automatic Emergency Calls","Automatische noodoproepen"
"Automatic headlight leveling system","Automatisch koplampnivelleringssysteem"
"Automatic headlight system","Automatisch koplampsysteem"
"Automatic High Beam","Automatic High Beam (automatisch grootlicht)"
"Automatic High Beam switch","Schakelaar voor automatisch grootlicht"
"Automatic illumination of the interior lights","Automatische verlichting van de interieurverlichting"
"Automatic light control system","Automatische verlichtingsregeling"
"automatic light off system","Automatische uitschakeling van verlichting"
"Automatic mirror folding and extending operation","Automatisch in- en uitklappen van de buitenspiegels"
"Automatic mode","Automatische modus"
"Automatic mode switch","Schakelaar voor automatische modus"
"Automatic P position selection function","Functie voor automatische selectie van de P-stand"
"Automatic Rear Flashing Hazard Lights","Automatische alarmknipperlichten achter"
"Automatic Releasing the Grip control","Automatische uitschakeling van Grip Control"
"Automatic system cancelation of emergency brake signal","Automatische uitschakeling van het noodremsignaal"
"Automatic system cancelation of hill-start assist control","Automatische uitschakeling van Hill-Start Assist Control (assistentie bij wegrijden op een helling)"
"Auxiliary battery","Hulpbatterij"
"Auxiliary box","Extra vak"
"Auxiliary box lights","Verlichting in extra vak"
"Auxiliary boxes","Extra vakken"
"Auxiliary catch lever","Motorkapgrendel"
"Available","Beschikbaar"
"Average fuel economy","Gemiddeld brandstofverbruik"
"Average power consumption","Gemiddeld energieverbruik"
"Average speed","Gemiddelde snelheid"
"Average vehicle speed","Gemiddelde rijsnelheid"
"Avoiding 12-volt battery fires or explosions","Voorkomen dat de 12V-batterij vlam vat of explodeert"
"Avoiding damage to vehicle parts","Schade aan auto-onderdelen voorkomen"
"AWD models","Modellen met vierwielaandrijving"
"AWD operation status","AWD-werkingsstatus"
"AWD operation status display","Weergave AWD-werkingsstatus"
"AWD system display","Weergave van systeem voor voorwielaandrijving"
"Back-up light","Achteruitrijlicht"
"Back-up lights","Achteruitrijlichten"
"Back door","Bagageklep"
"Back door closer","Sluitmechanisme voor bagageklep"
"Back door closing assist","Sluithulp van de bagageklep"
"Back door precautions","Voorzorgsmaatregelen voor de bagageklep"
"Back door reserve lock function","Functie voor voorbereiding op vergrendeling van bagageklep"
"Back door spindles","Aandrijfassen van de bagageklep"
"Baking soda","Baking soda (natriumwaterstofcarbonaat)"
"Basic functions","Basisfuncties"
"Battery","Batterij"
"Battery-saving function","Batterijspaarfunctie"
"Battery cooler","Batterijkoeler"
"Battery Electric Vehicle driving tips","Tips voor rijden met het batterij-elektrische voertuig"
"Battery precautions","Voorzorgsmaatregelen voor de batterij"
"Battery Preconditioning","Batterijpreconditionering"
"Battery saving function","Batterijspaarfunctie"
"Beep","piep"
"Before driving","Vóór het rijden"
"Before driving the vehicle","Voordat u met de auto gaat rijden"
"Before jacking up the vehicle","Voordat u de auto opkrikt"
"Before leaving home","Voordat u van huis gaat"
"Before leaving the vehicle","Voordat u uitstapt"
"Before recharging","Voordat u gaat opladen"
"Before repairing the vehicle","Voordat u de auto repareert"
"Before replacing fuses","Voordat u zekeringen gaat vervangen"
"Before starting the EV system","Vóór het starten van het EV-systeem"
"digital inner mirror","digitale binnenspiegel"
"Before using the LDA system","Voordat u het LDA-systeem gebruikt"
"Before using the LTA system","Voordat u het LTA-systeem gebruikt"
"Bent wheels that have been straightened","Velgen die zijn rechtgebogen na verbuiging"
"Bicycles","Fietsen"
"Bicyclists","Fietsers"
"Blank","Blanco"
"Blind Spot Monitor","dodehoekbewaking"
"Blind Spot Monitor operation","Werking van de dodehoekbewaking"
"Blown fuse","Doorgebrande zekering"
"blue","Blauw"
"Blue","Blauw"
"Bluetooth devices","Bluetooth-apparaten"
"Bolts and nuts on chassis and body","Bouten en moeren op chassis en carrosserie"
"Bottle","Fles"
"Bottle holders","Flessenhouders"
"Brake","Rem"
"Brake assist","Remhulp"
"Brake control","Remregeling"
"Brake fluid","Remvloeistof"
"Brake function","Remwerking"
"Brake Hold","Brake Hold"
"Brake hold function","Brake Hold-functie"
"Brake hold operated indicator","Indicatielampje Brake Hold ingeschakeld"
"Brake hold standby indicator","Indicatielampje Brake Hold stand-by"
"Brake hold switch","Brake Hold-schakelaar"
"Brake hold system","Brake Hold-systeem"
"Brake hold system operating conditions","Voorwaarden voor de werking van het Brake Hold-systeem"
"Brake Override System","Brake Override System"
"Brake pads and calipers","Remblokken en remklauwen"
"Brake pads and discs","Remblokken en -schijven"
"Brake parts","Onderdelen van het remsysteem"
"Brake pedal and parking brake","Rempedaal en parkeerrem"
"Brake pipes and hoses","Remleidingen en -slangen"
"Brake status","Status van de rem"
"Brake system","Remsysteem"
"Brake system warning light","Waarschuwingslampje remsysteem"
"Braking force","Remkracht"
"Break-in schedule","Inrijschema"
"Break-in tips","Tips voor inrijden"
"Break suggestion function","Functie voor pauzesuggestie"
"Breaking in your new SUBARU","Inrijden van uw nieuwe SUBARU"
"Bright","Fel"
"Brighter","Lichter"
"Brightness control","Helderheidsregeling"
"BRITAX","BRITAX"
"BSM outside rear view mirror indicators","Indicatielampjes dodehoekbewaking buitenspiegels"
"Bull bars or kangaroo bars","Bullbars"
"Bumpers","Bumpers"
"Buzzer","Zoemer"
"Buzzer volume","Zoemervolume"
"CABRIOFIX","CABRIOFIX"
"Calendar","Kalender"
"Calendar settings","Kalenderinstellingen"
"Call sending/receiving and history display","Oproep starten/aannemen en weergave van oproepgeschiedenis"
"Camera","Camera"
"Camera indicator","Indicatielampje voor de camera"
"Camera switch","Cameraschakelaar"
"Cancel switch","Schakelaar voor uitschakeling"
"Cancelation procedure","Procedure voor verwijderen"
"Capacity","Capaciteit"
"Capacity reduction of the traction battery","Afname van de capaciteit van de tractiebatterij"
"Card holders","Kaarthouders"
"Care","Verzorging"
"Cargo and luggage","Bagage en lading"
"Cargo hooks","Bagagehaken"
"Caring for leather areas","Leren oppervlakken verzorgen"
"Catch protection function","Beveiligingsfunctie tegen vastzitten"
"CAUTION","VOORZICHTIG"
"Caution after DC charging","Wees voorzichtig bij het DC-laden"
"Caution label","Waarschuwingsetiket"
"Caution symbols","Symbolen “voorzichtig”"
"Caution when charging","Wees voorzichtig bij het opladen"
"Caution while driving","Waarschuwing tijdens het rijden"
"Caution while in motion","Waarschuwing tijdens het rijden"
"Ceiling","Hemel"
"Center console","Middenconsole"
"Center console light","Verlichting van middenconsole"
"Certification","Certificering"
"Certifications","Certificeringen"
"Chains","Kettingen"
"Changing the shift position","Wijzigen van de versnellingsstand"
"Charge area","Ladingsgedeelte"
"Charge area","Laadoppervlak"
"Charging","Opladen"
"Charging-linked functions","Functies gerelateerd aan het opladen"
"Charging-related messages","Meldingen met betrekking tot opladen"
"Charging area","Laadoppervlak"
"Charging cable","Laadkabel"
"Charging cable indicator","Indicatielampje laadkabel"
"Charging components","Laadcomponenten"
"Charging connector","Laadaansluiting"
"Charging current","Laadstroom"
"Charging electricity","Laadstroom"
"Charging equipment","Laadapparatuur"
"Charging equipment and names","Laadapparatuur en benamingen"
"Charging indicator","Laadindicatielampje"
"Charging limit","Laadlimiet"
"Charging methods","Laadmethodes"
"Charging mode","Laadmodus"
"Charging port","Laadpoort"
"Charging port lid","Klep van laadpoort"
"Charging port lid open/close detection switch","Schakelaar voor de detectie van een open/gesloten klep van de laadpoort"
"Charging precautions","Voorzorgsmaatregelen voor opladen"
"Charging procedure","Laadprocedure"
"Charging rates:","Laadsnelheid:"
"Charging schedule","Laadplanning"
"Charging schedule function","Functie voor laadplanning"
"Charging station","Laadstation"
"CHARGING STATION INFORMATION","INFORMATIE OVER LAADSTATION"
"Charging system","Laadsysteem"
"Charging system error","Storing in het laadsysteem"
"Charging system warning light","Waarschuwingslampje laadsysteem"
"Charging the 12-volt battery","Opladen van de 12V-batterij"
"Charging the traction battery","Opladen van de tractiebatterij"
"Charging tips","Laadtips"
"Charging tray","Oplaadvak"
"Charging tray side","Oplaadvak"
"Checking","Controleren"
"Checking 12-volt battery fluid","De vloeistof van de 12V-batterij controleren"
"Checking and replacing fuses","Controleren en vervangen van zekeringen"
"Checking interval","Controle-interval"
"Checking the 12-volt battery","De 12V-batterij controleren"
"Checking the heater coolant","Koelvloeistof van de verwarming controleren"
"Checking the power control unit coolant","De koelvloeistof van de eenheid voor vermogensregeling controleren"
"Checking the radiator and condenser","De radiateur en condensor controleren"
"Checking tire inflation pressure","De bandenspanning controleren"
"Checking tires","Banden controleren"
"Child-protectors","Kindersloten"
"child restraint system","Kinderzitje"
"Child restraint system","Kinderzitje"
"Child restraint system fixed with a seat belt","Kinderzitje bevestigd met een veiligheidsgordel"
"Child restraint system fixed with an ISOFIX lower anchorage","Kinderzitje bevestigd met een ISOFIX-bevestiging aan de onderkant"
"Child restraint system installation","Plaatsen van kinderzitje"
"Child restraint system installation method","Bevestigingsmethode van kinderzitjes"
"Child restraint systems","Kinderzitjes"
"Child safety","Veiligheid van kinderen"
"Child seat belt usage","Gebruik van de veiligheidsgordel door kinderen"
"Child seats definition","Definitie van kinderzitjes"
"Child seats installation","Aanbrengen van kinderzitjes"
"Child seats/child restraint system installation","Plaatsen van kinderzitjes"
"Child weight","Gewicht van kind"
"Class","Klasse"
"Cleaning","Schoonmaken"
"Cleaning aluminum parts","Aluminium onderdelen schoonmaken"
"Cleaning and protecting the vehicle exterior","De buitenkant van de auto schoonmaken en beschermen"
"Cleaning and protecting the vehicle interior","Het interieur van de auto schoonmaken en beschermen"
"Cleaning detergents","Schoonmaakmiddelen"
"Cleaning fabric portions","Stoffen gedeeltes schoonmaken"
"Cleaning instructions","Schoonmaakinstructies"
"Cleaning the camera","Schoonmaken van de camera"
"Clock","Klok"
"Clock setting","Klokinstelling"
"Close & lock (walk away) function","Functie voor sluiten en vergrendelen (weglopen)"
"Closing Display","Eindscherm"
"Closing the windows","Sluiten van de ruiten"
"Cloud Navigation","Cloud Navigation"
"Coat hooks","Jashaken"
"Coins","Munten"
"Cold tire inflation pressure","Bandenspanning bij koude banden"
"Collision from the front","Frontale botsing"
"Collision from the rear","Botsing van achteren"
"Collision from the side","Botsing van opzij"
"Collision from the side at an angle","Zijdelingse botsing onder een hoek"
"Collision from the side to the vehicle body other than the passenger compartment","Botsing tegen de zijkant van de auto buiten de cabine"
"Column lock release","Ontgrendelen van stuurslot"
"Compartment","Ruimte"
"Compass display","Kompasweergave"
"Compatibility of each seating position with child restraint systems","Geschiktheid van elke stoelpositie voor kinderzitjes"
"Components","Componenten"
"Compressed air source","Bron van perslucht"
"Compressor","Compressor"
"Compressor switch","Compressorschakelaar"
"Condensation build-up on the inside of the lens","Condensaatvorming in de lens"
"Condenser","Condensor"
"Configuration","Configuratie"
"Conformity","Conformiteit"
"Console box","Consolevak"
"Console box lid","Deksel van consolevak"
"Constant speed cruising","Met constante snelheid rijden met cruisecontrol"
"Contact information","Contactgegevens"
"Content display area","Weergavegebied voor inhoud"
"Content of driving information","Inhoud van rij-informatie"
"Conventional wrench","Steeksleutel"
"Coolant","Koelvloeistof"
"Coolant selection","Keuze van koelvloeistof"
"Coolant type","Type koelvloeistof"
"Cooling fan","Koelventilator"
"Cooling system","Koelsysteem"
"Cooling system coolant","Koelvloeistof van koelsysteem"
"Coping with flat tires","Wat te doen bij een lekke band"
"Coping with overheat","Wat te doen bij oververhitting"
"Correct driving posture","Juiste rijhouding"
"Correction procedure","Correctieprocedure"
"Correction procedures","Correctieprocedures"
"Corrosion inspection","Corrosie-inspectie"
"Country","Land"
"Croatia","Kroatië"
"Cross chain","Dwarsketting"
"Crossing vehicle speed","Snelheid van kruisend voertuig"
"crossing vehicles","kruisende voertuigen"
"Cruise control","Cruisecontrol"
"Cruise control indicator","Indicatielampje cruisecontrol"
"Cruise control switch","Cruisecontrolschakelaar"
"Cruise control system","Cruisecontrolsysteem"
"Cup holders","Bekerhouders"
"Current electricity consumption","Huidig elektriciteitsverbruik"
"Current electricity consumption screen","Scherm voor huidig elektriciteitsverbruik"
"Current fuel consumption","Huidige brandstofverbruik"
"Current Power consumption","Huidig energieverbruik"
"Curtain shield airbag operating conditions","Voorwaarden voor activering van de gordijnairbags"
"Curtain shield airbag precautions","Voorzorgsmaatregelen voor gordijnairbags"
"Curtain shield airbags","Gordijnairbags"
"Curve deceleration assistance","Hulp bij het afremmen van bochten"
"Curve speed reduction","Vaart minderen in bochten"
"Curve speed reduction function","Functie voor vaart minderen in bochten"
"customer@toyota.gr","customer@toyota.gr"
"customerservice@toyota.ie","customerservice@toyota.ie"
"Customizable features","Aan te passen functies"
"Customization","Aanpassing"
"Customized setting","Aangepaste instelling"
"Customizing vehicle features","Aanpassen van voertuigfuncties"
"Cyber Attack Risk","Risico op cyberaanvallen"
"D.SNOW/MUD mode","D.SNOW/MUD-modus"
"D.SNOW/MUD mode indicator","Indicatielampje D.SNOW/MUD-modus"
"DAC","DAC"
"Dark","Donker"
"Darker","Donkerder"
"Dashboard","Dashboard"
"Data processing flow","Gegevensverwerkingsstroom"
"Data usage","Gegevensgebruik"
"datenschutz@toyota-frey.at","datenschutz@toyota-frey.at"
"Daytime running light function","Functie voor voertuigverlichting overdag"
"Daytime running light system","Systeem voor voertuigverlichting overdag"
"Daytime running lights","voertuigverlichting overdag"
"DC","DC"
"DC charging","DC-laden"
"DC charging does not start","DC-laden begint niet"
"DC charging inlet","DC-laadingang"
"DC charging power","DC-laadvermogen"
"DCM","DCM"
"Deceleration and follow-up cruising","Afremmen en cruisecontrol"
"Deceleration Assist","Afremhulp"
"Deceleration stop phase","Rem-en-stopfase"
"Deck board","Afdekplank"
"Deck under tray","Bak onder vloer van bagageruimte"
"DEEP SNOW•MUD Mode","Modus DIEPE SNEEUW/MODDER"
"Default","standaard"
"Default setting","Standaardinstelling"
"Defensive driving","Defensief rijden"
"Definition of symbols","Definitie van symbolen"
"Defogger","Ontwaseming"
"Defogging the mirrors","Ontwasemen van de spiegels"
"Defogging the rear window and outside rear view mirrors","Ontwasemen van de achterruit en buitenspiegels"
"Defogging the windshield","Ontwasemen van de voorruit"
"delegue.protectiondonnees@toyota-europe.com","delegue.protectiondonnees@toyota-europe.com"
"Description","Beschrijving"
"DESCRIPTION OF THE ECALL IN-VEHICLE SYSTEM","BESCHRIJVING VAN HET ECALL-SYSTEEM IN DE AUTO"
"Description of the operation and the functionalities of the TPS system/added value service","Beschrijving van de werking en functies van het TPS-systeem/dienst die toegevoegde waarde biedt"
"DESCRIPTION OF THE SUBARU Care IN-VEHICLE SYSTEM","BESCHRIJVING VAN HET SUBARU Care-SYSTEEM IN DE AUTO"
"Detail information for child restraint systems installation","Gedetailleerde informatie voor het bevestigen van een kinderzitje"
"Details/Actions","Details/handelingen"
"Detectable objects","Detecteerbare objecten"
"Detection areas of approaching vehicles","Detectiegebieden voor naderende voertuigen"
"Detection range","Detectiebereik"
"Detection range of the sensors","Detectiebereik van de sensoren"
"Detection sensitivity","Detectiegevoeligheid"
"Dial position","Stand van draaiknop"
"Digital audio players","Digitale audiospelers"
"digital inner mirror","digitale binnenspiegel"
"digital mirror mode","digitale spiegelmodus"
"Digital mirror mode operating condition","Voorwaarden voor de werking van de digitale spiegelmodus"
"Diluting washer fluid","Ruitensproeiervloeistof verdunnen"
"Dim/Bright","Dim/helder"
"Dimension","Afmetingen"
"Dimensions and weights","Maten en gewichten"
"Disabling the TRC system","De tractieregeling uitschakelen"
"Disc wheel","Schijfwiel"
"Discharging","Ontladen"
"Display","Display"
"Display and menu icons","Display en menupictogrammen"
"Display contents","Weergave-inhoud"
"Display Function","Weergavefunctie"
"Display items","Weergaveonderdelen"
"Display off button","Scherm uit-knop"
"Display range","Weergavebereik"
"Display settings","Weergave-instellingen"
"Displayed value","Weergegeven waarde"
"Displays the average vehicle speed since the display was reset","Geeft de gemiddelde rijsnelheid weer sinds de weergave is gereset"
"Displays the distance driven since EV system start","Geeft de gereden afstand weer sinds het EV-systeem is gestart"
"Displays the distance driven since the display was reset","Geeft de gereden afstand weer sinds de weergave is gereset"
"Displays the elapsed time since EV system start","Geeft de verstreken tijd weer sinds het EV-systeem is gestart"
"Displays the elapsed time since the display was reset","Geeft de verstreken tijd weer sinds de weergave is gereset"
"Displays the vehicle speed","Geeft de rijsnelheid weer"
"Displays warning messages if a malfunction occurs","Geeft een waarschuwing als een storing optreedt"
"Distance","Afstand"
"Distance until next engine oil change","Afstand tot volgende motorolieverversing"
"Distilled water","Gedestilleerd water"
"Do-it-yourself maintenance","Doe-het-zelf-onderhoud"
"Do-it-yourself service precautions","Voorzorgsmaatregelen voor doe-het-zelf-onderhoud"
"Door lock","Portiervergrendeling"
"Door lock linked window operation","Aan portiervergrendeling gekoppelde werking van de ruiten"
"door lock switch","schakelaar voor portiervergrendeling"
"door lock switches","schakelaars voor portiervergrendeling"
"Door trim ornament lights","Verlichting van sierbekleding van portier"
"Doors","portieren"
"Double locking system","Dubbel vergrendelingssysteem"
"Double locking system precaution","Voorzorgsmaatregel voor het dubbelevergrendelingssysteem"
"Downhill assist control system indicator","Indicatielampje Downhill Assist Control-systeem"
"dpcp@toyota.hr","dpcp@toyota.hr"
"dpcp@toyota.si","dpcp@toyota.si"
"Drawbar load","Belasting van de trekbalk"
"DRCC","DRCC"
"Drive-Start Control","regeling voor starten van aandrijving"
"Drive Connect","Drive Connect"
"Drive distance","Gereden afstand"
"Drive Info","Rij-informatie"
"Drive Info Items","Items van rij-informatie"
"Drive Info Type","Type rij-informatie"
"Drive information","Rij-informatie"
"Drive information items","Rij-informatieonderdelen"
"Drive information type","Rij-informatietype"
"Drive mode cancellation","Rijmodus uitschakelen"
"Drive mode select switch","Schakelaar voor rijmodusselectie"
"Drive mode select switch Operation","Bediening van schakelaar voor rijmodusselectie"
"Drive shaft boots","Aandrijfashoezen"
"Driver","Bestuurder"
"Driver airbag","Airbag bestuurder"
"Driver and front passenger","Bestuur en voorpassagier"
"Driver break suggestion","Pauzesuggestie voor bestuurder"
"Driver distraction","Afleiding van de bestuurder"
"Driver monitor","Bestuurderscamera"
"Driver monitor camera","Bestuurderscamera"
"Driver Monitor support function","Ondersteuningsfunctie van bestuurderscamera"
"Driver’s and front passenger’s seat belt reminder light","Herinneringslampje veiligheidsgordel bestuurder en voorpassagier"
"Driver’s and front passenger’s seat belt warning buzzer","Waarschuwingszoemer veiligheidsgordel bestuurder en voorpassagier"
"Driver’s door","Bestuurdersportier"
"Driver’s door linked door unlocking function","Aan bestuurdersportier gekoppelde functie voor portierontgrendeling"
"Driver’s seat position memory","Bestuurdersstoelpositiegeheugen"
"Driving assist information","Rijhulpinformatie"
"Driving assist information indicator","Indicatielampje rijhulpinformatie"
"Driving assist mode select switch","Keuzeschakelaar rijhulpmodus"
"Driving assist switch","Rijhulpschakelaar"
"Driving assist systems","Rijhulpsystemen"
"Driving in the rain","Rijden in de regen"
"Driving information display","Weergave van rij-informatie"
"Driving mode select switch","Keuzeschakelaar rijmodus"
"Driving on rough roads","Rijden op slecht wegdek"
"Driving position","Rijpositie"
"Driving position memory","Rijpositiegeheugen"
"Driving position memory switches","Schakelaars voor rijpositiegeheugen"
"Driving position recall","Oproepen van rijpositie"
"Driving position registration","Opslaan van rijpositie"
"Driving procedure","Rijprocedure"
"Driving procedures","Rijprocedures"
"Driving range","Actieradius"
"Driving support system information","Informatie over rijhulpsystemen"
"Driving support system information display","Weergave van informatie over rijhulpsystemen"
"Driving support system status display area","Weergavegebied voor de status van rijhulpsystemen"
"Driving the vehicle","Rijden met de auto"
"Driving tips","Rijtips"
"Driving to spread the liquid sealant evenly","Rijden om het vloeibare afdichtmiddel gelijkmatig te verdelen"
"Driving with snow tires","Rijden met winterbanden"
"Driving with tire chains","Rijden met sneeuwkettingen"
"During customization","Tijdens het aanpassen van instellingen"
"During setting up the display","Tijdens het instellen van het display"
"Dusty road driving","Stoffige wegen"
"Dynamic radar cruise control","Dynamische cruisecontrol met radar"
"Dynamic radar cruise control indicator","Indicatielampje dynamische cruisecontrol met radar"
"Dynamic radar cruise control system warning messages and buzzers","Waarschuwingsmeldingen en -zoemers van de dynamische cruisecontrol met radar"
"dynamic radar cruise control with full-speed range","Dynamische cruisecontrol met radar voor het volledige snelheidsbereik"
"Dynamic Radar Cruise Control with Road Sign Assist","Dynamische cruisecontrol met radar en verkeersbordherkenning"
"e-Transaxle fluid","e-Transaxle-vloeistof"
"e-Transaxle Fluid TE","e-Transaxle Fluid TE"
"Earlier","eerdere"
"Early","vroeg"
"ECB operating sound","Werkingsgeluid van ECB"
"Eco air conditioning mode","Eco-airconditioningsmodus"
"Eco drive mode","Eco-rijmodus"
"Eco drive mode indicator","Indicatielampje eco-rijmodus"
"Eco mode","Eco-modus"
"EDSS","EDSS"
"Effective range","Effectief bereik"
"Elapsed time","Verstreken tijd"
"Electric cooling fan","Elektrische koelventilator"
"electric motor","Elektromotor"
"Electric motor speed","Toerental van elektromotor"
"Electric power steering","Elektrische stuurbekrachtiging"
"Electric Power Steering system","elektrische stuurbekrachtiging"
"Electric power steering system warning light","Waarschuwingslampje elektrische stuurbekrachtiging"
"Electric Vehicle system","Elektrisch-voertuigsysteem"
"Electric Vehicle system features","Kenmerken van het elektrisch-voertuigsysteem"
"Electric Vehicle system precautions","Voorzorgsmaatregelen voor het elektrisch-voertuigsysteem"
"Electrical leakage detection function","Functie voor lekstroomdetectie"
"Electrical system","Elektrisch systeem"
"Electricity consumption","Elektriciteitsverbruik"
"Electricity Supply Unit","Elektrischevoedingseenheid"
"Electromagnetic waves","Elektromagnetische golven"
"Electronic key","Elektronische sleutel"
"Electronic key battery","Batterij van de elektronische sleutel"
"Electronic key battery depletion","Leegraken van de batterij van de elektronische sleutel"
"Electronic sunshade","Elektronisch zonnescherm"
"Electronic sunshade switch","Schakelaar voor elektronisch zonnescherm"
"Electronically Controlled Brake System","elektronisch geregeld remsysteem"
"Emergency assistance","Noodhulp"
"Emergency brake signal","Noodremsignaal"
"Emergency Driving Stop System","Nooduitschakeling aandrijving"
"Emergency flasher switch","Schakelaar voor alarmknipperlichten"
"Emergency flashers","Alarmknipperlichten"
"Emergency flashers switch","Schakelaar voor alarmknipperlichten"
"Emergency locking retractor","Oprolmechanisme met noodvergrendeling"
"Emergency measures regarding electrolyte","Noodmaatregelen met betrekking tot elektrolyt"
"Emergency Notification Services","Noodmeldingsdiensten"
"Emergency release lever","Hendel voor noodontgrendeling"
"Emergency repair procedure","Procedure voor noodreparaties"
"Emergency shut off system","Systeem voor nooduitschakeling"
"Emergency start function","Noodstartfunctie"
"Emergency steering assist","Noodstuurassistentie"
"Emergency stop of the EV system","Noodstop van het EV-systeem"
"emergency tire puncture repair kit","Noodreparatieset voor een lekke band"
"Emergency tire puncture repair kit components","Onderdelen van de noodreparatieset voor een lekke band"
"Emergency towing","Slepen in noodsituaties"
"Emergency towing procedure","Procedure voor slepen in noodsituaties"
"EN 62196-2","EN 62196-2"
"EN 62196-3","EN 62196-3"
"Enabling the system","Het systeem inschakelen"
"Enabling/disabling the Parking Support Brake","In-/uitschakelen van het remmen tijdens parkeren"
"End of prohibition","Einde van verboden"
"Engine coolant temperature gauge","Temperatuurmeter motorkoelvloeistof"
"English","Engels"
"Enter/Set","Enter/instellen"
"Entry functions","Toegangsfuncties"
"EPS operation sound","Geluid van werking van EPS (elektrische stuurbekrachtiging)"
"Error warning indicator","Waarschuwingslampje voor foutmelding"
"Essential information","Essentiële informatie"
"Estonia","Estland"
"ESU","ESU"
"EV system","EV-systeem"
"EV system does not start after DC charging","EV-systeem start niet na het DC-laden"
"EV system output","Vermogen van EV-systeem"
"EV system output restriction control","Regeling voor vermogensbeperking van EV-systeem"
"EV system overheating","Oververhitting van het EV-systeem"
"Event data recorder","gebeurtenisdatarecorder"
"Example","Voorbeeld"
"Example of the displayed regulation number","Voorbeeld van het weergegeven richtlijnnummer"
"Examples of function operation","Voorbeelden van activering van de functie"
"Examples of system operation","Voorbeelden van activering van het systeem"
"Excess speed notification function","Waarschuwingsfunctie voor overschrijden van snelheidslimiet"
"Excess speed notification level","Snelheid waarmee de snelheidslimiet wordt overschreden waarbij wordt gewaarschuwd"
"Excess speed notification method","Waarschuwingsmethode voor overschrijding van snelheidslimiet"
"Excessive tire squeal when cornering","Overmatig bandengeluid in bochten"
"Excessive wear","Overmatige slijtage"
"exhaust fumes","uitlaatrook"
"Exit ramp on left","Afrit links"
"Exit ramp on right","Afrit rechts"
"Explains symbols used in this manual","Verklaart symbolen die worden gebruikt in deze handleiding"
"Expressway","Autoweg"
"Expressway exit","Eind autoweg"
"Extended Headlight Lighting system","Follow-me-home-verlichting"
"Extended Resume Time","Verlengde hervattingstijd"
"Exterior","Buitenkant"
"External power source","Externe voedingsbron"
"Face Authentication","Gezichtsauthenticatie"
"Face identification","Gezichtsherkenning"
"Fall-down protection function","Beveiligingsfunctie tegen vallen"
"Fan speed control switch","Schakelaar voor ventilatortoerental"
"Fast","Snel"
"Fastening and releasing the seat belt","Vastmaken en losmaken van de veiligheidsgordel"
"Favorite settings","Favoriete instellingen"
"FCTA system control","FCTA-systeemcontrole"
"Features","Kenmerken"
"FHL","FHL"
"Fine adjustment","Fijnafstelling"
"Finland","Finland"
"Fitting tire chains","Sneeuwkettingen aanbrengen"
"Fixation","Bevestiging"
"Fixed with a seat belt","bevestigd met een veiligheidsgordel"
"Fixed with an ISOFIX lower anchorage","Bevestigd met een ISOFIX-bevestiging aan de onderkant"
"Fixing the top strap to the top tether anchorage","Bevestigen van de bovenste band aan het “top tether”-bevestigingspunt"
"Fixture","Bevestiging"
"flags","vlaggen"
"Flashes normally","Knippert normaal"
"Flashes rapidly","Knippert snel"
"Flat tire","Lekke band"
"Flathead screwdriver","Platte schroevendraaier"
"Fluid","Vloeistof"
"Fluid capacity","Vloeistofcapaciteit"
"Fluid type","Vloeistoftype"
"Fog light switch","Schakelaar voor mistlichten"
"Fog lights","Mistlichten"
"Fog lights can be used when","Mistlichten kunnen gebruikt worden wanneer"
"Folding and extending the mirrors","In- en uitklappen van de spiegels"
"Folding down the rear seatbacks","Neerklappen van de rugleuningen van de achterstoelen"
"Folding the mirrors","Inklappen van de spiegels"
"Footwell lights","Voetlichten"
"for driver’s side","aan bestuurderszijde"
"For safe driving","Om veilig te rijden"
"For safe use","Voor veilig gebruik"
"For safety and security","Veiligheid en beveiliging"
"for terminal clamp bolts","voor klembouten van aansluitingen"
"For vehicles with navigation system","Voor auto’s met navigatiesysteem"
"For your information","Ter informatie"
"For your safety","Voor uw veiligheid"
"Foreign substance detection:","Detectie van vreemd voorwerp:"
"France","Frankrijk"
"Free play","Vrije slag"
"Free/Open Source Software Information","Informatie over vrije/open source-software"
"Front","Vóór"
"front bumper","Voorbumper"
"Front bumper","Voorbumper"
"Front camera","Camera aan de voorkant van de auto"
"Front camera detection","Detectie door de camera aan de voorkant van de auto"
"Front camera installation area on the windshield","Installatiegebied van de camera aan de voorkant van de auto op de voorruit"
"Front center sensor","Sensor vóór in het midden"
"Front center sensor detection","Detectie van sensoren middenvoor"
"Front center sensors","Sensoren middenvoor"
"Front corner sensor detection","Detectie van sensoren voorhoeken"
"Front corner sensors","Sensoren voorhoeken"
"Front crossing traffic alert","waarschuwing bij voorlangs kruisend verkeer"
"Front door panels","Voordeurpanelen"
"Front door speakers","Luidsprekers voorportier"
"Front door trim","Voordeurbekleding"
"Front eAxle","eAxle vóór"
"Front eAxle fluid type","Vloeistoftype voor eAxle vóór"
"Front electric motor","Elektromotor vóór"
"front fender","Voorspatbord"
"Front fender","Voorspatbord"
"Front fog light indicator","Indicatielampje mistkoplampen"
"Front fog lights","Mistkoplampen"
"Front impact sensors","Botssensoren vóór"
"Front interior lights","Interieurverlichting vóór"
"Front passenger airbag","Airbag voor voorpassagier"
"Front pillars","Voorstijlen"
"Front position lights","Parkeerlichten vóór"
"Front radar sensor","Radarsensor vóór"
"Front right-hand","Rechtsvoor"
"Front Seat Center AirBag","Airbag midden tussen de voorstoelen"
"Front Seat Center AirBag operating conditions","Voorwaarden voor activering van de airbag midden tussen de voorstoelen"
"Front seat concentrated airflow mode (S-FLOW)","Modus voor geconcentreerde luchtstroom voor de voorstoelen (S-FLOW)"
"Front seat concentrated airflow mode (S-FLOW) switch","Schakelaar voor modus voor geconcentreerde luchtstroom voor de voorstoelen (S-FLOW)"
"Front seats","Voorstoelen"
"Front side radar sensors","Zijradarsensoren vóór"
"Front side sensors","Zijsensoren vóór"
"Front turn signal lights","Richtingaanwijzers vóór"
"Fuel economy","Brandstofverbruik"
"Fuel Economy","Brandstofverbruik"
"Fuel gauge","Brandstofmeter"
"Full","Vol"
"Full-height, forward-facing child restraint systems","Naar voren gerichte kinderzitjes met volledige hoogte"
"Full-size, rearward-facing child restraint systems","Naar achteren gerichte kinderzitjes van volledig formaat"
"Full luggage loading","Bagageruimte vol"
"Function","Functie"
"Funnel","Trechter"
"Fuse box","Zekeringenkastje"
"Fuse with same amperage rating as original","Zekering met dezelfde nominale ampèrage als de originele"
"Fuses","Zekeringen"
"Gauges","Meters"
"Gauges and meters","Tellers en meters"
"Gauges, meters and multi-information display","Tellers, meters en het multi-informatiedisplay"
"General airbag precautions","Algemene voorzorgsmaatregelen voor airbags"
"General precaution regarding children’s safety","Algemene voorzorgsmaatregelen voor de veiligheid van kinderen"
"General precautions while driving","Algemene voorzorgsmaatregelen tijdens het rijden"
"GENUINE SUPER LONG LIFE COOLANT (PINK)","GENUINE SUPER LONG LIFE COOLANT (PINK) «ORIGINELE KOELVLOEISTOF MET SUPER LANGE LEVENSDUUR (ROZE)»"
"Germany","Duitsland"
"gestaodadospessoais@toyotacaetano.pt","gestaodadospessoais@toyotacaetano.pt"
"Global Warming Potential","aardopwarmingsvermogen"
"Gratings and gutters","Roosters en goten"
"Gravel roads","Grindwegen"
"Gray","Grijs"
"Grease","Smeervet"
"Great Britain","Groot-Brittannië"
"Greece","Griekenland"
"Green","Groen"
"Grey","Grijs"
"Grip control","Grip Control"
"Grip control indicator","Indicatielampje Grip Control"
"Grip control Operations","Werking van Grip Control"
"Grip control Operations Conditions","Voorwaarden voor gebruik van Grip Control"
"Grip control set speed indicator","Indicatielampje ingestelde snelheid van Grip Control"
"Grip control switch","Grip Control-schakelaar"
"Gross Vehicle Mass","Brutovoertuiggewicht"
"Grounding","Aarding"
"Grounding precautions","Voorzorgsmaatregelen voor aarding"
"guardrail","vangrail"
"Guest","Gast"
"Guidance","Advies"
"Guide line","Geleidingslijn"
"Guide line display mode","Displaymodus van de geleidingslijnen"
"Guide message","Geleidingsmelding"
"Guide pin","Geleidepen"
"Guide to dial settings","Richtlijnen voor instelling van de draaiknop"
"Hand warmers made of metal","Metalen handwarmers"
"Handling method","Methode om hiermee om te gaan"
"Handling of the 12-volt battery","Hanteren van de 12V-batterij"
"Handling of tires and the suspension","Hanteren van banden en de ophanging"
"Handling the child restraint system","Hanteren van het kinderzitje"
"Handling the seat belts","Hanteren van de veiligheidsgordels"
"Hands off steering wheel warning","Waarschuwing handen van stuur"
"Hands off steering wheel warning operation","Werking van waarschuwing handen van stuur"
"Head-up display","Head-up-display"
"Head restraint","Hoofdsteun"
"Head restraint precautions","Voorzorgsmaatregelen voor hoofdsteun"
"Head restraints","Hoofdsteunen"
"heading-up display","head-up-display"
"Headlight cleaners","Koplampreinigers"
"Headlight control sensor","Sensor voor koplampregeling"
"Headlight high beam indicator","Indicatielampje grootlicht"
"Headlight leveling dial","Draaiknop voor koplampnivellering"
"Headlight switch","Schakelaar voor koplampen"
"Headlights","Koplampen"
"Hearing the RCTA buzzer","Hoorbaarheid van de RCTA-zoemer"
"Heated steering wheel","Stuurverwarming"
"Heater coolant","Koelvloeistof van de verwarming"
"Heater coolant level","Koelvloeistofniveau voor de verwarming"
"Heater coolant reservoir","Koelvloeistofreservoir voor de verwarming"
"Heater system","Verwarmingssysteem"
"Heaters","Verwarmingen"
"High-voltage precautions","Voorzorgsmaatregelen voor hoogspanning"
"High pressure car washes","Hogedrukwasstraten"
"High speed operation","Hoge snelheid"
"High voltage cables","Hoogspanningskabels"
"Hill-start assist control","Hill-Start Assist Control (assistentie bij wegrijden op een helling)"
"Hill-start assist control does not operate effectively when","Wanneer Hill-Start Assist Control (assistentie bij wegrijden op een helling) niet effectief werkt"
"Hold-down clamp","Bevestigingsklem"
"hood","motorkap"
"hood lock release lever","hendel voor ontgrendeling van motorkap"
"Hook","Haak"
"Hooks","Haken"
"Horn","Claxon"
"Hose","Slang"
"Hour","Uur"
"How to change between wheel sets","Wisselen tussen wielsets"
"How to change the unit","Veranderen van de meeteenheid"
"How to charge your vehicle","Het opladen van uw auto"
"How to registration ID code","Id-codes registreren"
"How to search","Zoeken"
"How to set the DC charging power","Het instellen van de DC-laadstroom"
"How to use AC charging","Hoe AC-laden werkt"
"How to use DC charging","Hoe DC-laden werkt"
"How to wear your seat belt","Het dragen van een veiligheidsgordel"
"How your child should wear the seat belt","Het dragen van een veiligheidsgordel door uw kind"
"Hybrid System Indicator","Indicatielampje hybride systeem"
"Hybrid system overheat","Oververhitting van het hybride systeem"
"i-Size seating position","Stoelpositie voor i-Size"
"Ice","Gladheid"
"Iceland","IJsland"
"Icon","Pictogram"
"Icon display area","Gebied voor weergave van pictogrammen"
"Icons","Pictogrammen"
"Identification","Identificatie"
"identification label","Identificatie-etiket"
"Identification label","Identificatie-etiket"
"Identification number","Identificatienummer"
"If a warning light turns on or a warning buzzer sounds","Als een waarschuwingslampje gaat branden of een waarschuwingszoemer klinkt"
"If a warning message is displayed","Als een waarschuwingsmelding wordt weergegeven"
"If equipped","Indien aanwezig"
"If the 12-volt battery is discharged","Als 12V-batterij is ontladen"
"If the electronic key does not operate properly","Als de elektronische sleutel niet naar behoren werkt"
"If the vehicle becomes stuck","Als de auto vast komt te zitten"
"If you have a flat tire","Als uw auto een lekke band heeft"
"If you lose your keys","Bij verlies van uw sleutels"
"If you notice any symptoms","Als u symptomen opmerkt"
"If you think something is wrong","Als u denkt dat er iets mis is"
"If your vehicle becomes stuck","Als uw auto vast komt te zitten"
"If your vehicle has to be stopped in an emergency","Als uw auto moet worden gestopt bij een noodsituatie"
"If your vehicle needs to be towed","Als uw auto moet worden gesleept"
"If your vehicle overheats","Als uw auto oververhit raakt"
"Ignition switch","Contactschakelaar"
"Illuminated entry system","Systeem voor instapverlichting"
"Illumination","Verlichting"
"Illustration Number","Afbeeldingsnummer"
"Images from the cameras","Beelden van de camera’s"
"Immobilizer system","Startonderbrekersysteem"
"Impact detection door lock release system","Portierontgrendelsysteem bij botsdetectie"
"Implementing Regulation","Implementatie van richtlijn"
"Implementing Regulation Annex1 PART3 User Information","Implementatie van Richtlijn Annex1 DEEL3 Gebruikersinformatie"
"Important points of the wireless charger","Belangrijke opmerkingen voor de draadloze lader"
"Important points regarding stability","Belangrijke punten met betrekking tot stabiliteit"
"Important points regarding trailer loads","Belangrijke punten met betrekking tot lading van een aanhanger"
"Important points regarding turning","Belangrijke punten met betrekking tot bochten nemen"
"Important points while driving","Belangrijke punten tijdens het rijden"
"Importer Information","Informatie over importeur"
"Inappropriate pedal operation warning light","Waarschuwingslampje onjuiste pedaalbediening"
"Increase Speed","Snelheid verhogen"
"Increasing vehicle-to-vehicle distance","De afstand tussen voertuigen vergroten"
"Index","Index"
"Indication to prevent misplacement in the rear seat","Indicatie om onjuiste positionering in de achterstoel te voorkomen"
"Indicator","Indicatielampje"
"Indicator lights","Indicatielampjes"
"Indicator operation","Werking van indicatielampjes"
"Indicators","Indicatielampjes"
"Induction cookers","Inductiekookplaten"
"Inflation pressure","Bandenspanning"
"info@toyota.ch","info@toyota.ch"
"INFORMATION ON DATA PROCESSING","INFORMATIE OVER GEGEVENSVERWERKING"
"INFORMATION ON THIRD PARTY SERVICES AND OTHER ADDED VALUE SERVICES (IF FITTED)","INFORMATIE OVER DIENSTEN VAN DERDEN EN ANDERE DIENSTEN DIE TOEGEVOEGDE WAARDE BIEDEN (INDIEN AANWEZIG)"
"Information on what to do in case of a flat tire","Informatie over wat u moet doen bij een lekke band"
"Information symbols","Informatiesymbolen"
"Information tag","Informatielabel"
"Initialization","Initialisatie"
"Initializing","Initialiseren"
"Inside door handle lights","Verlichting in binnenhandgrepen van de portieren"
"Inside lock buttons","Vergrendelknoppen aan de binnenkant"
"Inside rear view mirror","Binnenspiegel"
"Inspect","Inspecteren"
"Installation method","Bevestigingsmethode"
"Installation of an RF-transmitter system","Aanbrengen van een RF zendsysteem"
"Installation with ISOFIX lower anchorage","Aanbrengen met ISOFIX-bevestigingen aan de onderkant"
"Installing child restraint system using a seat belt","Aanbrengen van een kinderzitje bevestigd met een veiligheidsgordel"
"Installing child restraints","Aanbrengen van kinderzitjes"
"Installing floor mats","Vloermatten aanbrengen"
"Installing the head restraints","Aanbrengen van de hoofdsteunen"
"Installing the tire","Aanbrengen van het wiel"
"Installing tire pressure warning valves and transmitters","Ventielen en zenders voor waarschuwing voor de bandenspanning aanbrengen"
"Installing towing eyelets to the vehicle","Sleepogen aanbrengen op de auto"
"Instructions for checking tire inflation pressure","Instructies voor het controleren van de bandenspanning"
"Instructions for manual activation of the system","Instructies voor handmatige activering van het systeem"
"Instrument cluster","Instrumentenpaneel"
"Instrument panel","Instrumentenpaneel"
"Instrument panel light control","Regeling van de verlichting van het instrumentenpaneel"
"Instrument panel light control switches","Schakelaars voor de verlichting van het instrumentenpaneel"
"Intelligent Assistant","Intelligent Assistant"
"Interior","Interieur"
"Interior features","Interieurkenmerken"
"Interior light","Interieurverlichting"
"Interior lights","Interieurverlichting"
"Interior lights list","Lijst van interieurverlichting"
"Intermediate","gemiddeld"
"Intersection collision avoidance support","Hulp bij het voorkomen van botsingen op kruispunten"
"Intrusion sensor","Inbraaksensor"
"Intrusion sensor and tilt sensor","Inbraaksensor en kantelsensor"
"Intrusion sensor and tilt sensor cancel switch","Schakelaar voor uitschakeling van inbraaksensor en kantelsensor"
"Intrusion sensor cancel switch","Schakelaar voor uitschakeling van inbraaksensor"
"Intrusion sensor detection considerations","Aandachtspunten voor detectie door de inbraaksensor"
"Inverter","omvormer"
"IP67","IP67"
"Ireland","Ierland"
"ISO fixture","ISO-bevestiging"
"ISOFIX child restraint system","ISOFIX-kinderzitje"
"ISOFIX lower anchorage","ISOFIX-bevestiging aan de onderkant"
"ISOFIX lower anchorage attachment","Bevestiging van onderste ISOFIX-punten"
"ISOFIX lower anchorages","ISOFIX-bevestigingen aan de onderkant"
"Italy","Italië"
"Item","Item"
"Items to check before locking the vehicle","Punten die moeten worden gecontroleerd voordat u de auto vergrendelt"
"Items to initialize","Items die moeten worden geïnitialiseerd"
"Items to prepare","Wat u moet klaarleggen"
"Jack","Krik"
"Jack handle","Krikhandgreep"
"Jam protection function","Beveiligingsfunctie tegen beknelling"
"JSS MAXI PLUS","JSS MAXI PLUS"
"Junior seat","Peuterzitje"
"Key information","Informatie over sleutels"
"Key linked functions","Aan de sleutel gekoppelde functies"
"Key number plate","Sleutelnummerplaatje"
"Keyless entry","Keyless Entry"
"Keys","Sleutels"
"Kick in buzzer","Kick-in zoemer"
"Kick Sensor","Trapsensor"
"KIDFIX 2S","KIDFIX 2S"
"KIDFIX i-SIZE","KIDFIX i-SIZE"
"klient@toyota.pl","klient@toyota.pl"
"L1","L1"
"L2","L2"
"Landing hard or falling","Hard landen of vallen"
"Lane Change Assist","rijstrookassistent"
"Lane Departure Alert","Waarschuwing bij verlaten van rijstrook"
"Lane departure alert function","Functie voor waarschuwing bij verlaten van rijstrook"
"Lane Departure Alert system","Functie voor waarschuwing bij verlaten van rijstrook"
"Lane departure prevention function","Functie voor voorkomen van verlaten van rijstrook"
"Lane display","Rijstrookweergave"
"Lane Tracing Assist","rijstrookassistent"
"Language","Taal"
"Large adjustment","Grote aanpassing"
"Late","Laat"
"Later","Later"
"LCA display","LCA-display"
"LDA indicator","Indicatielampje LDA"
"LDA OFF indicator","Indicatielampje LDA UIT"
"LED lights","Ledverlichting"
"LED Lights","Ledverlichting"
"Left-hand drive vehicles","Auto’s met stuur links"
"Left-hand side temperature control switch","Schakelaar voor temperatuurregeling links"
"Left lateral-facing infant seat","Naar links gericht babyzitje"
"Left side instrument panel","Instrumentenpaneel links"
"Left turn","Links afslaan"
"Lever","Hendel"
"License plate lights","Kentekenverlichting"
"Lid lifter","Kleplichter"
"Light bulbs","Lampjes"
"Light bulbs of the exterior lights for driving","Lampjes van rijverlichting"
"Light reminder buzzer","Zoemer ter herinnering aan verlichting"
"Light sensor sensitivity","Gevoeligheid van de lichtsensor"
"Light switch","Verlichtingsschakelaar"
"Light switches","Verlichtingsschakelaars"
"Lighting conditions of operation indicator light","Status van indicatielampje voor werking"
"Likely cause","Waarschijnlijke oorzaak"
"Linked mirror function when reversing","Functie gekoppelde spiegels bij achteruitrijden"
"Linked to operation of the power switch","Gekoppeld aan bediening van de contactschakelaar"
"Liquid crystal display","Lcd-scherm"
"List of storage features","Lijst van opslagvoorzieningen"
"Lithium-ion battery","Lithium-ionbatterij"
"Lithium battery CR2450","Lithiumbatterij CR2450"
"Load and distribution","Lading en verdeling"
"Location","Locatie"
"Location of air outlets","Locatie van luchtroosters"
"Location of the emergency tire puncture repair kit and tools","Locatie van de noodreparatieset voor een lekke band en gereedschap"
"Location of the interior lights","Locatie van de interieurverlichting"
"Location of the jack point","Locatie van het krikpunt"
"Location of the SRS airbags","Locatie van de SRS-airbags"
"Location of the storage features","Locatie van de opslagvoorzieningen"
"Location of the tools","Locatie van het gereedschap"
"Locations of airbags","Locatie van airbags"
"Locations of gauges and meters","Locaties van tellers en meters"
"Lock","Vergrendelen"
"Locking and unlocking the AC charging connector","De AC-laadaansluiting vergrendelen en ontgrendelen"
"Locking and unlocking the doors","De deuren ontgrendelen en vergrendelen"
"Locking clip for child restraint system","Borgklem voor kinderzitje"
"Locking the charging connector","Vergrendelen van de laadaansluiting"
"Locking the front doors from the outside without a key","De voorportieren van buitenaf vergrendelen zonder sleutel"
"Locking/unlocking","Vergrendelen/ontgrendelen"
"Locking/unlocking by using the mechanical key","Vergrendelen/ontgrendelen met de mechanische sleutel"
"Locks all the doors","Vergrendelt alle deuren"
"Locks the door","Vergrendelt het portier"
"Long","Groot"
"Long press adjustment","Aanpassen door lang indrukken"
"Low","Laag"
"Low fuel level","Laag brandstofniveau"
"Low objects","Lage objecten"
"Low outside temperature indicator","Indicatielampje lage buitentemperatuur"
"Low speed operation","Lage snelheid"
"Low tire inflation pressure from flat tire","Lage bandenspanning door lekke band"
"Low tire inflation pressure from natural causes","Lage bandenspanning door natuurlijke oorzaken"
"Low washer fluid warning message","Waarschuwingsmelding voor laag ruitensproeiervloeistofniveau"
"Lower hook","Onderste haak"
"Lowers the level of the headlights","Stelt de koplampen naar beneden af"
"LTA (Lane-Tracing Assist) switch","LTA-schakelaar (Lane Tracing Assist, rijstrookassistent)"
"LTA (Lane Tracing Assist) switch","LTA-schakelaar (Lane Tracing Assist, rijstrookassistent)"
"LTA indicator","Indicatielampje LTA"
"LTA switch","LTA-schakelaar"
"Luggage compartment features","Voorzieningen in de bagageruimte"
"Luggage compartment light","Lampje van bagageruimte"
"luggage cover","Hoedenplank"
"Luggage load","Hoeveelheid bagage"
"Lumbar support adjustment switch","Schakelaar voor afstelling van lendensteun"
"Main Owner’s Manual","Hoofdgebruikershandleiding"
"Maintenance","Onderhoud"
"Maintenance and care","Onderhoud en verzorging"
"Maintenance data","Onderhoudsgegevens"
"MAINTENANCE ITEMS","ONDERHOUDSITEMS"
"Maintenance requirements","Onderhoudsvereisten"
"Maintenance schedule","Onderhoudsschema"
"Malfunction in the tire pressure warning system","Storing in het waarschuwingssysteem voor de bandenspanning"
"Manhole covers","Putdeksels"
"Manual Emergency Calls","Handmatige noodoproepen"
"Manual headlight leveling dial","Draaiknop voor handmatige koplampnivellering"
"Manual seat","Handbediende stoel"
"Mass groups","Massagroep"
"MAX","MAX."
"MAXI COSI","MAXI COSI"
"Maximum output","Maximumvermogen"
"Maximum permissible axle capacity","Maximaal toelaatbare asbelasting"
"Maximum permissible rear axle capacity","Maximaal toelaatbare achterasbelasting"
"Maximum torque","Maximumkoppel"
"Meanings","Betekenis"
"mechanical key","Mechanische sleutel"
"Mechanical key linked operation","Werking gekoppeld aan mechanische sleutel"
"Mechanical keys","Mechanische sleutels"
"Medium","Middelgroot"
"Memory recall function","Geheugenfunctie"
"Menu button","Menuknop"
"Menu icons","Menupictogrammen"
"Message","Melding"
"Metal plates","Metaalplaten"
"Metallic wallets or bags","Metalen portemonnees of tassen"
"Meter","Instrumentenpaneel"
"Meter control switches","Bedieningsschakelaars op het instrumentenpaneel"
"Meter display","Meterweergave"
"Meter display and multimedia information","Meterweergave en multimedia-informatie"
"Meters","Tellers"
"Microphone","Microfoon"
"Middle","Middelhoog"
"miles","mijl"
"Minimum vehicle speed","Minimale rijsnelheid"
"Mirror position memory","Spiegelpositiegeheugen"
"Mirrors","Spiegels"
"Mode 2 AC charging cable","AC-laadkabel Mode 2"
"Model","Model"
"Modification and disposal of airbags","Aanpassing en afvoer van airbags"
"Modification and disposal of SRS airbag system components","Aanpassing en afvoer van onderdelen van het SRS-airbagsysteem"
"Modifications to the vehicle’s suspension system","Aanpassing van de ophanging van de auto"
"Motor","Motor"
"Motor compartment","Motorruimte"
"Motorcycles","Motoren"
"Motorway","Autosnelweg"
"Motorway exit","Einde autosnelweg"
"Moving objects","Bewegende objecten"
"Multi-information display","Multi-informatiedisplay"
"Multi-information display operation","Procedure via het multi-informatiedisplay"
"Multimedia display","Multimediadisplay"
"Multimedia operation","Procedure via het multimediadisplay"
"multimedia system","Multimediasysteem"
"Multimedia system screen","Scherm van multimediasysteem"
"Multimedia system screen side","Scherm van multimediasysteem"
"Mute","Dempen"
"Muting a buzzer","Een zoemer dempen"
"Muting a buzzer temporarily","Een zoemer tijdelijk dempen"
"My Room Mode","My Room Mode"
"My Settings","Mijn instellingen"
"N/A","N.v.t."
"Navigation system","Navigatiesysteem"
"Navigation system-linked display","Weergave gekoppeld aan het navigatiesysteem"
"Near","Dichtbij"
"Negative (-) battery terminal","Minpool (-) van de batterij"
"Netherlands","Nederland"
"Neutral","Neutraal"
"New tread","Nieuw loopvlak"
"No-entry","Verboden in te rijden"
"No entry notification function","Waarschuwingsfunctie voor verboden in te rijden"
"No overtaking begins","Begin inhaalverbod"
"No overtaking ends","Einde inhaalverbod"
"Nominal voltage","Nominale spanning"
"Non-seat portions","Andere onderdelen dan de stoelen"
"None","Geen"
"Normal","Normaal"
"Normal driving","Normaal rijden"
"Normal fuse","Normale zekering"
"Normal mode","Normale modus"
"Norway","Noorwegen"
"Not applicable","Niet van toepassing"
"Not available","Niet beschikbaar"
"Not illuminated","Brandt niet"
"NOTE","OPMERKING"
"Note for checking the emergency tire puncture repair kit","Opmerking voor het controleren van de noodreparatieset voor een lekke band"
"Note for the entry function","Opmerking voor de toegangsfunctie"
"Notes when washing the vehicle","Opmerkingen bij het wassen van de auto"
"NOTICE","OPMERKING"
"Notification function","Meldingsfunctie"
"Number of consecutive door lock operations","Aantal opeenvolgende vergrendelingen van de deuren"
"Obstacle Anticipation Assist","Hulp bij anticiperen op obstakels"
"Occupancy and luggage load conditions","Bezetting en hoeveelheid bagage"
"Occupants","Inzittenden"
"odometer","Kilometerteller"
"Odometer","Kilometerteller"
"Odometer and trip meter display","Weergave van kilometerteller en dagtellers"
"Off-road driving","Off-road rijden"
"Off-road driving precautions","Voorzorgsmaatregelen voor off-road rijden"
"Onboard traction battery charger","Boordlader voor de tractiebatterij"
"Oncoming motorcycles","Tegemoetkomende motoren"
"Oncoming vehicle speed","Snelheid van tegenligger"
"Oncoming vehicles","Tegenliggers"
"One-touch closing","Sluiten met één aanraking"
"One-touch opening","Openen met één aanraking"
"Open door warning buzzer","Waarschuwingszoemer bij geopend portier"
"Open tray","Open bak"
"Open window","Ruit geopend"
"Opener","Schakelaar voor openen"
"Opening and closing the power windows","Openen en sluiten van de elektrisch bedienbare ruiten"
"Opening the hood","De motorkap openen"
"Opening, closing and locking the doors","Openen, sluiten en vergrendelen van de portieren"
"Opening/closing the back door","Openen/sluiten van de bagageklep"
"Opening/closing the side windows","Openen/sluiten van de zijruiten"
"Opens the windows","Opent de ruiten"
"Operating conditions","Voorwaarden voor de werking"
"Operating instructions","Instructies voor gebruik"
"Operating the lights and wipers","Bediening van de verlichting en ruitenwissers"
"Operation","Werking"
"Operation buzzer","Zoemer bij werking"
"Operation cancelation conditions","Voorwaarden voor uitschakeling van de werking"
"Operation display of steering wheel operation support","Weergave van werking van stuurondersteuning"
"Operation indicator light","Indicatielampje voor werking"
"Operation noises and vibrations","Geluid en trillingen bij werking"
"Operation of the RCTA function","Werking van de RCTA-functie"
"Operation signal (emergency flashers)","Signaal bij werking (alarmknipperlichten)"
"Operation signals","Signalen bij acties"
"Operation status of the driving assist systems","Werkingsstatus van de rijhulpsystemen"
"Operational symptoms","Symptomen in de werking"
"Optical mirror mode","Optische spiegelmodus"
"Option screen switch","Schakelaar voor optiescherm"
"orange","oranje"
"Other interior features","Andere interieurvoorzieningen"
"Other road signs","Overige verkeersborden"
"Outer foot lights","Buitenste voetlichten"
"Output restrictions reference display","Weergave van informatie over vermogensbeperkingen"
"outside rear view mirror defoggers","Ontwaseming voor de buitenspiegels"
"Outside rear view mirror indicator brightness","Lichtsterkte van de richtingaanwijzers op de buitenspiegels"
"Outside rear view mirror indicator visibility","Zichtbaarheid van de richtingaanwijzers op de buitenspiegels"
"Outside rear view mirror indicators","Richtingaanwijzers op de buitenspiegels"
"Outside rear view mirror switches","Schakelaars voor buitenspiegels"
"Outside rear view mirrors","Buitenspiegels"
"Outside rear view mirrors display","Weergave buitenspiegels"
"Outside temperature","Buitentemperatuur"
"Outside temperature display","Weergave van buitentemperatuur"
"Outside/recirculated air mode","Modus buitenlucht/gerecirculeerde lucht"
"Outside/recirculated air mode switch","Modusschakelaar buitenlucht/gerecirculeerde lucht"
"Overall height","Totale hoogte"
"Overall length","Totale lengte"
"Overall width","Totale breedte"
"Overheating","Oververhitting"
"Overtake prevention","Blokkeren van inhalen"
"Overtaking prevention function","Functie voor het blokkeren van inhalen"
"P position switch","Schakelaar voor de P-stand"
"Paddle shift switch","Schakelflipper"
"Paddle shift switches","Schakelflippers"
"Paddle switch","Schakelflipper"
"Paddle switches","Flippers"
"Panoramic view monitor","Scherm voor panoramische weergave"
"Panoramic View Monitor","Scherm voor panoramische weergave"
"Parked vehicles","Geparkeerde voertuigen"
"Parking brake","Parkeerrem"
"Parking brake automatic lock function","Functie voor automatisch inschakelen van parkeerrem"
"Parking brake automatic release function","Functie voor automatisch uitschakelen van parkeerrem"
"Parking brake engaged warning buzzer","Waarschuwingszoemer parkeerrem ingeschakeld"
"Parking brake indicator","Indicatielampje parkeerrem"
"Parking brake indicator light","Indicatielampje parkeerrem"
"Parking brake operation","Werking van de parkeerrem"
"Parking brake operation sound","Werkingsgeluid van de parkeerrem"
"Parking brake switch","Parkeerremschakelaar"
"Parking Support Brake","Remmen tijdens parkeren"
"Parking the vehicle","Parkeren"
"Parking the vehicle/starting the EV system","Parkeren van de auto/starten van het EV-systeem"
"Partial","Gedeeltelijk"
"Particle filter","Deeltjesfilter"
"Parts and tools","Onderdelen en gereedschap"
"Passenger detection functions","Functies voor passagierdetectie"
"passenger seat only","alleen passagiersstoel"
"Passing other vehicles","Passeren van andere voertuigen"
"PCS-linked control","PCS-gekoppelde controle"
"PCS-linked seat belt pretensioner control","Regeling van gordelspanner bij veiligheidsgordel gekoppeld aan PCS"
"PCS warning light","PCS-waarschuwingslampje"
"PDA indicator","PDA-indicatielampje"
"Pedal clearance","Hoogte van pedaal boven vloer"
"Pedal free play","Vrije slag van pedaal"
"Pedestrian detection icon","Pictogram voor voetgangerdetectie"
"Pedestrians","Voetgangers"
"Pedestrians Rear of the Vehicle","Voetgangers aan achterkant van de auto"
"People suffering illness","Mensen met een aandoening"
"Permanent magnet synchronous motor","Synchroonmotor met permanente magneet"
"Permissible drawbar load","Toegestane belasting van de trekbalk"
"Personal computers","Pc’s"
"Personal lights","Persoonlijke verlichting"
"Persons who are fatigued","Vermoeide personen"
"Persons with sensitive skin","Personen met een gevoelige huid"
"personuvernd@toyota.is","personuvernd@toyota.is"
"personvern@toyota.no","personvern@toyota.no"
"Pictorial index","Afbeeldingsindex"
"PKSB (Parking Support Brake) function","Functie PKSB (remmen tijdens parkeren)"
"PKSB (Parking Support Brake) system","PKSB-systeem (remmen tijdens parkeren)"
"Plated portions","Onderdelen bedekt met platen"
"Plug","Stekker"
"Plug-cord","Netsnoer"
"Points to remember","Aandachtspunten"
"Poland","Polen"
"Pollen removal type","Pollenfilter"
"Poor handling","Slechte rijeigenschappen"
"Pop-up display","Pop-upscherm"
"Portable game systems","Draagbare spelcomputers"
"Portugal","Portugal"
"Position memory switches","Schakelaars voor positiegeheugen"
"Positioning a floor jack","Plaatsen van een krik"
"Positive (+) battery terminal","Pluspool (+) van de batterij"
"Possibility of blowouts resulting from overheated tires","Risico op klapbanden door oververhitting"
"Power (ignition) switch","Contactschakelaar"
"Power area","Vermogensgedeelte"
"Power back door","Elektrisch bedienbare bagageklep"
"Power back door opener and closer","Mechanisme voor openen en sluiten van elektrisch bedienbare bagageklep"
"Power back door opener and closer switch","Schakelaar voor openen en sluiten van elektrisch bedienbare bagageklep"
"Power back door opening position","Openingsstand elektrisch bedienbare bagageklep"
"Power back door operating conditions","Voorwaarden voor werking van de elektrisch bedienbare bagageklep"
"Power back door operation","Werking van elektrisch bedienbare bagageklep"
"Power back door switch","Schakelaar elektrisch bedienbare bagageklep"
"Power consumption","Energieverbruik"
"Power consumption display","Weergave energieverbruik"
"Power control unit","Eenheid voor vermogensregeling"
"Power control unit coolant","Koelvloeistof van de eenheid voor vermogensregeling"
"Power control unit coolant level","Koelvloeistofniveau van eenheid voor vermogensregeling"
"Power control unit coolant reservoir","Koelvloeistofreservoir voor de eenheid voor vermogensregeling"
"Power easy access system","Elektrisch systeem voor gemakkelijke toegang"
"Power indicator","Voedingsindicatielampje"
"Power meter","Vermogensmeter"
"Power mode","Vermogensmodus"
"Power mode indicator","Indicatielampje vermogensmodus"
"Power outlet","Voedingsaansluiting"
"Power plug","Stekker"
"Power seat","Elektrisch bedienbare stoel"
"Power sources","Voedingsbronnen"
"Power sources precautions","Voorzorgsmaatregelen voor voedingsbronnen"
"Power sources that can be used","Te gebruiken voedingsbronnen"
"Power steering","Stuurbekrachtiging"
"Power switch","Contactschakelaar"
"Power switch illumination","Contactschakelaarverlichting"
"Power window","Elektrisch bedienbare ruit"
"Power window lock switch","Schakelaar voor vergrendeling van elektrisch bedienbare ruiten"
"Power window precautions","Voorzorgsmaatregelen voor elektrisch bedienbare ruiten"
"Power window switch","Schakelaar voor elektrisch bedienbare ruiten"
"Power window switches","Schakelaars voor elektrisch bedienbare ruiten"
"Power windows","Elektrisch bedienbare ruiten"
"Power windows open warning buzzer","Waarschuwingszoemer voor geopende elektrisch bedienbare ruiten"
"Pre-collision brake assist","Remhulp van de botswaarschuwing"
"Pre-collision brake control","Remregeling van de botswaarschuwing"
"pre-collision braking","Remmen door de botswaarschuwing"
"Pre-collision braking","Remmen door de botswaarschuwing"
"Pre-collision system","botswaarschuwingssysteem"
"Pre-collision warning","botswaarschuwing"
"Pre-driving check","Controle voordat u gaat rijden"
"Precaution regarding the rear bumper","Waarschuwing met betrekking tot de achterbumper"
"Precautions against towing","Voorzorgsmaatregelen voor trekken"
"Precautions against winter season","Voorzorgsmaatregelen voor de winter"
"Precautions for the emergency tire puncture repair kit","Voorzorgsmaatregelen voor de noodreparatieset voor een lekke band"
"Precautions for use of the sealant","Voorzorgsmaatregelen voor gebruik van het afdichtmiddel"
"Preceding vehicle","Voorgaand voertuig"
"Preceding vehicle deceleration assistance","Hulp bij het afremmen vóór het voorgaande voertuig"
"Pregnant women","Zwangere vrouwen"
"Preparation for winter","Voorbereiding op de winter"
"Preparing and checking before winter","Voorbereiding en controles vóór de winter"
"Press","Indrukken"
"Press and hold","Ingedrukt houden"
"Preventing accidental operation","Onbedoelde bediening voorkomen"
"Preventing damage to leather surfaces","Schade aan leren oppervlakken voorkomen"
"privacy@tgb.toyota.co.uk","privacy@tgb.toyota.co.uk"
"privacy@toyota.be","privacy@toyota.be"
"Proactive Driving Assist","proactieve rijhulp"
"Procedures","Procedures"
"Proper inflation is critical to save tire performance","Een goede bandenspanning is essentieel om te zorgen dat de banden goed blijven presteren"
"Properly sitting in the seat","Op de juiste manier op de stoel zitten"
"Protecting the vehicle interior","Het interieur van de auto beschermen"
"Quantity","Aantal"
"Quick charge","Snelladen"
"R1","R1"
"R2","R2"
"R2X","R2X"
"R3","R3"
"Radar cruise control","Cruisecontrol met radar"
"Radar sensor","Radarsensor"
"Radar sensor cover","Radarsensorkap"
"Radar sensor cover with a heater","Radarsensorkap met verwarming"
"Radar sensors","Radarsensoren"
"Radiant heaters","Stralingsverwarming"
"Radiator","Radiateur"
"Radiator and condenser","Radiateur en condensor"
"Rain","Regen"
"Rain-sensing operation","Werking met regensensor"
"Rain-sensing windshield wipers","Ruitenwissers met regensensor"
"Rain-tight socket","Waterdichte contactdoos"
"Raindrop sensor","Regensensor"
"Rapid charging function","Functie voor snelladen"
"RCTA (Rear Crossing Traffic Alert) function","RCTA-functie (waarschuwing bij achterlangs kruisend verkeer)"
"RCTA buzzer","RCTA-zoemer"
"RCTA function","RTCA-functie"
"RCTA function detection areas","Detectiegebieden van de RCTA-functie"
"Re-enabling the Parking Support Brake","Het remmen tijdens parkeren weer inschakelen"
"Reading this manual","Deze handleiding leiden"
"Rear","Achter"
"Rear camera","Camera aan de achterkant van de auto"
"Rear Camera Detection","detectie met camera achter"
"Rear center seat","Stoel middenachter"
"Rear center sensor","Sensor achter in het midden"
"Rear center sensor detection","Detectie van sensoren middenachter"
"Rear center sensors","Sensoren middenachter"
"Rear corner and rear center sensors","Sensoren achterhoeken en middenachter"
"Rear corner sensor detection","Detectie van sensoren achterhoeken"
"Rear corner sensors","Sensoren achterhoeken"
"Rear Cross Traffic Alert","Waarschuwing bij achterlangs kruisend verkeer"
"Rear Crossing Traffic Alert","Waarschuwing bij achterlangs kruisend verkeer"
"Rear distance guide line","Afstandsgeleidingslijnen achter"
"Rear door child-protector lock","Kindersloten van de achterportier"
"Rear door child-protectors","Kindersloten van de achterportieren"
"Rear eAxle","eAxle achter"
"Rear eAxle fluid type","Vloeistoftype voor eAxle achter"
"Rear electric motor","Elektromotor achter"
"Rear fog light","Mistachterlicht"
"Rear fog light indicator","Indicatielampje mistachterlicht"
"Rear fog lights","Mistlichten achter"
"Rear interior light","Binnenverlichting achter"
"Rear interior light and footwell lights","Interieurverlichting achter en voetverlichting"
"Rear interior lights","Interieurverlichting achter"
"Rear outer seats","Buitenste achterstoelen"
"Rear passengers’ seat belt reminder lights","Herinneringslampjes veiligheidsgordels achterpassagiers"
"Rear passengers’ seat belt warning buzzer","Waarschuwingszoemer veiligheidsgordels achterpassagiers"
"Rear pillars","Achterstijlen"
"Rear seat heater switches","Schakelaars voor stoelverwarming achter"
"Rear seat reminder","Herinnering achterstoelen"
"Rear seat reminder function","Functie voor herinnering achterstoelen"
"Rear seats","Achterstoelen"
"Rear side radar sensors","Radarsensoren achter"
"Rear side sensors","Zijsensoren achter"
"Rear Vehicle Approaching Indication","Indicatie naderend voertuig van achteren"
"Rear view & dual side views/wide rear view & dual side views","Zicht aan achterzijde en dubbel zijzicht/breed zicht aan achterzijde en dubbel zijzicht"
"Rear view & dual side views/wide rear view & dual side views display","Weergave Zicht aan achterzijde en dubbel zijzicht/breed zicht aan achterzijde en dubbel zijzicht"
"Rear view & panoramic view","Zicht aan achterzijde en panoramazicht"
"Rear view & panoramic view/wide rear view & panoramic view display","Zicht aan achterzijde en panoramazicht/breed zicht aan achterzijde en panoramazichtweergave"
"Rear view mirror","Achteruitkijkspiegel"
"Rear window","Achterruit"
"Rear window and outside rear view mirror defogger switch","Schakelaar voor ontwaseming achterruit en buitenspiegels"
"Rear window and outside rear view mirror defoggers switch","Schakelaar voor ontwaseming achterruit en buitenspiegels"
"Rear window defogger","Achterruitverwarming"
"Rearward-facing infant seat","Naar achteren gericht babyzitje"
"Recall procedure","Procedure voor oproepen"
"Recalled functions","Opgeroepen functies"
"Recalling the driving position using the memory recall function","De rijpositie oproepen met de geheugenfunctie"
"Receptacles containing gasoline","Verpakkingen met benzine"
"Recharging cellular phones or cordless phones","Opladers van mobiele telefoons of draadloze telefoons"
"Recharging function","Functie voor opnieuw opladen"
"Recommended child restraint system","Aanbevolen kinderzitje"
"Recommended child restraint systems information","Informatie over aanbevolen kinderzitjes"
"Recording procedure","Procedure voor opslaan"
"Recovering procedure","Procedure voor het bevrijden van de auto"
"Reduced-height, forward-facing child restraint systems","Naar voren gerichte kinderzitjes met beperkte hoogte"
"Reduced-size, rearward-facing child restraint systems","Naar achteren gerichte kinderzitjes van beperkt formaat"
"Reduced driving comfort and poor handling","Verminderd rijcomfort en slechte rijeigenschappen"
"Reduced effectiveness of the EPS system","Verminderde effectiviteit van het EPS-systeem (elektrische stuurbekrachtiging)"
"Reduced electricity consumption efficiency","Hoger elektriciteitsverbruik"
"Reduced safety","Verminderde veiligheid"
"Reduced tire life due to wear","Meer slijtage en kortere levensduur van de banden"
"Reference","Meer informatie"
"Regeneration restrictions reference display","Weergave van informatie over regeneratiebeperkingen"
"Regenerative braking","Regeneratief remmen"
"regenerative braking power indicator","indicatielampje regeneratief remvermogen"
"Registering ID codes","Registreren van id-codes"
"Registering procedure","Registratieprocedure"
"Registering the charging schedule","Instellen van de laadplanning"
"Regulations on the use of tire chains","Voorschriften voor het gebruik van sneeuwkettingen"
"relatii.clienti@toyota.ro","relatii.clienti@toyota.ro"
"Relative speed between your vehicle and object","Relatieve snelheid tussen uw auto en het object"
"Reminder light and buzzer","Herinneringslampje en -zoemer"
"Remote Air Conditioning System","Aircosysteem op afstand"
"Remote Air Conditioning System automatic shut-off","Automatische uitschakeling van het aircosysteem op afstand"
"Remote switch","Afstandsschakelaar"
"Removing a child restraint system installed with a seat belt","Verwijderen van een kinderzitje bevestigd met een veiligheidsgordel"
"Removing the air conditioning filter","Het aircofilter verwijderen"
"Removing the head restraints","Verwijderen van de hoofdsteunen"
"Removing the luggage cover","Verwijderen van de hoedenplank"
"Repairing or replacing snow tires","Repareren of vervangen van winterbanden"
"Repeated setting","Herhalingsinstelling"
"Replacing","Verwisselen"
"Replacing a flat tire","Een wiel met een lekke band verwisselen"
"Replacing light bulbs","Lampjes vervangen"
"Replacing method","Vervangingsmethode"
"Replacing the tire","Een wiel verwisselen"
"Replacing tire pressure warning valves and transmitters","Ventielen en zenders voor waarschuwing voor de bandenspanning vervangen"
"Replacing tires","Banden vervangen"
"Replacing wheels","Velgen vervangen"
"Reservoir","Reservoir"
"Reservoir cap","Dop van reservoir"
"Reset/Display customizable items","Resetten/aanpasbare onderdelen weergeven"
"Residential area beginning","Begin woonerf"
"Residential area ending","Einde woonerf"
"Restraining sudden start","Tegengaan van plotselinge bewegingen"
"Retaining hooks","Bevestigingshaken"
"Return button","Knop Terug"
"Return switch","Terugkeerknop"
"Return to the previous screen","Terug naar het vorige scherm"
"Returning the rear seatbacks","Terugklappen van de rugleuningen van de achterstoelen"
"Reverse estimated course lines","Geschatte richtingslijnen bij achteruitrijden"
"Reverse warning buzzer","Waarschuwingszoemer achteruitrijden"
"Reversing","Achteruit rijden"
"Riding with children","Rijden met kinderen aan boord"
"Right","Rechts"
"Right-hand drive vehicles","Auto’s met stuur rechts"
"Right-hand side temperature control switch","Schakelaar voor temperatuurregeling rechts"
"Right lateral-facing infant seat","Naar rechts gericht babyzitje"
"Right side instrument panel","Instrumentenpaneel rechts"
"Right turn","Rechts afslaan"
"Road accident cautions","Waarschuwingen bij verkeersongevallen"
"Road condition","Rijomstandigheid"
"Road Sign Assist","verkeersbordherkenning"
"Romania","Roemenië"
"Roof luggage carrier","Dakbagagedrager"
"Roof side rails","Zijrails van het dak"
"rope hook","touwhaak"
"Rotary shifter","Draaiknop voor versnellingskeuze"
"Rotary shifter display","Weergave van draaiknop voor versnellingskeuze"
"Rotating tires","Wielen omwisselen"
"Rough road surfaces","Slechte wegen"
"Route guidance to destination","Routegeleiding naar bestemming"
"Routine inspection","Routine-inspectie"
"Routine tire inflation pressure checks","Routinecontrole van de bandenspanning"
"S-FLOW","S-FLOW"
"S PEDAL DRIVE indicator","Indicatielampje S-PEDAL DRIVE"
"S PEDAL DRIVE switch","Schakelaar S-PEDAL DRIVE"
"Safe driving support function","Functie ter ondersteuning van veilig rijden"
"Safe Exit Assist","assistentie voor veilig uitstappen)"
"Safe exit assist operation","Werking van assistentie voor veilig uitstappen"
"Safety function","Beveiliging"
"Safety glasses","Veiligheidsbril"
"Scheduled maintenance","Gepland onderhoud"
"Scrapping of your SUBARU","Afvoeren van uw SUBARU"
"Searching by installation position","Zoeken op installatiepositie"
"Searching by name","Zoeken op naam"
"Searching by symptom or sound","Zoeken op symptoom of geluid"
"Searching by title","Zoeken op titel"
"seat adjustment","afstelling van stoelen"
"Seat adjustment caution","Waarschuwing bij afstelling van stoelen"
"Seat belt","Veiligheidsgordel"
"Seat belt attachment","Bevestiging van veiligheidsgordel"
"Seat belt damage and wear","Beschadiging en slijtage van een veiligheidsgordel"
"Seat belt precautions","Voorzorgsmaatregelen voor veiligheidsgordels"
"Seat belt pretensioner system","Gordelspannersysteem"
"Seat belt pretensioners","Gordelspanners"
"Seat belt pretensioners and force limiters","Gordelspanners en gordelkrachtbegrenzers"
"Seat belt regulations","Voorschriften voor veiligheidsgordels"
"Seat belt reminder light","Herinneringslampje veiligheidsgordel"
"Seat belt shoulder anchor height","Hoogte van schoudergordelklem"
"Seat belts","Veiligheidsgordels"
"Seat cushion (front) angle adjustment switch","Schakelaar voor de hoekafstelling van het zitkussen (voor)"
"Seat heater switches","Schakelaars voor stoelverwarming"
"Seat heaters","Stoelverwarming"
"Seat heaters operation","Werking van stoelverwarming"
"Seat position adjustment lever","Hendel voor afstelling van stoelpositie"
"Seat position adjustment switch","Schakelaar voor afstelling van stoelpositie"
"Seat position memory","Stoelpositiegeheugen"
"Seat position number","Nummer van stoelpositie"
"Seat upholstery","Stoelbekleding"
"Seatback angle adjustment lever","Hendel voor afstelling van hoek van rugleuning"
"Seatback angle adjustment switch","Schakelaar voor afstelling van hoek van rugleuning"
"Seating position","Stoelpositie"
"Seating position suitable for lateral fixture","Stoelpositie geschikt voor laterale bevestiging"
"Seating position suitable for universal belted","Stoelpositie geschikt voor universeel kinderzitje met gordel"
"Seats","Stoelen"
"Second position","Tweede stand"
"Secondary Collision Brake","Remmen tegen tweede botsing"
"Secondary Collision Brake automatic cancellation","Automatische uitschakeling van remmen tegen tweede botsing"
"Secondary Collision Brake operating conditions","Voorwaarden voor de werking van remmen tegen tweede botsing"
"Security feature","Beveiliging"
"Security indicator","Indicatielampje beveiliging"
"Selecting the driving mode","De rijmodus selecteren"
"Selecting tire chains","Sneeuwkettingen kiezen"
"Selecting wheel set","De wielset selecteren"
"Self-restoring coat","Zelfherstellende coating"
"Sensor","Sensor"
"Sensor detection information","Informatie over de sensordetectie"
"Server","Server"
"Service plug","Serviceaansluiting"
"Service responsible for handling access requests","Dienst verantwoordelijk voor behandeling van toegangsverzoeken"
"Set cooling and dehumidification function","Instellen van de koel- en ontvochtigingsfunctie"
"Setting","Instellen"
"Setting procedure","Instelprocedure"
"Setting/canceling the double locking system","Instellen/uitschakelen van het dubbel vergrendelingssysteem"
"Setting/canceling/stopping the alarm system","Instellen/uitschakelen/stoppen van het alarmsysteem"
"Settings","Instellingen"
"Settings display","Weergave van instellingen"
"Severe driving","Hevig rijden"
"Shaded high beam","Afgeschermd grootlicht"
"Shampooing the carpets","Met shampoo wassen van de vloerbedekking"
"Sharply-angled objects","Objecten met scherpe hoeken"
"Shift lever","Versnellingshendel"
"Shift lights","Schakelverlichting"
"Shift position","Versnellingsstand"
"Shift position indicator","Versnellingsindicator"
"Shift position linked door locking function","Aan versnellingsstand gekoppelde functie voor portiervergrendeling"
"Shift position linked door unlocking function","Aan versnellingsstand gekoppelde functie voor portierontgrendeling"
"Shift position operation","Schakelen"
"Shift position purpose and functions","Doel en functie van versnellingen"
"Short","Klein"
"Short beep","Korte piep"
"Side airbag operating conditions","Voorwaarden voor activering van de zijairbags"
"Side airbag precautions","Voorzorgsmaatregelen voor zijairbags"
"Side airbags","Zijairbags"
"Side and curtain shield airbags operating conditions","Voorwaarden voor activering van de zij- en gordijnairbags"
"Side and curtain shield airbags precautions","Voorzorgsmaatregelen voor zij- en gordijnairbags"
"Side chain","Zijketting"
"Side doors","Portieren"
"Side impact sensors","Botssensoren zijkant"
"Side mirrors","Zijspiegels"
"Side pillars","Zijstijlen"
"Side turn signal lights","Richtingaanwijzers zijkant"
"Side view & Rear view","Zijzicht en zicht aan achterzijde"
"Side view & Wide front view","Zijzicht en breed zicht aan voorzijde"
"Side view & Wide rear view","Zijzicht en breed zicht aan achterzijde"
"Side views","Zicht aan de zijkanten"
"Situation","Situatie"
"Situations in which the system may not operate properly","Situaties waarin het systeem mogelijk niet naar behoren werkt"
"Situations in which the tire pressure warning system may not operate properly","Situaties waarin het waarschuwingssysteem voor de bandenspanning mogelijk niet naar behoren werkt"
"Situations when it is necessary to contact dealers before towing","Situaties waarin u contact moet opnemen met een dealer voordat er wordt gesleept"
"Size","Formaat"
"Size class","Lengteklasse"
"Slip indicator","Slipindicatielampje"
"Slovenia","Slovenië"
"Slow","Langzaam"
"Slow charge","Langzaam laden"
"Small flathead screwdriver","Kleine platte schroevendraaier"
"Smart door unlocking","Slimme deurontgrendeling"
"Smart entry & start system","Smart Entry met startsysteem"
"Smart entry & start system indicator","Indicatielampje Smart Entry met startsysteem"
"Smart entry and start system","Smart Entry met startsysteem"
"Smart entry and start system indicator","Indicatielampje Smart Entry met startsysteem"
"Smart transmitter","Slimme afstandsbediening"
"Smart tuner","Slimme tuner"
"Snow plows","Sneeuwschuivers"
"Snow tires","Winterbanden"
"SNOW/DIRT mode","SNOW/DIRT-modus"
"SNOW/DIRT mode indicator","Indicatielampje SNOW/DIRT-modus"
"SNOW•DIRT Mode","Modus SNEEUW/ONVERHARD"
"SOC (State of Charge) gauge","Laadstatusmeter"
"Software update","Software-update"
"Solution","Oplossing"
"Spain","Spanje"
"Speaker","Luidspreker"
"Specification","Specificatie"
"Specifications","Specificaties"
"Speech command window operation","Werking van het spraakcommandovenster"
"Speed limit begins/Maximum speed zone begins","Begin van maximumsnelheid(szone)"
"Speed limit change notification","Melding wijziging snelheidslimiet"
"Speed limit ends/Maximum speed zone ends","Einde van maximumsnelheid(szone)"
"Speed limit related information","Informatie over snelheidslimiet"
"Speed limit road signs","Verkeersborden met een maximumsnelheid"
"Speed limit with supplemental mark","Snelheidslimiet met onderbord"
"Speed limiter","Snelheidsbegrenzer"
"Speed limiter indicator","Indicatielampje snelheidsbegrenzer"
"Speed limiter switch","Schakelaar voor snelheidsbegrenzer"
"Speed limiter with Road Sign Assist","Snelheidsbegrenzer met verkeersbordherkenning"
"Speed linked door locking function","Aan snelheid gekoppelde functie voor portiervergrendeling"
"Speed setting","Snelheidsinstelling"
"Speedometer","Snelheidsmeter"
"Spherical portion","Bolle gedeelte"
"Sport mode","Sportmodus"
"SRS airbag","SRS-airbag"
"SRS airbag deployment conditions","Voorwaarden voor activering van de SRS-airbags"
"SRS airbag precautions","Voorzorgsmaatregelen voor SRS-airbags"
"SRS airbag system","SRS-airbagsysteem"
"SRS airbag system components","Onderdelen van het SRS-airbagsysteem"
"SRS airbags","SRS-airbags"
"SRS curtain shield airbags","SRS-gordijnairbags"
"SRS driver airbag/front passenger airbag","SRS-airbag bestuurder/airbag voorpassagier"
"SRS front airbags","SRS-frontairbags"
"SRS front center airbag","SRS-frontairbag in het midden"
"SRS front center airbags","SRS-frontairbags in het midden"
"SRS front passenger airbag","SRS-airbag voor voorpassagier"
"SRS Front Seat Center AirBag","SRS-airbag midden tussen de voorstoelen"
"SRS knee airbag","SRS-knieairbag"
"SRS side airbags","SRS-zijairbags"
"SRS side and curtain shield airbags","SRS-zij- en SRS-gordijnairbags"
"SRS warning light","SRS-waarschuwingslampje"
"Standard","Norm"
"Starting off on a steep uphill","Heuvelopwaarts optrekken op een steile helling"
"Steering","Stuurinrichting"
"Steering icon","Stuurpictogram"
"Steering lock","Stuurslot"
"Steering lock function","Stuurslotfunctie"
"Steering lock system warning message","Waarschuwingsmelding van het stuurslotsysteem"
"Steering parts","Onderdelen van de stuurinrichting"
"Steering wheel","Stuur"
"Steps to take in an emergency","Te ondernemen stappen bij een noodsituatie"
"Sticker","Sticker"
"Stop","Stop"
"Stop hold phase","Stopvasthoudfase"
"Stop light indicator","Indicatielampje remlichten"
"Stop lights","Remlichten"
"stopped vehicles","stilstaande voertuigen"
"Stopping the vehicle","De auto tot stilstand brengen"
"Storage","Opslag"
"Storage feature","Opslagvoorziening"
"Storage location","Opslaglocatie"
"Storage precautions","Voorzorgsmaatregelen voor opslag"
"Strange noises related to suspension movement","Vreemde geluiden bij beweging van de ophanging"
"Strange noises related to the suspension system","Vreemde geluiden van de ophanging"
"Stuck","Vastzitten"
"SUBARU","SUBARU"
"SUBARU Care","SUBARU Care"
"SUBARU Park Assist 3D Display","3D-weergave SUBARU-parkeerhulp"
"SUBARU Park Assist Distance","Afstand SUBARU-parkeerhulp"
"SUBARU Parking Assist","SUBARU-parkeerhulp"
"SUBARU Parking Assist buzzer","Zoemer van SUBARU-parkeerhulp"
"SUBARU Parking Assist detection indicator","Indicatielampje SUBARU-parkeerhulpdetectie"
"SUBARU Parking Assist linked display","Weergave gekoppeld aan SUBARU-parkeerhulp"
"SUBARU Parking Assist monitor","Scherm voor SUBARU-parkeerhulp"
"SUBARU Parking Assist mute button","Toets voor het dempen van het geluid van SUBARU-parkeerhulp"
"SUBARU Parking Assist OFF","SUBARU-parkeerhulp UIT"
"SUBARU Parking Assist OFF indicator","Indicatielampje SUBARU-parkeerhulp UIT"
"SUBARU Parking Assist pop-up display","Pop-upscherm SUBARU-parkeerhulp"
"SUBARU Parking Assist sensor","SUBARU-parkeerhulpsensor"
"SUBARU Parking Assist sensor buzzer","Zoemer van SUBARU-parkeerhulpsensor"
"SUBARU Parking Assist sensor on/off","SUBARU-parkeerhulpsensor aan/uit"
"SUBARU Safety Sense","SUBARU Safety Sense"
"SUBARU Safety Sense software update","Update van SUBARU Safety Sense-software"
"Sudden start restraint control","Regeling om plotselinge bewegingen tegen te gaan"
"Suggestion function","Suggestiefunctie"
"Suitable forward facing fixture","Geschikt voor bevestiging naar voren gericht kinderzitje"
"Suitable junior seat fixture","Geschikt voor bevestiging van peuterzitje"
"Suitable rearward facing fixture","Geschikt voor bevestiging naar achteren gericht kinderzitje"
"Summary of the driving assist systems","Samenvatting van de rijhulpsystemen"
"Summary of the system","Overzicht van het systeem"
"Sun visors","Zonnekleppen"
"Sunshade","Zonnescherm"
"Supplemental mark exists","Onderbord aanwezig"
"Supply type","Voedingstype"
"Support sensitivity","Ondersteuningsgevoeligheid"
"Suspension ball joints and dust covers","Kogelgewrichten en stofkappen ophanging"
"Suspension of the settings display","Tijdelijke uitschakeling van de weergave van instellingen"
"Suspension parts","Onderdelen van de ophanging"
"Sweden","Zweden"
"switch","Schakelaar"
"Switching the display","Overschakelen van de weergave"
"Switching the door unlock function","Overschakelen van de functie voor portierontgrendeling"
"Switching the meter display","Overschakelen van de meterweergave"
"Switzerland","Zwitserland"
"Symbols","Symbool"
"Symbols in illustrations","Symbolen in afbeeldingen"
"Symbols in this manual","Symbolen in deze handleiding"
"Symptom","Symptoom"
"System component","Systeemcomponent"
"System components","Systeemonderdelen"
"System controls","Systeemregeling"
"System disabled","Systeem uitgeschakeld"
"System functions","Systeemfuncties"
"System maintenance","Onderhoud van het systeem"
"System operating conditions","Voorwaarden voor de werking van het systeem"
"System operation display","Weergave van de werking van het systeem"
"System overview","Systeemoverzicht"
"System overview of added service","Overzicht van toegevoegde diensten van het systeem"
"Table lamps","Tafellampen"
"Table of contents","Inhoudsopgave"
"Tail light indicator","Indicatielampje achterlicht"
"Tail lights","Achterlichten"
"Talk switch","Spreekschakelaar"
"TEL switch","TEL-schakelaar"
"Temperature detection function","Functie voor temperatuurdetectie"
"Temporary cancelation of functions","Tijdelijke uitschakeling van functies"
"Temporary operation","Eén keer wissen"
"Terminals","Aansluitingen"
"The camera","De camera"
"The rear door cannot be opened","Het achterportier kan niet worden geopend"
"Theft deterrent system","Antidiefstalsysteem"
"Ticket holders","Kaarthouders"
"tietosuoja@toyota.fi","tietosuoja@toyota.fi"
"Tightening torque","Aanhaalkoppel"
"Tilt and telescopic steering control switch","Schakelaar voor kantelen en intrekken/uitschuiven van stuur"
"Tilt and telescopic steering lock release lever","Schakelaar voor ontgrendeling van kantelen en in-/uitschuiven van het stuur"
"Tilt meter","Hellingmeter"
"Tilt meter display","Weergave hellingmeter"
"Tilt sensor","Kantelsensor"
"Time","Tijd"
"Tire","Wiel"
"Tire chain installation","Aanbrengen van sneeuwkettingen"
"Tire inflation pressure","Bandenspanning"
"Tire inflation pressure display function","Weergavefunctie voor bandenspanning"
"Tire information","Informatie over banden"
"Tire life","Levensduur van banden"
"Tire pressure","Bandenspanning"
"Tire pressure gauge","Bandenspanningsmeter"
"Tire pressure warning light","Waarschuwingslampje bandenspanning"
"Tire pressure warning reset switch","Resetschakelaar voor de waarschuwing voor de bandenspanning"
"Tire pressure warning system","Waarschuwingssysteem bandenspanning"
"Tire rotation","Wielen omwisselen"
"Tire size","Bandenmaat"
"Tire size/inflation pressure","Bandenmaat/bandenspanning"
"Tires","Banden"
"Tires and inflation pressure","Bandenspanning en vuldruk"
"Tires and wheels","Banden en wielen"
"tmi.dpo@toyota-europe.com","tmi.dpo@toyota-europe.com"
"To prevent burns","Om brandwonden te voorkomen"
"Tools","Gereedschap"
"Top strap","Bovenste band"
"Top tether anchorage attachment","Bevestiging van “top tether”"
"Top tether anchorages","“Top tether”-bevestigingspunten"
"Torque distribution","Koppelverdeling"
"Total average","Gemiddelde totaal"
"Total Time","Totale tijd"
"Total trailer weight","Totale aanhangermassa"
"Total trailer weight and permissible drawbar load","Totale aanhangermassa en toegestane belasting van de trekbalk"
"Towing","Trekken"
"Towing capacity","Maximaal getrokken massa"
"Towing eyelet","Sleepoog"
"Towing hitch/Bicycle holder bracket","Trekhaak/beugel voor fietsendrager"
"Towing hitch/bracket","Trekhaak/trekbeugel"
"Towing with a sling-type truck","Slepen met een kraanwagen"
"Towing with a wheel-lift type truck","Slepen met een lepelwagen"
"Toyota parking assist-sensor","Toyota-parkeerhulpsensor"
"Toyota Safety Sense","Toyota Safety Sense"
"Toyota Smart Center","Toyota Smart Center"
"Toyota.Datenschutz@toyota.de","Toyota.Datenschutz@toyota.de"
"toyota@toyota.dk og","toyota@toyota.dk og"
"traction battery","Tractiebatterij"
"Traction battery","Tractiebatterij"
"Traction battery charge","Opladen van de tractiebatterij"
"Traction battery charge warning light","Waarschuwingslampje tractiebatterij"
"Traction battery charger","Tractiebatterijlader"
"Traction battery coolant","Koelvloeistof tractiebatterij"
"Traction battery cooler","Tractiebatterijkoeler"
"Traction battery heater","Tractiebatterijverwarming"
"Traction battery type","Type tractiebatterij"
"Traction battery warming control","Regeling van de tractiebatterijverwarming"
"Traction Control","tractieregeling"
"Traction motor","tractiemotor"
"Traction related parts","Onderdelen van de aandrijflijn"
"Trademark information","Informatie over handelsmerken"
"Trailer lights","Aanhangerverlichting"
"Trailer Sway Control","slingerbeheersing van aanhanger"
"Trailer Sway Control precaution","Voorzorgsmaatregelen voor Trailer Sway Control (slingerbeheersing van aanhanger)"
"Trailer towing","Trekken van een aanhanger"
"Trailer towing precautions","Voorzorgsmaatregelen voor het trekken van een aanhanger"
"Transaxle fluid","Transaxlevloeistof"
"Transmission:","Transmissie:"
"Tray within console box","Bak in het consolevak"
"TRC","TRC"
"Tread","Spoorbreedte"
"Treadwear indicator","Slijtage-indicator van het loopvlak"
"Triggering of the alarm","Activering van het alarm"
"Trip average","Gemiddelde rit"
"Trip meter A/Trip meter B","Dagteller A/dagteller B"
"Trip meters","Dagtellers"
"Truss bridges","Vakwerkbruggen"
"Tunnels","Tunnels"
"Türkiye","Türkiye"
"Turn signal indicator","Indicatielampje richtingaanwijzers"
"Turn signal lever","Hendel voor richtingaanwijzers"
"Turn signal lights","Richtingaanwijzers"
"Turn signals can be operated when","De richtingaanwijzers kunnen worden bediend wanneer"
"Turning on the high beam headlights","Grootlicht inschakelen"
"Turning the Blind Spot Monitor on/off","De dodehoekbewaking in-/uitschakelen"
"Turning the high beams on/off manually","Het grootlicht handmatig in-/uitschakelen"
"Turning the RCTA function on/off","De RCTA-functie in-/uitschakelen"
"Type A","Type A"
"Type B","Type B"
"Type C","Type C"
"Types of data and its recipients","Gegevenstypes en ontvangers"
"Types of sensors","Sensortypes"
"™","™"
"UN(ECE) R129 approval mark","Goedkeuringsmerkteken voor UN(ECE) R129"
"UN(ECE) R44 approval mark","Goedkeuringsmerkteken voor UN(ECE) R44"
"Uneven wear","Ongelijkmatige slijtage"
"Units","Meeteenheden"
"Unlock","Ontgrendelen"
"Unlocking function","Ontgrendelfunctie"
"Unlocking operation","Ontgrendeling"
"Updating the software","Bijwerken van de software"
"Upper hook","Bovenste haak"
"Urban area beginning","Begin bebouwde kom"
"Urban area ending","Einde bebouwde kom"
"Usable temperature range","Temperatuurbereik voor gebruik"
"Usage","Gebruik"
"Usage in winter time","Gebruik in de winter"
"USB charging ports","USB-laadpoorten"
"USB Type-C charging ports","USB-C-laadpoorten"
"Used wheels","Gebruikte velgen"
"Using automatic mode","De automatische modus gebruiken"
"Using the air conditioning system and defogger","Gebruik van het aircosysteem en de ontwasemer"
"Using the driving support systems","Gebruik van de rijhulpsystemen"
"Using the interior lights","Gebruik van de interieurverlichting"
"Using the other interior features","Gebruik van de andere interieurvoorzieningen"
"Using the storage features","Gebruik van de opslagvoorzieningen"
"Using the voice control system","Het spraakbesturingssysteem gebruiken"
"Using the wireless remote control","Gebruik van de draadloze afstandsbediening"
"utility hook","voorzieningenhaak"
"Utility vehicle feature","Kenmerk van SUV’s"
"Utility vehicle precautions","Voorzorgsmaatregelen voor SUV’s"
"Vanity lights","Make-uplampjes"
"Vanity mirrors","Make-upspiegels"
"Vehicle","Voertuig"
"Vehicle-equipped jack","Krik bij de auto"
"Vehicle-to-vehicle distance","Afstand tot voorligger"
"Vehicle-to-vehicle distance setting","Instelling van afstand tot voorligger"
"Vehicle-to-vehicle distance switch","Schakelaar voor afstand tot de voorligger"
"Vehicle condition","Staat van auto"
"Vehicle customization","Voertuiginstellingen"
"Vehicle data recording","Vastlegging van voertuiggegevens"
"Vehicle identification","Voertuigidentificatie"
"Vehicle identification number","Voertuigidentificatienummer"
"Vehicle information display","Weergave van voertuiginformatie"
"Vehicle rollover","Over de kop slaan van de auto"
"Vehicle specifications","Voertuigspecificaties"
"Vehicle speed","Rijsnelheid"
"Vehicle speed in towing","Rijsnelheid tijdens het trekken van een aanhanger"
"Vehicle Stability Control","voertuigstabiliteitsregeling"
"Vehicle Stability Control+","voertuigstabiliteitsregeling+"
"Vehicle status information and indicators","Voertuigstatusinformatie en indicatielampjes"
"vehicles with towing packages","Auto’s met trekpakket"
"Ventilation and air conditioning odors","Geuren van ventilatie en airco"
"Vertical adjustment","Hoogteverstelling"
"Vertical height adjustment lever","Hendel voor hoogteverstelling"
"Vertical height adjustment switch","Schakelaar voor hoogteverstelling"
"Vibration","Trilling"
"VIEW switch","WEERGAVE-schakelaar"
"Visible symptoms","Zichtbare symptomen"
"Visual","Visueel"
"Visual & Audible","Visueel en Hoorbaar"
"Voice notifications","Gesproken meldingen"
"Voltage","Spanning"
"Voltage range","Spanningsbereik"
"VSC OFF indicator","Indicatielampje VSC UIT"
"VSC off switch","Schakelaar VSC UIT"
"Warms up the grip of the steering wheel","Verwarmt de buitenkant van het stuur"
"WARNING","WAARSCHUWING"
"Warning buzzer","Waarschuwingszoemer"
"Warning buzzer/message","Waarschuwingszoemer/-melding"
"Warning function","Waarschuwingsfunctie"
"Warning label","Waarschuwingsetiket"
"Warning light","Waarschuwingslampje"
"Warning lights","Waarschuwingslampjes"
"Warning lights and indicators","Waarschuwingslampjes en indicatielampjes"
"Warning lights and indicators displayed on the instrument cluster","Waarschuwingslampjes en indicatielampjes op het instrumentenpaneel"
"Warning lights/indicator lights","Waarschuwingslampjes/indicatielampjes"
"Warning message","Waarschuwingsmelding"
"Warning message display","Weergave van waarschuwingsmeldingen"
"Warning messages","Waarschuwingsmeldingen"
"Warning messages and buzzers","Waarschuwingsmeldingen en zoemers"
"Warning phase","Waarschuwingsfase"
"Warning phase 1","Waarschuwingsfase 1"
"Warning phase 2","Waarschuwingsfase 2"
"Warning reflector","Gevarendriehoek"
"Warning symbols","Waarschuwingssymbolen"
"Warning timing","Waarschuwingsmoment"
"Washer","Ruitensproeier"
"Washer","Sluitring"
"Washer fluid","Ruitensproeiervloeistof"
"Washer fluid tank","Ruitensproeierreservoir"
"Washer/wiper dual operation","Inschakelen van ruitenwisser en -sproeier tegelijk"
"Washing and waxing","Wassen en in de was zetten"
"Water pump","Waterpomp"
"Wearing a seat belt","Een veiligheidsgordel dragen"
"Weight limits","Gewichtslimieten"
"What about do-it-yourself maintenance?","Het onderhoud zelf uitvoeren"
"Wheel bolt socket","Wielboutdop"
"Wheel bolt torque","Aanhaalkoppel van wielbouten"
"Wheel bolt wrench","Wielsleutel"
"Wheel bolts","Wielbouten"
"Wheel chock positions","Positie van wielblok"
"Wheel deformation and/or tire damage","Vervorming van de wielen en/of schade aan de banden"
"Wheel selection","Velgen kiezen"
"Wheel size","Velgmaat"
"Wheelbase","Wielbasis"
"Wheels","Velgen"
"Wheels and wheel ornaments","Velgen en siervelgen"
"Wheels of different sizes or types","Velgen met verschillende maten of van verschillende types"
"When functioning abnormally","Wanneer deze abnormaal werkt"
"When replacing the battery","Bij het vervangen van de batterij"
"When rotating the tires","Wanneer u de wielen omwisselt"
"When the warning lights come on","Wanneer de waarschuwingslampjes gaan branden"
"When the warning messages are displayed","Wanneer de waarschuwingsmeldingen worden weergegeven"
"When to initialize","Wanneer initialisatie nodig is"
"When trouble arises","Wanneer zich problemen voordoen"
"White","Wit"
"Winches","Lieren"
"Window glasses","Ruiten"
"window lock switch","Schakelaar voor ruitvergrendeling"
"Window lock switch","Schakelaar voor ruitvergrendeling"
"Windows","Ruiten"
"Windshield","Voorruit"
"Windshield defogger","Voorruitontwaseming"
"Windshield defogger switch","Schakelaar voor voorruitontwaseming"
"Windshield wiper and washer switch","Schakelaar voor ruitenwissers en -sproeier"
"Windshield wiper de-icer","Ruitenwisserverwarming"
"Windshield wiper de-icer switch","Schakelaar voor ruitenwisserverwarming"
"Windshield wipers","Ruitenwissers"
"Windshield wipers and washer","Ruitenwissers en -sproeier"
"Windshield wipers and washer switch","Schakelaar voor ruitenwissers en -sproeier"
"Winter drive tips","Rijtips voor de winter"
"Winter driving tips","Rijtips voor de winter"
"Winter tires/tire chain","Winterbanden/sneeuwkettingen"
"Wiper lever","Ruitenwisserhendel"
"Wireless charger","Draadloze lader"
"Wireless charger tray lights","Verlichting voor draadloos oplaadvak"
"Wireless remote control","Draadloze afstandsbediening"
"Wireless remote control linked operation","Werking gekoppeld aan draadloze afstandsbediening"
"Wireless remote control linked operation signal","Signaal bij werking gekoppeld aan draadloze afstandsbediening"
"Worn tread","Versleten loopvlak"
"www.toyota-europe.com","www.toyota-europe.com"
"www.toyota.nl/klantenservice","www.toyota.nl/klantenservice"
"X-MODE","X-MODE"
"X-MODE switch","Schakelaar X-MODE"
"X Mode Switch","Schakelaar X-modus"
"Yellow","Geel"
"You lose your keys","U verliest uw sleutels"
"door","portier"
"outlet","contactdoos"
"Proactive Driving Assist","proactieve rijhulp"
"as a reference only","slechts als indicatie"
"as a reference","als indicatie"
"warning buzzers","waarschuwingszoemers"
"door lock buzzer","zoemer voor portiervergrendeling"
"door lock switch","schakelaar voor portiervergrendeling."
"luggage compartment","bagageruimte"
"back door handles","handgrepen van de bagageklep"
"kick sensor","trapsensor"
"interior alarm","interieuralarm"
"radio waves","radiogolven"
"luggage cover","hoedenplank"
"battery-saving mode","batterijspaarmodus"
"digital anti-glare mode indicator","indicatielampje voor de digitale antischittermodus"
"seatback angle adjustment","afstelling van hoek van rugleuning"
"seat cushion (front) angle adjustment","hoekafstelling van het zitkussen (voor)"
"vertical height adjustment","hoogteverstelling"
"outer mirror angle adjustment","afstelling van de buitenspiegelhoek"
"infrared rays","infraroodstraling"
"parking assist-sensor","parkeerhulpsensor"
"brake pedal","rempedaal"
"parking brake","parkeerrem"
"original position","oorspronkelijke stand"
"swivel for curves","meedraaien in bochten"
"self-luminous light sources","zelflichtgevende lichtbronnen"
"switch ring","skakelring"
"wiper switch","schakelaar voor de ruitenwissers"
"water repellent coating","waterafstotende coating"
"normal position","normale stand"
"retracted position","parkeerstand"
"surrounding conditions","omgevingsomstandigheden"
"license plate covers","kentekenplaathouders"
"grill badges","grille-emblemen"
"license plates","kentekenplaten"
"radar waves","radarstralen"
"SSS control unit","SSS-regeleenheid"
"air intake vent","luchtinlaat"
"truss bridge","vakwerkbrug"
"camera monitoring","camerabewaking"
"acceleration suppression at low speed","acceleratieonderdrukking bij lage snelheid"
"lane lines","rijstrookmarkeringen"
"lane change","rijstrookverandering"
"lane or course","rijstrook of weg"
"detectable object","detecteerbaar object"
"detected object","gedetecteerd object"
"target object","doelobject"
"moving object","bewegend object"
"static object","stilstaand object"
"traffic cones"."verkeerskegels"
"output restriction control","vermogensbegrenzing"
"eco run mode","eco-rijmodus"
"driving assist mode","rijhulpmodus"
```


---

## File: `solterra-batch-translation/reference/patterns.csv`

```csv
english,dutch
for details on,voor meer informatie over
refer to,zie
the kick sensor may not operate.,werkt de kicksensor mogelijk niet.
lower center part of the rear bumper,het onderste middendeel van de achterbumper
as shown in the illustration,zoals weergegeven in de afbeelding
after the image is taken,na vastlegging van het beeld
"any authorized SUBARU retailer or SUBARU authorized repairer, or any reliable repairer","een erkende SUBARU-dealer, een door SUBARU erkende reparateur of een andere betrouwbare hersteller"
possibly leading to an accident,wat kan leiden tot een ongeval
when the power switch is turned to ON,wanneer het contact wordt ingeschakeld
laws and regulations,wetgeving en voorschriften
Customizable features,Aan te passen functies
```


---

## File: `solterra-batch-translation/reference/units.csv`

```csv
"English","Dutch"
"km/h (mph)","km/h"
"km (mile) / km (miles)","km"
"rpm","rpm (min-1)"
"L (qt., Imp.qt.) / L (gal., Imp.gal.)","l"
"kg (lb.)","kg"
"°C (°F)","°C"
"V","V"
"A","A"
"W","W"
"mm (in.)","mm"
"m (ft.)","m"
"N (kgf, lbf)","N (kp)"
"N·m (kgf·m, ft·lbf)","N·m (kp·m)"
"kPa (kgf/cm2 or bar, psi)","kPa (kgf/cm2 of bar)"
"cm3 (cu.in.)","cm3"
"kHz","kHz"
"0.1","0,1"
"1000","1000"
"1,000","1.000"
"10000","10000"
"10,000","10.000"
"No.","Nr."
"NO.","NR."
"No.1","Nr.1"
"No. 1","Nr. 1"
":",":"
"“ ”","“ ”"
"’","’"
```
