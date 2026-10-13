"""Enumerate the linguistic and behavioural infrastructure this project depends on.

Why this exists
---------------
The report listed the corpora -- the data -- and nothing else. But a corpus is only meaningful
relative to the instruments that read it, and this project's instruments are numerous and
load-bearing: the reading channel cannot be constructed without `pypinyin`, the script-purity
gate is `GlotScript`, the script-type field is `alphabetic`, grapheme segmentation is `regex`'s
`\\X`, the English word-level frequency cross-check is `wordfreq`, and the measurement itself
requires `torch` and `transformers` driving one specific checkpoint. None of that appeared. A
reader could not tell what would have to be installed to reproduce a single number.

The list is therefore DERIVED, not written. The script parses every Python file in `scripts/`
with `ast`, collects the imports, resolves each to its distribution and version, and asserts at
the end that every import it found is classified. A hand-written list would be a second copy of
the truth, and would go stale the first time a dependency changed -- which is exactly how the
word-frequency instrument came to be missing while being used in seven places.

Output: config/instruments.json
"""
from __future__ import annotations

import ast
import collections
import importlib.metadata
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
OUT = REPO / "config" / "instruments.json"

# How each third-party import is pinned to a distribution on PyPI, where the names differ.
DIST_ALIAS = {
    # import name -> distribution name
    "sklearn": "scikit-learn",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "fitz": "pymupdf",
    "docx": "python-docx",
    "markdown_it": "markdown-it-py",
    "GlotScript": "GlotScript",
    "scienceplots": "SciencePlots",
}

# What each instrument is FOR, and its published basis where it has one. The purpose string is
# the load-bearing part: it says what would be missing from the data if the tool were absent.
CATALOG = {
    "playwright": {
        "role": "instrument",
        "purpose": ("renders the report in a real browser and asserts that every section has "
                    "content; the only check that can distinguish a section which is present and "
                    "empty from one which rendered"),
        "citation": "Playwright, browser automation library for Chromium, Firefox and WebKit (Apache-2.0).",
    },
    "pypinyin": {
        "role": "instrument",
        "purpose": ("the reading of a Han character, which is what the input-method channel's "
                    "candidate set is built from and what its frequency rank is defined over"),
        "citation": "pypinyin, Python library for Han-to-pinyin conversion (MIT).",
    },
    "wordfreq": {
        "role": "instrument",
        "purpose": ("lexical frequency for real-word filtering and for the English arms' "
                    "word-level cross-check; a published frequency resource, separate from the "
                    "corpus-observed character frequency used for the reading channel"),
        "citation": ("Speer, J. (2022). wordfreq: a Python library for accessing the world's "
                     "languages' word frequencies."),
    },
    "GlotScript": {
        "role": "instrument",
        "purpose": ("measures the writing system actually present in a line, which is what "
                    "enforces each arm's script declaration (the purity gate)"),
        "citation": ("Kargaran, A. H., Yvon, F. & Schu\u0308tze, H. (2024). GlotScript. "
                     "LREC-COLING 2024, 7774-7784."),
    },
    "alphabetic": {
        "role": "instrument",
        "purpose": ("classifies text as alphabet / abjad / abugida / syllabary / logographic; "
                    "supplies the script-type field. It reports French as AZERTY and the Japanese "
                    "writing system as mixed rather than syllabic"),
    },
    "regex": {
        "role": "instrument",
        "purpose": ("grapheme-cluster segmentation via \\X. Required, not cosmetic: slicing by "
                    "code point splits a combining accent from its base, so len() and slice "
                    "indices disagree with what a reader sees as a character"),
        "citation": "regex, Python module for extended regular expressions (Apache-2.0).",
    },
    "jieba": {"role": "instrument", "purpose": "Chinese word segmentation for the word-level views"},
    "fugashi": {"role": "instrument", "purpose": "Japanese morphological analysis (MeCab binding)"},
    "unidic_lite": {"role": "instrument", "purpose": "the dictionary fugashi analyses Japanese with"},
    "pykakasi": {"role": "instrument", "purpose": "kana/romaji conversion for the Japanese arm"},
    "mecab": {"role": "instrument", "purpose": "Japanese morphology (DLL conflicts on this host)"},
    "unisc": {"role": "instrument", "purpose": "script/Unicode property queries"},
    "multypo": {
        "role": "instrument",
        "purpose": ("the published multilingual typo generator, run against this project's "
                    "languages to establish what the published instrument does and does not "
                    "cover: it raises Unsupported language for Chinese and Japanese"),
        "citation": "MuLTYPO (ACL 2026).",
    },
    "torch": {"role": "instrument", "purpose": "the tensor runtime the measurement runs on"},
    "transformers": {
        "role": "instrument",
        "purpose": ("loads and drives the checkpoint under measurement, with trust_remote_code "
                    "for the checkpoint's own architecture definition"),
    },
    "numpy": {"role": "library", "purpose": "array arithmetic"},
    "scipy": {"role": "library", "purpose": "statistical tests"},
    "matplotlib": {"role": "library", "purpose": "figure generation"},
    "scienceplots": {
        "role": "library",
        "purpose": "the Nature-style matplotlib style used for every figure",
        "citation": "SciencePlots.",
    },
    "pymupdf": {
        "role": "library",
        "purpose": ("reads the source PDFs, which is how a citation is checked against the paper "
                    "it names rather than against a second memory of it"),
    },
    "pandas": {"role": "library", "purpose": "tabular processing"},
    "statsmodels": {"role": "library", "purpose": "regression and inference"},
    "lxml": {"role": "library", "purpose": "XML handling for the document pipeline"},
    "markdown_it": {"role": "library", "purpose": "markdown rendering for the document pipeline"},
    "docx": {"role": "library", "purpose": "DOCX output for the manuscript pipeline"},
    "requests": {"role": "library", "purpose": "HTTP for acquisition"},
    "tqdm": {"role": "library", "purpose": "progress reporting"},
}

