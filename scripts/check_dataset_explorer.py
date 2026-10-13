"""Assert the dataset explorer actually DREW, by counting marks in the live DOM.

WHY A RENDER GUARD AND NOT A SOURCE CHECK. A syntax check on dataset_explorer.js proves the file
parses; a structure check on the HTML proves the containers exist. Neither proves a single mark was
drawn. The failure this guards against is a view that loads, throws nothing the page reports as an
error, and leaves the reader an empty card -- which every source-level check passes. So this guard
loads the built page in a browser and counts the marks the drawing code is supposed to have appended,
each group carrying `data-d3-marks` with its own count.

The three views and what each must contain:
  a  #dx-funnel   six gates minimum, one bar per stage surviving, for the selected arm
  b  #dx-layers   one cell per (arm, layer) pair -- six arms x the union of layers
  c  #dx-stats    one bar per arm

NEGATIVE CONTROL. With the state removed the views must refuse to draw and say so. A page that draws
a plausible-looking chart from absent data is worse than one that draws nothing, so the control
asserts the refusal path fires; if it does not, this guard would certify fabrication as success.
"""

import pathlib
import re
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
REPORT = REPO / "viz" / "report" / "technical-report.html"

VIEWS = {
    "dx-funnel": 6,   # six or more stages in the filtration
    "dx-layers": 12,  # at least 12 cells (6 arms x >=2 layers)
    "dx-stats": 5,    # at least 5 arms with a value drawn
}


def render(page, url, errs):
    page.goto(url, wait_until="load")
    page.wait_for_timeout(900)  # let the explorer's synchronous draw finish
    out = {}
    for host, floor in VIEWS.items():
        info = page.evaluate(
            """(host) => {
                const h = document.getElementById(host);
                if (!h) return {missing: true};
                const svgs = h.querySelectorAll('svg');
                const g = h.querySelector('g[data-d3-marks]');
                return {
                    svgs: svgs.length,
                    marks: g ? parseInt(g.getAttribute('data-d3-marks'), 10) : null,
                    err: h.getAttribute('data-d3-error'),
                    bars: h.querySelectorAll('rect.dx-bar, rect.dx-cell').length,
                };
            }""",
            host,
        )
        out[host] = info
    #  The item browser draws buttons rather than SVG marks, so it is asserted on its own attributes:
    #  the candidate count actually rendered, the arm tabs built, and the size of the filtered set.
    out["ib"] = page.evaluate("""() => {
        const h = document.getElementById('ib-stage');
        if (!h) return {missing: true};
        const m = h.querySelector('[data-ib-marks]');
        return {
            err: h.getAttribute('data-ib-error'),
            items: parseInt(h.getAttribute('data-ib-items') || '0', 10),
            marks: m ? parseInt(m.getAttribute('data-ib-marks'), 10) : null,
            cands: h.querySelectorAll('button.ib-cand').length,
            tabs: document.querySelectorAll('#ib-tabs button').length,
        };
    }""")
    out["pageerrors"] = list(errs)
    return out


def check(res, tol_floor):
    bad = []
    for host, floor in tol_floor.items():
        i = res[host]
        if i.get("missing"):
            bad.append("%s: container absent" % host); continue
        if i.get("err"):
            bad.append("%s: refused to draw (%s)" % (host, i["err"])); continue
        if not i.get("svgs"):
            bad.append("%s: no svg element" % host); continue
        m = i.get("marks")
        if m is None:
            bad.append("%s: drew an svg with no data-d3-marks group" % host); continue
        if m < floor:
            bad.append("%s: %d marks, expected at least %d" % (host, m, floor)); continue
        if i.get("bars", 0) < floor:
            bad.append("%s: %d drawn rects, expected at least %d" % (host, i["bars"], floor))
    ib = res.get("ib") or {}
    if ib.get("missing"):
        bad.append("ib-stage: container absent")
    elif ib.get("err"):
        bad.append("item browser refused to draw: %s" % ib["err"])
    else:
        if (ib.get("tabs") or 0) < 2:
            bad.append("item browser: %s arm tabs, expected at least 2" % ib.get("tabs"))
        if (ib.get("items") or 0) < 1:
            bad.append("item browser: no items in the filtered view")
        if (ib.get("cands") or 0) < 2 or (ib.get("marks") or 0) < 2:
            bad.append("item browser: %s candidate buttons (%s marks), expected at least 2"
                       % (ib.get("cands"), ib.get("marks")))
    if res["pageerrors"]:
        bad.append("page errors: %s" % "; ".join(res["pageerrors"][:2]))
    return bad


