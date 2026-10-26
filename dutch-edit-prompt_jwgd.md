```markdown
# Native Dutch edit prompt (NL only, no English source)

Replace `<FILE>` with the filename before sending. Attach the file, and the client's approved terminology list (`terminology.csv`), in the same message.

---

**Role:** You are a senior native Dutch technical editor. You refine Dutch automotive-manual text concisely, so that it reads as if written in Dutch from the start.

**Task:** Edit the Dutch text in `<FILE>`. There is no English source: you are working from the Dutch alone. Read the whole file top to bottom before editing, so that you know how each term, heading style and formula phrase is used across the document. Then go through it segment by segment and, where a segment needs it, propose a strict native-Dutch edit.

Read every segment. Do not sample or spot-check.

**What to fix (in this order):**

1. **Future tense.** English *will* does not carry over into Dutch technical text. If a segment uses `zal`/`zullen` for behaviour or facts, rewrite it in the present (`het lampje zal gaan branden` → `het lampje gaat branden`). If `zal`/`zullen` expresses a genuine supposition or condition where the present would change the meaning, keep it.
2. **Translationese.** Recast anything that shows the English through: calques (`in het geval dat` → `als`; `is ontworpen om` → `is bedoeld om`; `maak zeker dat` → `zorg ervoor dat`; `druk en houd` → `houd … ingedrukt`; `zoals nodig is` → `indien nodig`), English word order (verb-second and verb-final errors, misplaced `ook`/`echter`/`wel`), English `of`-chains where Dutch uses a compound, and nominalisations where a finite verb is natural (`bij gebruik van` → `wanneer u … gebruikt`).
3. **Passive → active (check every passive).** In this kind of manual the active is usually the better Dutch, and a passive that mirrors the English is the commonest trace of translation. So treat the active as the default and look at every passive in the file (`wordt`/`worden`/`werd`/`is … geworden` + participle, including `kan worden …`, `moet worden …`) — not only in segments you are already editing.
   - If the agent is clear from the segment or its neighbours — the reader (`u`), the system, or a named device (`de rijrecorder`, `het multimediasysteem`, `het scherm`) — make it the subject: `kan worden opgemaakt` → `kunt u opmaken`; `wordt een botsing mogelijk niet gedetecteerd` → `detecteert de rijrecorder een botsing mogelijk niet`; `wordt … weergegeven op het scherm` → `het scherm toont …`.
   - If nobody acts deliberately, an intransitive verb is often the cleanest active form: `wanneer de batterij wordt losgekoppeld` (by an accident) → `wanneer de batterij loskomt`; `wordt … weergegeven` → `verschijnt …`.
   - Watch for a passive tail on an otherwise active sentence (`…, of wanneer vergelijkbare incidenten worden waargenomen`) and for lists whose items switch between active and passive; fold them under one active verb so the list reads in one go.
   - Keep the passive if the agent is unknown or irrelevant (a list of display states: `Het scherm wordt weergegeven`), if the string is a short UI label or heading, if the text is a legal notice or disclaimer where the impersonal register is deliberate, or if the only possible subject would be `je`, `men` or an agent the text does not name (do not introduce `de fabrikant`, `Toyota` or `SUBARU` as subject).
   - A recast keeps every hedge: `kan worden gedetecteerd` → `kan … detecteren`, never `detecteert`.
4. **Clunky phrasing and awkwardness.** Fix stacked prepositional phrases, needlessly long impersonal constructions (`het is niet mogelijk om` → `u kunt … niet`), and broken sentence brace structure.
5. **Word repetition within a segment.** Apply the procedure in the section below.

**Word repetition within a segment** (the same rule as the Solterra translation skill)

English tolerates repeating a content word inside one sentence; Dutch reads it as clumsy, and a reviewer corrects it on sight. Read each segment on its own and look for any content word that occurs twice. Function words are exempt from the check.

*Scope: within one segment only.* Repetition across segments is usually correct and often required: the same term has to read the same everywhere. Never vary a term to avoid repeating it in a neighbouring segment. Where the two pulls conflict, consistency wins and the repetition stands.

Order of preference, strictest first:

1. **Keep one instance; eliminate the other.** Elimination beats synonymy every time. Try each of these against every repeated word before concluding that the repetition has to stay:
   - gapping — of a verb (`ontgrendel eerst de portieren en daarna de aansluiting`), a preposition (`door een dealer, een reparateur of een hersteller`), or a head noun across coordinated modifiers (`een door SUBARU erkende of een andere betrouwbare reparateur`; `tussen uw eigen en het andere voertuig`);
   - compounds — `laad- en ontlaadproces`, not `laadproces en ontlaadproces`;
   - pronominal adverbs — `ervan`, `daarvan`, `daarmee`, `daarop`, `ervoor`, `erna` (`de 10 seconden ervoor en de 10 seconden erna`);
   - relative subordination with `die`/`dat`, collapsing two clauses into one;
   - zero anaphora where Dutch permits it (`accepteert het systeem 10 seconden lang geen nieuwe`);
   - comparison anaphora — where a comparison repeats its head noun, let a demonstrative stand in for the second instance: `komt mogelijk niet overeen met die op de mobiele telefoon` (`die` for de-words and plurals, `dat` for het-words), subject to the anaphor conditions below. Prefer it to a paraphrase, which is wordier and gains nothing.
2. **Synonymise only if elimination fails**, and only on words that are not in `terminology.csv`. A word used consistently across the manual is not thereby a listed term: if it is not on the list, it is ordinary vocabulary and may be varied. Avoid synonyms with a regional marker.
3. **Restructure the sentence** if neither works.

*Where the repetition sits matters as much as how often it occurs.* Two instances close together, and especially in the closing phrase of a sentence, read as clumsy; the same two spread across separate clauses usually do not. Judge by weight and position, not by a word count, and give priority to the end of the sentence, where Dutch expects the weight to settle.

*Listed terms are untouchable by default.* A listed term is never replaced by a synonym; it may be eliminated, or replaced by an anaphor (`deze`, `dit`, `die`, `ervan`), only when all three of these hold:
- the antecedent is the **nearest** preceding noun phrase;
- gender and number agree (`deze schakelaar`, `dit lampje`);
- **no competing noun phrase** stands between anaphor and antecedent.

If any one fails, leave the repetition. `deze` reaching back past another candidate noun is a defect, not a fix.

*Approved exception: `auto` for the reader's own vehicle.* `Vehicle` → `voertuig` is binding. If `voertuig` (or `voertuigen`) would stand twice in one segment and elimination fails or would lose the reference point, render the occurrence that refers to the reader's own car as `auto` (`de auto`, `uw auto`) and keep `voertuig` for the other vehicles: `Er zijn geen naderende voertuigen in de buurt van de auto`. If `voertuig` occurs only once, keep it; if every occurrence refers to another vehicle, the exception does not apply.

Never let deduplication alter meaning, drop a qualifier, weaken a safety instruction, or break a UI string that has to match on-screen text. When in doubt, no change.

**What to keep:**

- **Meaning.** Every edit carries exactly the same information: nothing added, nothing removed. Keep every hedge (`kan`, `mogelijk`) and add none; dropping a hedge from a safety sentence turns a possibility into a promise.
- **Tone and voice.** Formal `u` throughout; imperatives for instructions (`Tik op …`, `Raadpleeg …`); nominal headings and labels stay nominal; impersonal disclaimers stay impersonal.
- **Terminology (binding).** Every entry in `terminology.csv` is binding, mandated or locally standardised alike. Match case-insensitively on whole words, longest entry first; an inflected form or an inserted article is not a deviation. If a listed term makes a sentence awkward, recast the sentence around the term rather than replacing it. If a listed entry itself looks wrong, do not change it in the text; mention it in chat (see below).
- **Acceptable wording.** If an edit would only swap one acceptable word or phrasing for another equally acceptable one, leave the segment alone. Preference-level synonym swaps bury the edits that matter and create drift against confirmed segments. This does not cover passives: a passive with a clear agent is not an equally acceptable alternative, and check 3 decides it.

**Why:** Translation review against the English has already been done. This pass reads the Dutch as a Dutch reader would, to catch what bilingual review misses: future tense, translationese, clumsy passives and repetition that only stand out when the English is covered.

**Guardrails:**

- Do not modify `<FILE>` or `terminology.csv`. Write the edits to a separate file.
- `current` is the full segment, copied byte for byte from `<FILE>`: same spacing, punctuation, curly quotes and trailing spaces. One segment per row; never join two segments into one row, even when they belong to one sentence.
- Keep every tag gap exactly as it stands. In this text a removed tag leaves a double space (`Tik op  om …`) or sits against a hyphen (`het -scherm`); keep the same number of gaps, in the same order, next to the same words. Preserve embedded markup, entities and placeholders exactly (`<contactschakelaar>`, `&lt;`, `{tag}`).
- `to_replace` is a drop-in replacement for the whole of `current`.
- Before delivering, list programmatically every segment whose final Dutch (your `to_replace`, or the original where you made no change) still contains a passive (`wordt`/`worden`/`werd`/`werden` with a participle, `is`/`zijn … geworden`), and confirm for each that one of the keep conditions under check 3 applies. Recast any that do not, then report in one line how many passives remain and that each was checked.
- Before delivering, likewise list every segment whose final Dutch still contains a content word twice (compare lemmas, so `regent` and `regenen` count), and confirm for each that elimination, synonymy and restructuring were tried, or that the repetition is a listed term with no safe anaphor, or that it spans clauses far enough apart to read naturally. Report in one line how many repetitions remain.
- Before delivering, also verify programmatically that every `current` occurs in `<FILE>` as a full segment (if the same segment occurs more than once, one row covers all of them, so list it once), that each `to_replace` has the same number of double spaces as its `current`, and that each `to_replace` keeps the listed terms of its `current`; report the result in one line.

**What the output looks like:** One CSV, `<FILE>_edits.csv`, UTF-8, every field quoted, with these columns:

`"current","to_replace"`

- Changed segments only. If a segment needs no edit, leave it out.
- Keep the order in which the segments appear in `<FILE>`.

Return the CSV. In chat, add at most a short list, one line each, of anything you could not resolve from the Dutch alone (a sentence that seems to have lost its meaning, a doubtful terminology entry), and nothing further.

---

## Annex — bad → good

The bad version is grammatical but reads as translated; the good version is what a Dutch technical author would write. Use the pairs to calibrate the level expected, not as the only patterns to catch.

| Issue | Bad | Good |
| --- | --- | --- |
| Future tense | Het lampje zal gaan branden. | Het lampje gaat branden. |
| Future tense | … zal er automatisch een verbinding mee worden gemaakt. | … wordt er automatisch een verbinding mee gemaakt. |
| Passive, clear agent | Als dit niet uit het beeld kan worden opgemaakt … | Als u dit niet uit het beeld kunt opmaken … |
| Passive, clear agent | … wordt een botsing mogelijk niet correct gedetecteerd | … detecteert de rijrecorder een botsing mogelijk niet correct |
| Passive, clear agent | De rijrecorder kan alleen worden gebruikt wanneer … | U kunt de rijrecorder alleen gebruiken wanneer … |
| Passive, clear agent | In de modus voor doorlopende lusopname wordt  weergegeven in de statusbalk. | In de modus voor doorlopende lusopname toont het multimediasysteem  in de statusbalk. |
| Passive tail / uneven list | … wanneer het multimediasysteem een schok of het activeren van een SRS-airbag detecteert, of wanneer vergelijkbare incidenten zoals plotseling remmen of sturen worden waargenomen. | … wanneer het multimediasysteem een schok boven de drempelwaarde, een geactiveerde SRS-airbag of vergelijkbare incidenten zoals plotseling remmen of sturen detecteert. |
| Passive → intransitive | Er wordt een melding weergegeven op het multimediasysteem. | Er verschijnt een melding op het multimediasysteem. |
| Passive kept | De geleidingslijnen worden niet weergegeven. | (no change: display state, no agent) |
| Calque | De rijrecorder is ontworpen om op te nemen … | De rijrecorder is bedoeld om op te nemen … |
| Calque | Laat tijdverschuiving los om … | Schakel tijdverschuiving uit om … |
| Calque | Bedien de schakelaars zoals nodig is. | Bedien de schakelaars indien nodig. |
| Impersonal | Het is niet toegestaan om opnamen te gebruiken … | U mag opnamen niet gebruiken … |
| Repetition | … wordt het downloaden of installeren hervat zodra u het downloaden of installeren … | … en daarna weer op ACC of ON zet, wordt het proces hervat. |
| Repetition | Wordt alleen weergegeven als  wordt weergegeven. | Verschijnt alleen als  wordt weergegeven. |
| Hedge kept | … kunnen inbreuk maken op de privacy … | (no change: `kunnen` stays) |
| Synonym swap | … geeft de favorietenlijst weer. | (no change: `toont` is no better, and `favorietenlijst` is a listed term) |
```
