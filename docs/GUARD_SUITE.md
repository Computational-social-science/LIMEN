# Guard suite — what each guard checks, and why three were needed

**Three mechanical guards, each with one job, each with a negative control.** A guard that has never
failed is not a guard, so every one of these can be asked to prove it fails.

| Guard | Checks | Negative control |
|---|---|---|
| `scripts/check_object_drift.py` | **Vocabulary.** Retired-object terms appearing in live files. | injects each rule class |
| `scripts/check_relative_paths.py` | **Rule 1 of `global-research-project-rules`** — no absolute paths. | injects an absolute path into a script and into a document |
| `scripts/check_anchor.py` | **Anchor integrity** — the objective is present, version-coherent, uncontradicted, and its promised paths resolve. | injects hash drift, version disagreement, a dead reference, an authority claim |

## Why the second and third guards exist

**Both were written because a real defect survived the first one.**

`CURRENT_OBJECT.md` listed nine paths under the heading *"Live instruments — kept, and why"*, and
asserted that "the current object needs them". **All nine did not exist** — every one was under
`archive/R1_jevrsi_loop_objective_2026-10-04/`. The vocabulary guard reported `OK` across 45 files,
because a promise to a file that is gone is not retired vocabulary. **A path that cannot be resolved
is the most mechanical contamination class there is, and nothing checked it.**

Protocol v1.2 was then edited in three places while `§12` still specified the superseded three-question
`Q0` and `§14` still read *"Version 1.1"* / *"End of protocol v1.1"*. The version markers disagree in
exactly that way whenever an edit lands in one place and not another, so that check is mechanical.

## The finding that mattered more than the defects

**The first version of the dead-reference check produced 46 findings, of which about 43 were false.**
It flagged every path a document merely *mentions*: files inside the model repository, sibling
documents named without their directory, output names a report describes, and files a spec will create.

**A checker with a 2 % signal rate trains its reader to ignore it, which is worse than having no
checker.** The trigger was therefore changed from *"a path is mentioned"* to *"a path is **promised**"* —
the sentence must carry an availability or obligation verb — and retirement records are exempt by
construction, because a sentence saying a path was archived is the opposite of a promise.

Two more self-inflicted defects were found **by running** the guard, not by reading it:

- **URLs produced phantom drives.** The Windows-drive pattern ate the tail of a scheme, so
  `https://hf-mirror.com` left the fragment `s://hf-mirror.com`, reported as a path on drive `s`.
  Nine findings, all imaginary. URLs are now blanked before the scan.
- **Shebangs are not paths.** `#!/usr/bin/env python` contains `/usr/bin/env` by definition. Also
  blanked.

**Both were caught only because the guard was run against a repository containing those constructs.**
A guard validated only against synthetic inputs would have shipped with both defects and been
trusted anyway.

## Known open findings, and why they are not blocking

Each of the following was examined by hand and judged a legitimate statement. They are listed so a
reader can disagree with the judgement rather than discover it later.

| Finding | Why it is legitimate |
|---|---|
| `scripts/build_item_bank.py` names `scripts/template_confound_probe.py` | The probe is **committed to and not yet written.** The builder documents the plan. |
| `docs/ITEM_BANK_SPEC.md` names `BANK_SPEC_FROZEN.md` | An artefact the spec **requires** the bank to carry at freeze time. |
| `docs/PAPER_AGENT_LIBRARY.md` names `paper.md` | A file **inside a generated skill package**, not in this repository. |
| `docs/INSTRUMENT_LEDGER.md` names two retired instruments | The ledger's **entire purpose** is to name them, with their archive location. |

**If any of these becomes a real promise — the probe is never written, the bank never carries its
record — the guard will still say `OK`, because it checks resolvability and not intent.** That limit is
stated here rather than left to be discovered.

## One more limit, stated plainly

**`check_relative_paths.py` still reports 2 findings in code that are not machine paths** — a
fragment of a regular expression, and a Windows path that is part of a longer literal. They are
advisory rather than blocking, and they are the residue of a heuristic scan. A perfect scanner for
"is this a path" is not achievable by pattern alone, and the guard's value is in the blocking cases,
not in being noiseless.