"""Produce the numeric profile of RRC for the Technical Report.

Every figure the report quotes comes from here, so the report has no hand-entered number and
the profile can be regenerated from the artefacts. Read from `config/rrc.json` and the arm
files; written to `data/processed/rrc_profile.json` and printed as a table.

The profile is deliberately descriptive: distributions, not summaries. A dataset whose arms
differ in unit, layer coverage and item count cannot be characterised by a total, and quoting
one would hide exactly the properties a reader needs.
"""
from __future__ import annotations

import collections
import json
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "config" / "rrc.json"
OUT = REPO / "data" / "processed" / "rrc_profile.json"


def pct(values, q):
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((len(s) - 1) * q))))
    return s[k]


def main() -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    arms = man["arms"]
    profile = {"dataset": man["dataset"], "version": man["version"],
               "seed": man["seed"], "n_options": man["n_options"],
               "total_items": man["total_items"], "arms": {}}

    print("RRC numeric profile")
    print("  version %s   seed %s   n_options %d   total %d items"
          % (man["version"], man["seed"], man["n_options"], man["total_items"]))
    print()
    print("  %-13s %8s %8s %8s %8s  %s"
          % ("arm", "items", "src rec", "state md", "root md", "layers"))
    print("  " + "-" * 78)

    for arm, m in arms.items():
        path = REPO / m["file"]
        if not path.exists():
            print("  %-13s (file missing: %s)" % (arm, m["file"]))
            continue
        sl, rl, margins, ratios, groups, ranks = [], [], [], [], [], []
        layers = collections.Counter()
        margin_layers = collections.Counter()
        n = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                it = json.loads(line)
                n += 1
                sl.append(len(it["state"]))
                rl.append(len(it["root"]))
                layers[it["layer"]] += 1
                lo, hi = sorted((len(it["state"]), len(it["root"])))
                if hi:
                    ratios.append(lo / hi)
                dif = it.get("difficulty") or {}
                # Only the layers where the margin is defined. L1 and L4 are not ranked, and
                # L2c's candidates are homophones by construction, so including their margins
                # would average in structural zeros and report a difficulty the arm does not
                # have -- which is exactly how the earlier version of this profile produced its
                # "margin median 0.0" for every non-English arm.
                if dif.get("margin_defined"):
                    mg = dif.get("margin")
                    if mg is not None:
                        margins.append(mg)
                        margin_layers[it["layer"]] += 1
                gs = dif.get("group_size")
                if gs:
                    groups.append(gs)
                gr = dif.get("group_rank")
                if gr:
                    ranks.append(gr)

        entry = {
            "language": m["language"],
            "source": m["corpus"],
            "n_items": n,
            "source_records": m.get("source_records"),
            "sha256": m.get("sha256"),
            "chance": m.get("chance"),
            "dropped": m.get("dropped"),
            "dropped_script": m.get("dropped_script"),
            "dropped_margin": m.get("dropped_margin"),
            "layers": dict(layers),
            "state_len": {"min": min(sl), "p25": pct(sl, .25), "median": statistics.median(sl),
                          "p75": pct(sl, .75), "max": max(sl)},
            "root_len": {"min": min(rl), "p25": pct(rl, .25), "median": statistics.median(rl),
                         "p75": pct(rl, .75), "max": max(rl)},
            "state_root_ratio_median": round(statistics.median(ratios), 3) if ratios else None,
            "state_root_ratio_min": round(min(ratios), 3) if ratios else None,
            "margin_median": round(statistics.median(margins), 4) if margins else None,
            "margin_positive_share": (round(sum(1 for v in margins if v > 0) / len(margins), 4)
                                      if margins else None),
            "margin_ranked_layers": dict(margin_layers),
            # The IME channel's difficulty: how many characters the channel offers for the
            # reading. This is the quantity a similarity margin cannot express for a layer whose
            # candidates are homophones by construction.
            "group_size_median": (round(statistics.median(groups), 1) if groups else None),
            "group_size_max": (max(groups) if groups else None),
            "group_size_n": len(groups),
            # The IME channel's difficulty distribution: the root's position when the channel's
            # candidates for that reading are ordered by corpus frequency, which is the order an
            # input method presents them in. Rank 1 is offered first and is nearly free to pick;
            # rank == group_size is offered last.
            "group_rank": ({
                "n": len(ranks),
                "min": min(ranks), "p25": pct(ranks, .25), "median": statistics.median(ranks),
                "p75": pct(ranks, .75), "max": max(ranks),
                "share_first": round(sum(1 for r in ranks if r <= 1) / len(ranks), 4),
                "share_last": round(sum(1 for r, g in zip(ranks, groups) if r == g)
                                    / len(ranks), 4),
            } if ranks else None),
        }
        profile["arms"][arm] = entry
        print("  %-13s %8d %8s %8.0f %8.0f  %s"
              % (arm, n, m.get("source_records"), statistics.median(sl),
                 statistics.median(rl), dict(layers)))

    print()
    print("  unit consistency -- the SAME check the quality-control suite applies, imported")
    print("  rather than reimplemented, because two implementations of one index are two")
    print("  instruments and their verdicts can disagree while both are 'correct'.")
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("rrc_qc", REPO / "scripts" / "rrc_qc.py")
        _qc = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_qc)
        _unit = getattr(_qc, "unit_consistency", None)
    except Exception:  # noqa: BLE001
        _unit = None
    if _unit is None:
        print("    [WARN] could not import the checker; unit verdict omitted rather than faked")
    else:
        for arm, e in profile["arms"].items():
            path = REPO / arms[arm]["file"]
            n = bad = 0
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    ok_u, _d = _unit(json.loads(line))
                    n += 1
                    if not ok_u:
                        bad += 1
            e["unit_violations"] = bad
            e["unit_checked"] = n
            print("    %s %-13s %d / %d violations"
                  % ("OK  " if bad == 0 else "FAIL", arm, bad, n))

    print()
    print("  difficulty -- on the ranked layers only (L2, L3del, L3), where the margin is")
    print("  defined; on the IME layer the equivalent is the size of the character group the")
    print("  channel offers for the reading, which a similarity margin cannot express.")
    for arm, e in profile["arms"].items():
        gs = ("  IME group_size median %s (max %s, n=%s)"
              % (e["group_size_median"], e["group_size_max"], e["group_size_n"])
              if e["group_size_median"] else "")
        print("    %-13s margin median %-8s positive %-8s ranked=%s%s"
              % (arm, e["margin_median"], e["margin_positive_share"],
                 e["margin_ranked_layers"] or "none", gs))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print()
    print("  wrote %s" % OUT)

    # Verdicts come from the quality-control suite's own checker (imported above), never from a
    # second implementation. The earlier version of this file ended by testing a length-ratio
    # band of its own invention and disagreed with the suite about the same arms.
    if _unit is not None:
        bad = [a for a, e in profile["arms"].items() if e.get("unit_violations")]
        print("  unit-consistency verdict: %s"
              % ("all arms clean" if not bad else "[WARN] violations in %s" % bad))
    else:
        print("  unit-consistency verdict: not available (checker could not be imported)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
