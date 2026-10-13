"""Export the dashboard state for the RRC Technical Report.

Follows the local-file-dashboard rules, because the report is opened by double-clicking a
file rather than served:

  * the state is shipped as a JS global via `<script src="...">`, never fetched. `fetch()` is
    blocked on `file://` and a dashboard that falls back to remembered numbers is worse than a
    blank one, so there is no fallback here at all: if the state is missing the report says so;
  * every figure is read from an artefact (`config/rrc.json`, the arm files, the profile and
    the quality-control output), so no number in the report is hand-entered;
  * the source file mtimes and a generation timestamp travel with the state, so a reader can
    see how old the numbers are.

Written to `viz/report/state.js` beside the report.
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import statistics
import sys
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "config" / "rrc.json"
PROFILE = REPO / "data" / "processed" / "rrc_profile.json"
CHANNEL = REPO / "data" / "processed" / "keystroke_channel.json"
DATASETS = REPO / "config" / "datasets.json"
INSTRUMENTS = REPO / "config" / "instruments.json"
MEASUREMENT = REPO / "measurement" / "out" / "measurement_report.json"
OUT_DIR = REPO / "viz" / "report"
OUT = OUT_DIR / "state.js"


def _ladder(vals):
    """The five-number summary the report's length table renders: min, p25, median, p75, max.

    A shape contract, not a convenience. The table asks for `state_len.{min,p25,median,p75,max}`
    and this file used to emit `state_median`/`state_max` instead -- a shape nothing reads. The
    mismatch was invisible until the page was actually loaded, because every check in the suite
    inspected the exporter's source or the report's source and none compared the two.

    Quartiles use the nearest-rank method on the sorted list rather than an interpolation: the arms'
    states are integers (token counts), and a fraction token is not a length anyone can read.
    """
    if not vals:
        return None
    v = sorted(vals)
    n = len(v)

    def q(p):
        return v[min(n - 1, max(0, int(round(p * (n - 1)))))]

    return {"min": v[0], "p25": q(0.25), "median": statistics.median(v), "p75": q(0.75), "max": v[-1]}


def mtime(p: pathlib.Path):
    if not p.exists():
        return None
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))


def pct(v, q):
    if not v:
        return None
    s = sorted(v)
    return s[max(0, min(len(s) - 1, int(round((len(s) - 1) * q))))]


def main() -> int:
    if not MANIFEST.exists():
        print("  [FAIL] manifest absent: %s -- run scripts/build_rrc.py first" % MANIFEST)
        return 1
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))

    arms = {}
    # The unit verdict comes from the quality-control suite's own checker, imported, so the
    # dashboard and the QC run cannot disagree about the same index -- they are one
    # implementation. An earlier version of the report page carried a length-ratio band of its
    # own invention and reported violations on arms the QC called clean.
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("rrc_qc", REPO / "scripts" / "rrc_qc.py")
        _qc = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_qc)
        _unit = getattr(_qc, "unit_consistency", None)
    except Exception:  # noqa: BLE001
        _unit = None

    for arm, m in man["arms"].items():
        path = REPO / m["file"]
        sl, rl, margins, ratios, groups, ranks = [], [], [], [], [], []
        layers = collections.Counter()
        margin_layers = collections.Counter()
        unit_bad = 0
        n = 0
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    it = json.loads(line)
                    n += 1
                    sl.append(len(it["state"]))
                    rl.append(len(it["root"]))
                    layers[it["layer"]] += 1
                    a, b = sorted((len(it["state"]), len(it["root"])))
                    if b:
                        ratios.append(a / b)
                    dif = it.get("difficulty") or {}
                    # only the layers where the margin is defined; elsewhere it is structurally
                    # absent (unranked layers) or degenerate (homophones by construction)
                    if dif.get("margin_defined") and dif.get("margin") is not None:
                        margins.append(dif["margin"])
                        margin_layers[it["layer"]] += 1
                    gs = dif.get("group_size")
                    if gs:
                        groups.append(gs)
                    gr = dif.get("group_rank")
                    if gr:
                        ranks.append(gr)
                    if _unit is not None:
                        _ok, _d = _unit(it)
                        if not _ok:
                            unit_bad += 1
        arms[arm] = {
            "language": m["language"],
            "source": m["corpus"],
            "n_items": n,
            "source_records": m.get("source_records"),
            "dropped": m.get("dropped"),
            "dropped_script": m.get("dropped_script"),
            "dropped_margin": m.get("dropped_margin"),
            "dropped_duplicate": m.get("dropped_duplicate"),
            "dropped_unit": m.get("dropped_unit"),
            # The record-level stage that was counted nowhere until the funnel was drawn: records
            # that cleared both record gates and then yielded no layer at all. `records_with_layer`
            # is its complement among the kept records, and `items_attempted` is the denominator the
            # margin drop is a fraction OF -- without it, "110 margin drops" has no base.
            "dropped_no_layer": m.get("dropped_no_layer"),
            "records_with_layer": m.get("records_with_layer"),
            "items_attempted": m.get("items_attempted"),
            "layer_offered": m.get("layer_offered"),
            "sha256": (m.get("sha256") or "")[:12],
            "file_mtime": mtime(path),
            "layers": dict(layers),
            # THE LADDER THE RENDERER READS, NOT A PAIR OF FLAT FIELDS. This emitted `state_median`
            # and `state_max`, a shape the report never reads, while the report's length table asks
            # for `state_len.{min,p25,median,p75,max}`. `a.state_len` was therefore undefined on every
            # arm, `a.state_len.min` threw inside an Array.map, and the exception aborted the page's
            # single IIFE -- so sections 4.4 through 8, including the entire reference list, rendered
            # nothing. The report is written with one script for the whole page, so an undefined field
            # anywhere costs every section after it, which is why the shape has to be agreed rather
            # than assumed and why the render check exists.
            "state_len": _ladder(sl),
            "root_median": statistics.median(rl) if rl else None,
            "root_max": max(rl) if rl else None,
            "margin_median": (round(statistics.median(margins), 4) if margins else None),
            "margin_positive_share": (sum(1 for v in margins if v > 0) / len(margins)
                                      if margins else None),
            "margin_ranked_layers": dict(margin_layers),
            "group_size_median": (round(statistics.median(groups), 1) if groups else None),
            "group_size_max": (max(groups) if groups else None),
            "group_size_n": len(groups),
            "group_rank": ({
                "n": len(ranks),
                "min": min(ranks), "p25": pct(ranks, .25),
                "median": statistics.median(ranks), "p75": pct(ranks, .75),
                "max": max(ranks),
                "share_first": round(sum(1 for r in ranks if r <= 1) / len(ranks), 4),
                "share_last": round(sum(1 for r, g in zip(ranks, groups) if r == g)
                                    / len(ranks), 4),
            } if ranks else None),
            "unit_ratio_min": (round(min(ratios), 3) if ratios else None),
            "unit_ratio_median": (round(statistics.median(ratios), 3) if ratios else None),
            "unit_violations": (unit_bad if _unit is not None else None),
        }

    total = sum(a["n_items"] for a in arms.values())
    channel = json.loads(CHANNEL.read_text(encoding="utf-8")) if CHANNEL.exists() else {}
    datasets = json.loads(DATASETS.read_text(encoding="utf-8")) if DATASETS.exists() else {}

    # Every source, read from the provenance registry rather than restated here.
    #
    # The registry is keyed by SOURCE, not by channel. Three of the six arms draw on one release
    # (the GitHub Typo Corpus), so a per-channel record listed three corpora and silently omitted
    # the largest single source in the dataset. The report's sources section iterates this list,
    # which is why the omission was visible as "too few sources" rather than as a wrong number.
    sources = {}
    for s in (datasets.get("sources") or []):
        sid = s.get("id")
        if not sid:
            continue
        sources[sid] = {
            "name": s.get("name"),
            "kind": s.get("kind"),
            "arms": s.get("arms") or [],
            "compiler": s.get("compiler"),
            "provenance": s.get("provenance"),
            "what": s.get("what_it_is"),
            "citation": s.get("citation"),
            "licence": s.get("licence"),
            "caveat": s.get("caveat"),
            "verification": s.get("verification"),
            "note": s.get("note"),
        }
    # the registry's own list of what it turned down, kept whole rather than per channel
    if datasets.get("rejected"):
        sources["__rejected__"] = {
            "name": "Rejected alternatives",
            "kind": "rejected",
            "arms": [],
            "provenance": "n/a",
            "what": ("sources considered and not used. A corpus is defined as much by what it "
                     "excludes, and a rejection without its reason is an omission."),
            "rejected": [{"name": r.get("name"), "reason": r.get("reason")}
                         for r in datasets["rejected"]],
        }

    edits = channel.get("edits") or {}
    etot = channel.get("edits_total") or 0

    # The instrument list, derived from the imports in scripts/ rather than written by hand.
    instruments = {}
    if INSTRUMENTS.exists():
        instruments = json.loads(INSTRUMENTS.read_text(encoding="utf-8"))

    # The d1-3B measurement, reduced by scripts/analyze_measurement.py. Read rather than
    # transcribed, so a sentence in the report cannot disagree with the rows it describes.
    #
    # TWO artefacts are merged because the two sampling schemes answer different questions and
    # neither alone answers both. The by-state scheme samples whole states, so a paired layer
    # contrast is possible; the per-rank scheme samples a quota per rank value, so the rank curve is
    # balanced instead of following whatever the corpus happens to contain, where rank 1 was ~20 %
    # of the layer and the tail a handful. Reading one and calling it the measurement would misstate
    # the other.
    #
    # Which scheme is AUTHORITATIVE for which field. Not first-non-empty: each scheme samples a
    # different unit, so each is the right instrument for a different quantity, and a generic
    # "whatever came first" rule picked the by-state rank curve -- which is unbalanced (rank 1 is
    # ~20 % of the layer and the tail a handful) and therefore the weaker instrument for the rank
    # question. Measured: the by-state artefact's paired contrast has n=392 per arm, and the
    # per-rank artefact's has n=42, and vice versa for the curve.
    FIELD_SOURCE = {
        # the balanced scheme, applied identically to BOTH channels' difficulty quantity, is the
        # fair instrument for every cross-arm comparison: the per-rank run sampled the reading
        # channel at a quota per rank value while the ranked layers were left on the corpus's own
        # distribution, so comparing those two curves compared the schemes as much as the channels.
        "f2_rank_effect": "measurement_report_bal.json",
        "candidate_preference": "measurement_report_bal.json",
        "state_displacement": "measurement_report_bal.json",
        "position_diagnostic": "measurement_report_bal.json",
        "margin_effect": "measurement_report_bal.json",
        "accuracy": "measurement_report_bal.json",
        "p_root": "measurement_report_bal.json",
        "rate": "measurement_report_bal.json",
        # the paired layer contrast is the one quantity the balanced scheme measures WORSE: sampling
        # a quota per difficulty value spreads the items, so few states carry both layers. The
        # by-state run sampled whole states, giving n=392 per arm against 39 here.
        "paired_ranked_vs_L4": "measurement_report_bs.json",
        "L4_to_L1_drop": "measurement_report_bs.json",
        "cross_arm_L4": "measurement_report_bs.json",
    }
    measurement = {}
    pool = {}
    for name in ("measurement_report_bal.json", "measurement_report_bs.json",
                 "measurement_report_rk.json", "measurement_report.json"):
        cand = MEASUREMENT.parent / name
        if not cand.exists():
            continue
        try:
            pool[name] = json.loads(cand.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
    # start from the balanced artefact (it carries all six arms under one scheme), then overwrite
    # each field from the scheme that is authoritative for it, recording where each came from
    base = (pool.get("measurement_report_bal.json")
            or pool.get("measurement_report_bs.json")
            or next(iter(pool.values()), {}))
    measurement = dict(base)
    measurement["_source_file"] = ("measurement_report_bal.json"
                                   if "measurement_report_bal.json" in pool else
                                   "measurement_report_bs.json"
                                   if "measurement_report_bs.json" in pool else "")
    for key, src in FIELD_SOURCE.items():
        if src in pool and pool[src].get(key):
            measurement[key] = pool[src][key]
            measurement["_from_" + key] = src
    measurement["_sources"] = sorted(pool)
    state = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "generated_epoch": int(time.time()),
        "dataset": {
            "name": man.get("dataset"),
            "version": man.get("version"),
            "built_utc": man.get("built_utc"),
            "seed": man.get("seed"),
            "n_options": man.get("n_options"),
            "total_items": total,
            "question_form": man.get("question_form"),
            "decoy_rule": man.get("decoy_rule"),
            "validity_constraint": man.get("validity_constraint"),
            "provenance_kind": man.get("provenance_kind"),
            "known_limitations": man.get("known_limitations") or [],
        },
        "arms": arms,
        "arm_order": list(arms),
        "sources": sources,
        "instruments": instruments,
        "measurement": measurement,
        "channel": {
            "source": channel.get("source"),
            "method": channel.get("method"),
            # Two rates that are NOT the same quantity, named for what they are. The validation in
            # figure 4.6(a) compares the ALL-EDITS rate against the publisher's, because that is
            # what the publisher's number counts. `substitution_rate` counts only the substitution
            # class and is about a third of it. An earlier version exposed the substitution rate
            # under the name `measured_rate`, which invites exactly the wrong comparison -- 0.395 %
            # against 1.167 % reads as 0.34x when the match is 1.02x on the right quantity.
            "edits_rate": ((channel.get("edits_total") or 0) / channel["target_chars"]
                           if channel.get("target_chars") else None),
            "substitution_rate": channel.get("substitution_rate"),
            "substitution_fraction_of_edits": channel.get("substitution_fraction_of_edits"),
            "published_rate": channel.get("published_rate"),
            "rate_basis": ("all edit operations over target characters; this is the quantity the "
                           "published rate counts, and the one the validation compares"),
            "substitution_rate_basis": ("substitution operations only; about a third of the "
                                        "all-edits rate and NOT comparable with the published one"),
            "edits_total": etot,
            "target_chars": channel.get("target_chars"),
            "classes": [{"name": k, "n": edits.get(k, 0),
                         "share": (edits.get(k, 0) / etot) if etot else 0.0}
                        for k in ("delete", "insert", "shift_state",
                                  "key_adjacency", "other_substitution")],
            "top_substitutions": channel.get("top_substitutions") or [],
        },
        "mtimes": {
            "config/rrc.json": mtime(MANIFEST),
            "config/datasets.json": mtime(DATASETS),
            "data/processed/keystroke_channel.json": mtime(CHANNEL),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text("window.APP_STATE = " + payload + ";\n", encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    print("  arms            : %d" % len(arms))
    print("  total items     : %d" % total)
    print("  channel classes : %s" % ", ".join(
        "%s %.1f%%" % (c["name"], 100 * c["share"]) for c in state["channel"]["classes"]))
    print("  state sha256    : %s" % digest)
    print("  wrote %s (%d bytes)" % (OUT, OUT.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