def main():
    if not REPORT.exists():
        print("  [FAIL] report not found: %s" % REPORT); return 1
    from playwright.sync_api import sync_playwright

    url = REPORT.resolve().as_uri()
    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome")
        page = br.new_page(viewport={"width": 1280, "height": 1000})
        # NOT `page.page_errors`: Playwright exposes that name as a METHOD on Page, so binding a list
        # to it shadows a real API and the collected errors read back as a bound method, not strings.
        # Our own list, passed explicitly, cannot collide with the library's surface.
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        res = render(page, url, errors)
        bad = check(res, VIEWS)

        print("  view a  funnel : svg=%d  marks=%s  rects=%d" %
              (res["dx-funnel"].get("svgs", 0), res["dx-funnel"].get("marks"),
               res["dx-funnel"].get("bars", 0)))
        print("  view b  layers : svg=%d  marks=%s  rects=%d" %
              (res["dx-layers"].get("svgs", 0), res["dx-layers"].get("marks"),
               res["dx-layers"].get("bars", 0)))
        print("  view c  stats  : svg=%d  marks=%s  rects=%d" %
              (res["dx-stats"].get("svgs", 0), res["dx-stats"].get("marks"),
               res["dx-stats"].get("bars", 0)))

        ib = res.get("ib") or {}
        print("  item browser   : tabs=%s  candidates=%s  marks=%s  items in view=%s  err=%s" %
              (ib.get("tabs"), ib.get("cands"), ib.get("marks"), ib.get("items"),
               (ib.get("err") or "none")))

        if "--negative-test" in sys.argv:
            # Serve the report with no state: every view must refuse.
            with tempfile.TemporaryDirectory() as td:
                td = pathlib.Path(td)
                html = REPORT.read_text(encoding="utf-8")
                html = html.replace('<script src="state.js"></script>', "")
                #  EVERY asset the page loads must be copied EXCEPT samples.js, so the item browser
                #  is loaded and can be OBSERVED refusing. Copying only the first two left
                #  item_browser.js absent, so the browser never ran, never set its error attribute,
                #  and the control passed without testing it -- a false green inside the check whose
                #  whole purpose is catching false greens.
                for asset in ("report.js", "dataset_explorer.js", "item_browser.js"):
                    src = REPORT.parent / asset
                    if src.exists():
                        (td / asset).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                vdir = td / "vendor"; vdir.mkdir(exist_ok=True)
                for v in (REPORT.parent / "vendor").glob("*.js"):
                    (vdir / v.name).write_text(v.read_text(encoding="utf-8"), encoding="utf-8")
                (td / "probe.html").write_text(html, encoding="utf-8")

                nude = br.new_page(viewport={"width": 1280, "height": 1000})
                errors2 = []
                nude.on("pageerror", lambda e: errors2.append(str(e)))
                res2 = render(nude, (td / "probe.html").as_uri(), errors2)
                refused = [h for h in VIEWS if res2[h].get("err")]
                if (res2.get("ib") or {}).get("err"):
                    refused.append("ib-stage")
                if (res2.get("ib") or {}).get("cands"):
                    print("  [FAIL] item browser drew candidates with no sample loaded")
                    br.close(); return 1
                drew = [h for h in VIEWS if res2[h].get("marks")]
                print("  negative control: refused=%d/%d hosts  drew-anyway=%d"
                      % (len(refused), len(VIEWS) + 1, len(drew)))
                for h in VIEWS:
                    e = res2[h].get("err")
                    print("    %-10s %s" % (h, ("REFUSED: " + e[:64]) if e else "drew marks=%s" % res2[h].get("marks")))
                # The control passes only if the refusal path fired AND nothing was drawn.
                #  FOUR hosts must refuse: the three d3 views and the item browser. Comparing against
                #  len(VIEWS) alone ignores the browser that was just appended, so a fully-correct
                #  refusal reads as a failure.
                if len(refused) == len(VIEWS) + 1 and not drew:
                    print("  [OK] negative control fires: with no state every view refuses and draws nothing")
                    br.close(); return 0
                print("  [FAIL] negative control did not fire -- views drew without state")
                br.close(); return 1

        br.close()

    if bad:
        print("  [FAIL] %d finding(s):" % len(bad))
        for b in bad:
            print("      %s" % b)
        return 1
    print("  [OK] all three views drew: every mark group is present with at least the expected "
          "number of rects, and the page reported no error")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
