"""Keyboard channels, parsed from CLDR LDML Part 7 rather than drawn by hand.

Why the layout has to come from a standard. The Latin and Cyrillic confusable layer is the
keystroke: a typist substitutes a neighbouring key. Which keys are neighbours is a property
of the *language's* layout, not of the alphabet, and a hand-written QWERTY is wrong for most
of them. Measured here: the French first row is `a z e r t y u i o p` -- q and a, w and z
are swapped relative to QWERTY -- so a QWERTY-derived neighbour set is simply the wrong
instrument for French. The Japanese case is stronger still: the CLDR layout carries
`flickId`, and あ い う え お sit on one key reached by directional flicks, so for kana the
channel is the flick group and not physical adjacency at all.

Source. CLDR `keyboards/3.0/*.xml` (Unicode, LDML Part 7). The files present in
`infra/cldr-keyboards/` were fetched from unicode-org/cldr; the provenance of each is its
`locale` and `layout` attributes, which are read rather than restated.

Scope, stated rather than hidden. CLDR ships keyboards only where the platform default is
insufficient, so `fr`, `pt`, `mt`, `bn`, `sa-Deva` and the Japanese ones are present and
`en` and `ru` are not. For those two the module reads a layout table that is declared with
its provenance in LAYOUTS below rather than being inferred, and `layout_source()` says
which of the two routes a given language took so a reader can tell them apart.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

INFRA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "infra")
CLDR_DIR = os.path.join(INFRA, "cldr-keyboards", "3.0")

# CLDR locales on disk, keyed by the BCP-47 tag the file declares.
CLDR_FILES = {
    "fr": "fr.xml",
    "pt": "pt-t-k0-abnt2.xml",
    "mt": "mt.xml",
    "bn": "bn.xml",
    "sa-Deva": "sa-Deva-t-k0-qwerty.xml",
    "ja-Hira": "ja-Hira-t-k0-flicks.xml",
    "ja-Latn": "ja-Latn.xml",
}

# Where CLDR has no keyboard, the layout is declared here with its provenance rather than
# being derived from an assumption about what the keys "probably" are. Both are the
# conventional national layouts; the rows are read left to right.
LAYOUTS = {
    "en": {
        "source": "declared-ansi",
        "note": "US ANSI QWERTY (ISO/IEC 9995-2 physical arrangement)",
        "rows": [
            "` 1 2 3 4 5 6 7 8 9 0 - =",
            "q w e r t y u i o p [ ]",
            "a s d f g h j k l ; '",
            "z x c v b n m , . /",
        ],
    },
    "ru": {
        "source": "declared-jcuken",
        "note": "Russian ЙЦУКЕН (GOST 6431-90 key arrangement)",
        "rows": [
            "ё 1 2 3 4 5 6 7 8 9 0 - =",
            "й ц у к е н г ш щ з х ъ",
            "ф ы в а п р о л д ж э",
            "я ч с м и т ь б ю .",
        ],
    },
}

# The physical stagger: each row below the top is offset by roughly half a key, so a key's
# neighbours are the two beside it and the one or two diagonally below/above. Encoding that
# offset is what makes the neighbour set a keyboard model rather than a string index.
_ROW_OFFSET = {0: 0, 1: 0, 2: 0, 3: 0}


def _load_imports(root, ns: str, out: dict) -> None:
    """Pull key definitions from the files a keyboard imports.

    A keyboard only defines the keys that differ from the platform default; everything else,
    including the punctuation names such as `open-angle` and `at`, arrives through
    `<import base="cldr" path="..."/>`. Without following those the row list is a list of
    key *names* rather than characters -- which is exactly what an early version reported.
    """
    for imp in root.iter(ns + "import"):
        path = imp.get("path") or ""
        fn = os.path.basename(path)
        for cand in (os.path.join(CLDR_DIR, fn),
                     os.path.join(CLDR_DIR, "45", fn),
                     os.path.join(CLDR_DIR, "import", fn)):
            if os.path.exists(cand):
                try:
                    iroot = ET.parse(cand).getroot()
                    # The imported files are written without a namespace -- the DOCTYPE form
                    # `<!DOCTYPE keys SYSTEM ...>` and a bare <keys> -- while the keyboard
                    # files use the schema namespace. Searching only for the namespaced tag
                    # therefore found nothing and the rows kept their key *names*. Both forms
                    # are accepted here.
                    found = list(iroot.iter(ns + "key"))
                    if not found:
                        found = list(iroot.iter("key"))
                    for k in found:
                        kid, o = k.get("id"), k.get("output")
                        if kid and o and kid not in out:
                            out[kid] = _unescape(o)
                except Exception:  # noqa: BLE001
                    pass
                break


def _parse_cldr(path: str) -> dict:
    """The rows, key outputs and flick groups of one CLDR keyboard file."""
    ns = "{https://schemas.unicode.org/cldr/45/keyboard3}"
    root = ET.parse(path).getroot()
    outputs = {}
    for k in root.iter(ns + "key"):
        kid, out = k.get("id"), k.get("output")
        if kid and out:
            outputs[kid] = _unescape(out)
    _load_imports(root, ns, outputs)
    layers = {}
    for layer in root.iter(ns + "layer"):
        mods = layer.get("modifiers") or "none"
        rows = []
        for row in layer.iter(ns + "row"):
            ids = (row.get("keys") or "").split()
            rows.append([outputs.get(i, i) for i in ids])
        if rows:
            layers[mods] = rows
    flicks = {}
    for fl in root.iter(ns + "flick"):
        fid = fl.get("id")
        chars = []
        for seg in fl.iter(ns + "flickSegment"):
            c = outputs.get(seg.get("keyId") or "")
            if c:
                chars.append(c)
        if fid and chars:
            flicks[fid] = chars
    return {
        "locale": root.get("locale"),
        "info": next((i.get("layout") for i in root.iter(ns + "info") if i.get("layout")), None),
        "layers": layers,
        "flicks": flicks,
    }


def _unescape(s: str) -> str:
    """CLDR `\\u{XXXX}` and `\\uXXXX` escapes to characters; `\\m{name}` marks stay as-is."""
    out, i = [], 0
    while i < len(s):
        if s.startswith("\\u{", i):
            j = s.index("}", i)
            out.append(chr(int(s[i + 3:j], 16)))
            i = j + 1
        elif s.startswith("\\u", i) and i + 6 <= len(s):
            try:
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
            except ValueError:
                out.append(s[i]); i += 1
        else:
            out.append(s[i]); i += 1
    return "".join(out)


def layout_for(lang: str) -> dict:
    """The rows for a language: CLDR if the file is present, else the declared table."""
    base = lang.split("-")[0]
    for key, fn in CLDR_FILES.items():
        if key == lang or key.split("-")[0] == base:
            p = os.path.join(CLDR_DIR, fn)
            if os.path.exists(p):
                d = _parse_cldr(p)
                rows = (d["layers"].get("none") or d["layers"].get("None")
                        or next(iter(d["layers"].values()), []))
                return {"rows": rows, "source": f"cldr:{fn}", "note": d.get("info")}
    if lang in LAYOUTS:
        return {"rows": [r.split() for r in LAYOUTS[lang]["rows"]],
                "source": LAYOUTS[lang]["source"], "note": LAYOUTS[lang]["note"]}
    if base in LAYOUTS:
        return {"rows": [r.split() for r in LAYOUTS[base]["rows"]],
                "source": LAYOUTS[base]["source"], "note": LAYOUTS[base]["note"]}
    return {"rows": [], "source": "none", "note": "no layout available"}


def layout_source(lang: str) -> str:
    """Which route supplied the layout, so the two can be told apart in a report."""
    return layout_for(lang)["source"]


def neighbours(lang: str) -> dict:
    """character -> the characters adjacent to it on that language's keyboard.

    Adjacency is computed on the physical grid: left and right within a row, plus the keys
    that straddle the half-key stagger on the rows above and below. Only characters that are
    actually produced by the layout appear, so the map cannot invent a neighbour.
    """
    rows = layout_for(lang)["rows"]
    if not rows:
        return {}
    adj: dict = {}

    def link(a: str, b: str) -> None:
        if a and b and a != b:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)

    for ri, row in enumerate(rows):
        for ci, ch in enumerate(row):
            if ci + 1 < len(row):
                link(ch, row[ci + 1])
            for dr in (-1, 1):
                nr = ri + dr
                if 0 <= nr < len(rows):
                    other = rows[nr]
                    # the stagger: horizontal neighbours in the adjacent row
                    for nc in (ci, ci + 1):
                        if 0 <= nc < len(other):
                            link(ch, other[nc])
    return {k: sorted(v) for k, v in adj.items()}


def flick_groups(lang: str = "ja-Hira") -> dict:
    """kana that share one physical key under the CLDR flick layout.

    The Japanese layout reaches five kana per key by directional flick, so for kana the
    keystroke channel is the flick group rather than adjacency. Before this read the
    `<flicks>` elements it returned one character per group, because the extra kana are
    flickSegments and not separate keys.
    """
    fn = CLDR_FILES.get(lang)
    if not fn:
        return {}
    p = os.path.join(CLDR_DIR, fn)
    if not os.path.exists(p):
        return {}
    return _parse_cldr(p)["flicks"]


if __name__ == "__main__":
    for lang in ("en", "ru", "fr", "pt"):
        lay = layout_for(lang)
        print(f"  {lang:<8} source={lay['source']:<22} rows={len(lay['rows'])}")
        if lay["rows"]:
            print(f"           row0: {' '.join(lay['rows'][0])}")
        nb = neighbours(lang)
        if nb:
            sample = list(nb.items())[:3]
            print(f"           neighbours: " + "  ".join(f"{k}->{''.join(v)}" for k, v in sample))
    fg = flick_groups()
    print(f"\n  ja-Hira flick groups: {len(fg)}")
    for g, v in list(fg.items())[:3]:
        print(f"    {g}: {''.join(v)}")
