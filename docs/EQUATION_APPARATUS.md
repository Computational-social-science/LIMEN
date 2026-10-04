# Equation apparatus — the source side, done before the renderer

**Measured before this work (and the reason for it).** A reference NHB-format manuscript
(`manuscript_NHB_publishable.html`, 693 KB) carried **24 `.eq-*` components, 9 numbered equations and
a purpose-sentence → equation → note pattern for every one of them.** This protocol's nine display
equations had **none of the three**: no purpose sentence, no number, no note. The gap was never in the
renderer — the renderer cannot invent the sentence that says what an equation is *for*.

**All nine equations now carry all three parts.** The apparatus lives in the anchor, not in the
builder, because the anchor is the programme's single authority and a scholarly device is content.

## What each note does, and why it is not decoration

The notes were written from symbols the protocol **already defines elsewhere** — nothing was imported
and no definition was invented. Two of them carry the argument rather than the notation:

- **SilentError** is identified as the metric that carries the thesis, because it counts only trials on
  which the model **committed and was wrong** — the subset no accuracy figure can see — and it is $P_e$
  in the noisy-channel reading of §0.1. It is also noted as **non-decreasing in $\tau$**, which is the
  reason $\tau$ is pre-registered rather than chosen after seeing the curve.
- **Coverage** is identified as the **Rate** of the same channel, so the pair (SilentError, Coverage)
  traces a rate–error curve — which is what makes "noise leaves the curve unchanged" testable instead
  of rhetorical, and is the mechanism H1.3 tests.

The remaining notes define symbols, and each says what the protocol does **not** license. Equation (2)
records that **no other map takes $\lambda$ as an argument**, which is what makes the central claim
checkable. Equation (5) records that the gate compares **no distance** from $c$ to $\tau$, matching
the refusal in §0.3. Equation (6) records that it differences **two estimated thresholds, not two
measurements of one thing** — the reason it stays diagnostic.

## Three defects this work introduced, and how each was caught

Every one of these produced a document that looked correct and was not. All three were found by
**re-reading the file after writing**, not by inspecting the code that wrote it.

1. **A formula was cut in half.** Inserting the note for equation (9) at an index computed *before* an
   earlier insertion shifted it, so the note landed **inside** the formula body:
   `\mathrm{Coverage@}\va` / `**The three dependent variables…**` / `epsilon(s,\lambda) = …`. A
   section-level rebuild from the pre-edit byte copy fixed it; the copy is `viz/protocol.md`, written by
   the HTML builder as the exact bytes it read.

2. **A sentence was orphaned.** The purpose sentence for equation (6) was appended after `then report`,
   which had been the end of a sentence — leaving `then report` / `**The diagnostic quantity…**` as two
   fragments. Merged into one sentence.

3. **My own verifier reported a false pass.** The check searched for `**where` while the notes begin
   with `where `, so it reported "no notes added" on notes that had been added correctly. **A checker
   that reports the wrong thing is worse than no checker**, and this one nearly caused duplicate notes
   to be written.

## Idempotence and structure, both verified

```
display equations   9 → 9        tables 99 rows → 99 rows
headings           39 → 39, order identical
blockquotes       105 → 105 rows
final: 9/9 equations carry purpose + equation + note
```

Structure is asserted against the pre-edit copy on every run, because an insertion that renumbers a
heading or drops a table row is invisible in a prose read-through and fatal in a protocol.