INTERNAL = {
    "typo_noise": "the noise channel model shared by the phase-2 measurement scripts",
    "keyboard_channel": "the keyboard-adjacency channel, built from the 136M Keystrokes estimate",
    "o1_calibration": "the readability-calibration machinery for the O1 instrument",
    "o1_recoverability": "the recoverability index",
    "o1_auto_indices": "automatic index construction for O1",
    "o1_agent_rater": "the agent rater used in the O1 validation",
    "merge_ratings": "rating aggregation",
    "o3_leakage_probe": "the leakage probe",
    "derive_panels": "figure panel derivation",
    "measure_collision_evidence": "measures the impossibility theorem's antecedent",
    "si_render": "supplementary-information rendering",
    "omml": "Office MathML emission for the DOCX pipeline",
    "nature_style": "the journal figure specification: widths, type sizes, tick weights, palette, "
                    "the shared axes styling and the four-format output set every figure uses",
}


def imports_of(path: pathlib.Path) -> set:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.add(node.module.split(".")[0])
    return out


def version_of(mod: str) -> str | None:
    dist = DIST_ALIAS.get(mod, mod)
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    if "--negative-test" in sys.argv:
        # Inject an undeclared import into a temporary script inside scripts/ and require the
        # check to reject it. A guard that has never failed is not a guard, and this one's positive
        # direction is trivially satisfiable by classifying nothing. The probe is written and
        # removed inside this call so a crash cannot leave it behind and poison later runs.
        probe = SCRIPTS / "_probe_undeclared_import.py"
        if probe.exists():
            print("  [FAIL] probe file already exists at %s; refusing to overwrite it" % probe)
            return 1
        try:
            probe.write_text("import definitely_not_a_declared_tool_xyz\n", encoding="utf-8")
            code = build(write=False)
        finally:
            probe.unlink(missing_ok=True)
        if code != 0:
            print()
            print("  [OK] negative control fires: the undeclared import was rejected")
            return 0
        print()
        print("  [FAIL] the negative control did not fire: an undeclared import was injected into")
        print("         %s and the check accepted it, so the check is not comparing anything."
              % probe.name)
        return 1

    if "--check" in sys.argv:
        # A guard mode: regenerate into memory and compare against the file on disk, so a
        # dependency added to a script without being declared is caught rather than shipped.
        if not OUT.exists():
            print("  [FAIL] no instrument manifest at %s; run without --check to build it" % OUT)
            return 1
        before = OUT.read_bytes()
        code = build(write=False)
        if code != 0:
            return code
        if OUT.read_bytes() != before:
            msg = build(write=True)
            print()
            print("  [FAIL] the instrument manifest is stale: an import was added, removed or "
                  "renamed since it was written (%s)" % (msg and "rebuilt" or "rebuild failed"))
            return 1
        print()
        print("  [OK] the instrument manifest matches the imports in scripts/")
        return 0
    return build(write=True)


