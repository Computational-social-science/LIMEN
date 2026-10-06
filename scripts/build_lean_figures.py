#!/usr/bin/env python
"""build_lean_figures.py -- figures for the machine-checked core, from data rather than from illustration.

WHY THESE FIGURES EXIST
    The three Stage 2 figures are empirical: they show what the noise did. Nothing in the manuscript showed
    the FORMALISATION - 27 theorems that the prose cites, the design justification for a pre-registered
    hypothesis among them, with no visual account of what they say or how they depend on one another. A
    reader could not see the shape of the proof or why the load-bearing theorem is load-bearing.

TWO FIGURES, AND NEITHER IS A SCHEMATIC
    fig4  the scale-free property MEASURED ON THE CONFIRMATORY RECORD: apply a family of strictly increasing
          rescalings to every confidence in the trial file, recompute the within-arm AUC and the
          absolute-threshold quantities, and watch which move. The theorem says the first cannot move; the
          figure shows the first not moving while the second moves a great deal. A drawing of two axes would
          have asserted this; measuring it on 13,692 real trials makes it evidence.
    fig5  the PROOF DEPENDENCY GRAPH, extracted from the Lean source by reading which theorems each proof
          invokes. Hand-drawn arrows would be a claim about the formalisation; parsed arrows are the
          formalisation's own structure.

NO VALUE IS TYPED IN THIS FILE. Every plotted number is computed here from the trial record or read from the
kernel's source.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# scienceplots registers its styles as an IMPORT SIDE EFFECT; without this the style name is unknown. The
# existing Stage 2 figure script does the same, and a missing import here failed exactly as loudly.
import scienceplots  # noqa: F401

plt.style.use(["science", "nature", "no-latex"])

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "viz" / "figures"
TRIALS = ROOT / "measurement" / "out" / "confirm_trials.jsonl"
LEAN_PHASE = ROOT.parent / "lean-nhb" / "NHB" / "PhaseI"

ACCENT, ACCENT2, ACCENT3 = "#1B6CA8", "#C45E11", "#2E8B57"
INK, MUTED = "#1a1a1a", "#6b7a8d"

plt.rcParams.update({
    "figure.dpi": 400, "savefig.dpi": 400, "font.size": 8,
    "axes.labelsize": 8, "axes.titlesize": 8.5, "legend.fontsize": 7,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    
})


# ────────────────────────────────────────────────────────────────────────────── figure 4

def auc_within(conf: np.ndarray, correct: np.ndarray) -> float:
    """P(confidence of a random correct trial > confidence of a random incorrect one), ties at 0.5."""
    c, e = conf[correct.astype(bool)], conf[~correct.astype(bool)]
    if len(c) == 0 or len(e) == 0:
        return float("nan")
    # rank-based, tie-aware: the Mann-Whitney form
    allv = np.concatenate([c, e])
    order = allv.argsort()
    ranks = np.empty(len(allv), float)
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks for ties
    _, inv, counts = np.unique(allv, return_inverse=True, return_counts=True)
    avg = {}
    start = 1
    for i, k in enumerate(counts):
        avg[i] = (start + start + k - 1) / 2
        start += k
    ranks = np.array([avg[i] for i in inv])
    r1 = ranks[:len(c)].sum()
    return (r1 - len(c) * (len(c) + 1) / 2) / (len(c) * len(e))


def load_trials(lam: float) -> tuple[np.ndarray, np.ndarray]:
    conf, corr = [], []
    with TRIALS.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if abs(r["lambda"] - lam) > 1e-9:
                continue
            conf.append(float(r["c"]))
            corr.append(1.0 - float(r["error"]))
    return np.array(conf), np.array(corr)


def figure4(lam: float = 0.18) -> pathlib.Path:
    conf, corr = load_trials(lam)
    if len(conf) == 0:
        raise SystemExit(f"no trials at lambda={lam} - the confirmatory record is not available")

    gammas = np.concatenate([np.linspace(0.35, 0.95, 7), np.linspace(1.05, 3.0, 12)])
    aucs, cov, acc = [], [], []
    for g in gammas:
        t = conf ** g                        # strictly increasing for every g > 0
        aucs.append(auc_within(t, corr))
        cov.append(float((t >= 0.90).mean()))
        acc.append(float(corr.mean()))

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.7))

    ax = axes[0]
    ax.plot(gammas, aucs, "o-", color=ACCENT, ms=3, lw=1.4, label="within-arm AUC")
    ax.axhline(aucs[0], color=MUTED, ls=":", lw=0.9)
    ax.set_xlabel("rescaling exponent $\\gamma$  in  $c \\mapsto c^{\\gamma}$")
    ax.set_ylabel("within-arm AUC")
    ax.set_ylim(min(aucs) - 0.05, max(aucs) + 0.05)
    spread = max(aucs) - min(aucs)
    ax.set_title("a  the estimand does not move", loc="left", color=ACCENT, fontweight="bold")
    ax.text(0.5, 0.08,
            f"flat across the family: spread {spread:.2e}\nscale-free, as the kernel proves",
            transform=ax.transAxes, ha="center", fontsize=6.6, color=ACCENT,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=ACCENT, lw=0.7))

    ax = axes[1]
    ax.plot(gammas, cov, "s-", color=ACCENT2, ms=3, lw=1.4, label="coverage at $\\tau=0.90$")
    ax.plot(gammas, acc, "^-", color=ACCENT3, ms=3, lw=1.4, label="accuracy (unchanged, as it must be)")
    ax.set_xlabel("rescaling exponent $\\gamma$  in  $c \\mapsto c^{\\gamma}$")
    ax.set_ylabel("proportion")
    ax.set_ylim(0, max(max(cov), max(acc)) * 1.25)
    ax.set_title("b  the threshold quantities do", loc="left", color=ACCENT2, fontweight="bold")
    ax.legend(frameon=False, loc="center right", fontsize=6.4)
    ax.text(0.5, 0.08,
            f"coverage moves by {100 * (max(cov) - min(cov)):.1f} points\nunder the SAME family",
            transform=ax.transAxes, ha="center", fontsize=6.6, color=ACCENT2,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=ACCENT2, lw=0.7))

    fig.suptitle(
        "The scale-free property, measured on the confirmatory record "
        f"($\\lambda$ = {lam}, n = {len(conf):,} trials)", fontsize=8.5, y=1.04)
    fig.tight_layout()
    p = write_formats(fig, "fig4_stage2_scale_free")
    plt.close(fig)

    print(f"  fig4: AUC spread {spread:.3e} across gamma in [{gammas.min():.2f}, {gammas.max():.2f}]")
    print(f"        coverage {min(cov):.4f} -> {max(cov):.4f}  (moves {100*(max(cov)-min(cov)):.2f} points)")
    print(f"        accuracy constant at {acc[0]:.4f} (a monotone map cannot reorder accuracy)")
    return p


# ────────────────────────────────────────────────────────────────────────────── figure 5

DECL = re.compile(r"^(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_']*)", re.M)


def lean_dependencies(path: pathlib.Path) -> dict[str, set[str]]:
    """For each theorem, which OTHER theorems of the same file its proof invokes.

    Read from the source by slicing each declaration up to the next one, so the graph is the file's own
    structure rather than a transcription of the author's mental model of it.
    """
    text = path.read_text(encoding="utf-8")
    marks = [(m.start(), m.group(1)) for m in DECL.finditer(text)]
    names = {n for _, n in marks}
    edges: dict[str, set[str]] = {}
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        body = text[pos:end]
        edges[name] = {n for n in names if n != name and re.search(rf"\b{re.escape(n)}\b", body)}
    return edges


def figure5() -> pathlib.Path:
    files = sorted(p for p in LEAN_PHASE.glob("*.lean") if not p.name.startswith("__"))
    edges: dict[str, set[str]] = {}
    origin: dict[str, str] = {}
    for f in files:
        e = lean_dependencies(f)
        edges.update(e)
        for n in e:
            origin[n] = f.stem

    # layer by longest-path depth so arrows point consistently downward
    depth: dict[str, int] = {}

    def d(n: str, seen: frozenset = frozenset()) -> int:
        if n in depth:
            return depth[n]
        if n in seen:
            return 0
        dep = [d(x, seen | {n}) for x in edges.get(n, ())] or [0]
        depth[n] = 1 + max(dep)
        return depth[n]

    for n in edges:
        d(n)
    layers: dict[int, list[str]] = defaultdict(list)
    for n, k in depth.items():
        layers[k].append(n)

    n_tot = len(edges)
    n_edges = sum(len(v) for v in edges.values())
    fig, ax = plt.subplots(figsize=(7.16, 4.5))
    pos: dict[str, tuple[float, float]] = {}
    for k in sorted(layers):
        for j, n in enumerate(sorted(layers[k])):
            pos[n] = (j - (len(layers[k]) - 1) / 2, -k)

    for n, deps in edges.items():
        for x in deps:
            if x in pos:
                ax.annotate("", xy=pos[x], xytext=pos[n],
                            arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.5,
                                            shrinkA=2, shrinkB=2, alpha=0.55))

    for n, (x, y) in pos.items():
        colour = ACCENT if origin[n] == "ScaleFree" else (ACCENT2 if depth[n] <= 1 else INK)
        ax.text(x, y, n, ha="center", va="center", fontsize=5.6, color=colour,
                bbox=dict(boxstyle="round,pad=0.22",
                          fc="#eef4fb" if origin[n] == "ScaleFree" else "white",
                          ec=colour, lw=0.6))
    ax.set_xlim(-max(len(v) for v in layers.values()) / 2 - 1, max(len(v) for v in layers.values()) / 2 + 1)
    ax.set_ylim(-max(layers) - 0.8, 0.8)
    ax.axis("off")
    ax.set_title("The proof dependency graph, parsed from the kernel source", loc="left",
                 fontsize=8.5, fontweight="bold")
    ax.text(0.0, -max(layers) - 1.6,
            f"{n_tot} theorems, {n_edges} invocations among them · arrows point from a proof to the "
            f"results it uses · blue = the scale-free module (no axioms at all)",
            fontsize=6.2, color=MUTED, ha="center")
    fig.tight_layout()
    p = write_formats(fig, "fig5_stage2_proof_graph")
    plt.close(fig)
    print(f"  fig5: {n_tot} theorems, {n_edges} dependency edges, {max(layers) + 1} layers")
    roots = sorted(n for n in edges if not edges[n])
    print(f"        premises (no dependencies): {len(roots)}")
    return p


def write_formats(fig, stem: str) -> pathlib.Path:
    """All four formats the journal needs, at 600 dpi - the same convention as the Stage 2 figures.

    TIFF is LZW-compressed because an uncompressed 600-dpi raster is rejected by most submission systems on
    size alone, and JPG drops to 300 dpi because JPEG is not the format the 600-dpi requirement is for.
    """
    for tag in ("png", "jpg", "svg", "tiff"):
        kw = {}
        if tag == "jpg":
            kw["dpi"] = 300
        if tag == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(OUT / f"{stem}.{tag}", dpi=kw.pop("dpi", 600), bbox_inches="tight", **kw)
    return OUT / f"{stem}.png"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--lambda", dest="lam", type=float, default=0.18)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"  writing to {OUT.relative_to(ROOT)}")
    figure4(args.lam)
    figure5()
    return 0


if __name__ == "__main__":
    sys.exit(main())