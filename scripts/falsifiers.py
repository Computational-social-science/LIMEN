"""The falsifiers: turning declared falsifiability into an executable test.

A claim of falsifiability is worth nothing until the test is written down, with its criterion
fixed before the numbers arrive. This module defines each falsifier from the framework (the
technical report, sections 2 and 5) as a function with an explicit acceptance region, and runs
the ones that need no model output.

F1  ranked-layer separation. On the layers where the margin is defined, a model's confidence
    must separate its correct from its incorrect answers by more than the margin already
    predicts. Requires model output; the criterion is fixed here so it cannot be chosen after
    seeing the result.

F2  reading-channel rank effect. On the reading channel, difficulty is the root's frequency
    rank (the margin is identically zero there, by the proposition in section 2.4). The
    falsifier is that accuracy at rank 1 equals accuracy at rank n; if the channel's own
    ordering carries no difficulty, the layer is uninformative rather than hard. Requires model
    output.

F3  layer-coverage explanation. The arms do not carry the same layers, so any cross-script
    difference must survive restricting to layers both arms contain. This one is a property of
    the corpus and is executable now: it reports, for every pair of arms, which layers they
    share and how many items fall in the shared set.
"""
import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO / "config" / "rrc.json"


def load() -> dict:
    if not MANIFEST.exists():
        raise SystemExit("manifest absent: run scripts/build_rrc.py first")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def f3_layer_coverage(man: dict) -> dict:
    """For each arm pair, the shared layers and the items comparable within them."""
    arms = man["arms"]
    per = {a: collections.Counter(e.get("per_layer") or {}) for a, e in arms.items()}
    out = {}
    keys = list(per)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            shared = sorted(set(per[a]) & set(per[b]))
            n_shared = sum(per[a][l] for l in shared)
            n_shared_b = sum(per[b][l] for l in shared)
            out[f"{a}|{b}"] = {
                "shared_layers": shared,
                "n_shared_a": n_shared,
                "n_shared_b": n_shared_b,
                "n_total_a": sum(per[a].values()),
                "n_total_b": sum(per[b].values()),
                "share_a": round(n_shared / max(1, sum(per[a].values())), 4),
                "share_b": round(n_shared_b / max(1, sum(per[b].values())), 4),
            }
    return out


def main() -> int:
    man = load()
    arms = man["arms"]
    print("RRC falsifier analysis")
    print("  version %s  |  %d arms  |  %s items"
          % (man["version"], len(arms), f"{man['total_items']:,}"))

    print()
    print("F3  layer-coverage confound  (executable now; needs no model output)")
    print("    The arms do not carry the same layers, so any cross-script difference has to")
    print("    survive restricting to the layers both arms contain. Below is, for every pair,")
    print("    what that shared set is and how much of each arm it accounts for.")
    print("    ACCEPTANCE: a cross-arm claim is admissible only on the shared layers, and only")
    print("    where the shared share is substantial in BOTH arms; otherwise the difference")
    print("    is a coverage artefact and must be reported as one.")
    cov = f3_layer_coverage(man)
    pairs = sorted(cov.items(), key=lambda kv: -min(kv[1]["share_a"], kv[1]["share_b"]))
    for key, v in pairs:
        worst = min(v["share_a"], v["share_b"])
        verdict = "admissible" if worst >= 0.50 else ("thin" if worst >= 0.20 else "NOT comparable")
        print("    %-26s shared=%-18s a %5.1f%%  b %5.1f%%   %s"
              % (key, ",".join(v["shared_layers"]) or "none",
                 100 * v["share_a"], 100 * v["share_b"], verdict))

    no_overlap = [k for k, v in cov.items() if not v["shared_layers"]]
    print()
    print("    pairs with NO shared layer: %d of %d" % (len(no_overlap), len(cov)))
    if no_overlap:
        for k in no_overlap:
            print("      %s" % k)

    print()
    print("F1  ranked-layer separation  (criterion fixed; needs model output)")
    ranked = {a: sum((e.get("per_layer") or {}).get(l, 0)
                     for l in ("L2", "L3del", "L3"))
              for a, e in arms.items()}
    print("    items on ranked layers, per arm: %s"
          % {a: n for a, n in ranked.items() if n})
    print("    ACCEPTANCE: on these layers, a model's confidence must separate correct from")
    print("    incorrect answers by more than the margin predicts. Concretely, at matched")
    print("    margin, the error rate must fall as confidence rises; if it does not, the")
    print("    claim that depth governs the visibility of error is not supported here.")

    print()
    print("F2  reading-channel rank effect  (criterion fixed; needs model output)")
    ime = {a: (e.get("per_layer") or {}).get("L2c", 0) for a, e in arms.items()}
    print("    items on the reading channel, per arm: %s"
          % {a: n for a, n in ime.items() if n})
    print("    The margin is identically zero on this layer (proposition, section 2.4), so")
    print("    difficulty is the frequency rank and nothing else. ACCEPTANCE: accuracy at")
    print("    rank 1 must exceed accuracy at rank n. Equality means the channel's own")
    print("    ordering carries no difficulty and the layer is uninformative, not hard.")

    out = REPO / "data" / "processed" / "falsifier_f3_coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "version": man["version"],
        "n_arms": len(arms),
        "pairs": cov,
        "pairs_with_no_shared_layer": no_overlap,
        "ranked_layer_items": ranked,
        "reading_channel_items": ime,
    }, indent=2), encoding="utf-8")
    print()
    print("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