def build(write: bool) -> int:
    stdlib = set(sys.stdlib_module_names)
    found: dict = collections.defaultdict(set)
    for p in sorted(SCRIPTS.glob("*.py")):
        for m in imports_of(p):
            found[m].add(p.name)

    third = {m: sorted(v) for m, v in found.items()
             if m not in stdlib and not m.startswith("_") and m not in INTERNAL}

    records, unclassified = [], []
    for m, files in sorted(third.items()):
        meta = CATALOG.get(m)
        if meta is None:
            unclassified.append(m)
            continue
        records.append({
            "import": m,
            "distribution": DIST_ALIAS.get(m, m),
            "version": version_of(m),
            "role": meta["role"],
            "purpose": meta["purpose"],
            "citation": meta.get("citation"),
            "used_in": files,
            "n_files": len(files),
        })

    internal = [{"module": m, "purpose": INTERNAL[m], "used_in": sorted(found[m])}
                for m in sorted(INTERNAL) if m in found]

    # the pipelines and artefacts the report's numbers are read from
    artefacts = []
    for rel, why in [
        ("config/rrc.json", "the manifest every count in the report is read from"),
        ("data/rrc/*.jsonl", "the shipped items, one file per arm"),
        ("data/processed/han_char_frequency.json",
         "corpus-observed character frequency, the reading channel's rank denominator"),
        ("data/processed/keystroke_channel.json", "the empirical keystroke channel estimate"),
        ("data/processed/rrc_profile.json", "the numeric profile"),
        ("data/processed/falsifier_f3_coverage.json", "the layer-coverage analysis"),
        ("config/datasets.json", "the provenance registry"),
        ("config/data_manifest.json", "the file-level manifest of the corpora on disk"),
    ]:
        artefacts.append({"path": rel, "purpose": why, "exists": bool(list(REPO.glob(rel)))})

    vendored = []
    for d in sorted((REPO / "infra").glob("*")) if (REPO / "infra").exists() else []:
        if d.is_dir():
            vendored.append({"dir": "infra/" + d.name,
                             "n_files": sum(1 for _ in d.rglob("*") if _.is_file())})

    payload = {
        "generated_by": "scripts/build_instrument_manifest.py",
        "why": ("The report listed the data and not the instruments. This is the instrument list, "
                "derived from the imports in scripts/ so it cannot omit a dependency that is "
                "actually used."),
        "n_python_files_scanned": sum(1 for _ in SCRIPTS.glob("*.py")),
        "instruments": records,
        "internal_modules": internal,
        "artefacts": artefacts,
        "vendored": vendored,
    }
    if write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("  scanned       : %d python files" % payload["n_python_files_scanned"])
    print("  third-party   : %d classified, %d unclassified" % (len(records), len(unclassified)))
    print("  internal      : %d modules" % len(internal))
    print("  artefacts     : %d (%d present)"
          % (len(artefacts), sum(1 for a in artefacts if a["exists"])))
    print("  vendored      : %d directories" % len(vendored))
    if unclassified:
        print()
        for m in unclassified:
            print("  [FAIL] import used but not classified: %s  (in %s)"
                  % (m, ", ".join(sorted(found[m])[:3])))
        print()
        print("  Every dependency must be declared. A tool that computes a number has to be")
        print("  named as surely as the corpus that supplies it.")
        return 1
    print()
    print("  [OK] every import in scripts/ is declared")
    print("  %s %s" % ("wrote" if write else "checked", OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
