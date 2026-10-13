"""verify_reference_urls.py -- a reference's URL must lead to the work it names.

WHY THIS EXISTS. The reference list carried the entry "Kernighan, Church & Gale (1990), A Spelling
Correction Program Based on a Noisy Channel Model" with the URL https://aclanthology.org/C90-2030/.
That address serves a different paper. Nothing in this project could see it: check_citation_links.py
proves a citation resolves to an ENTRY, and its resolution says nothing about whether the entry's
contents are true. The ID had been written from memory and the page range invented alongside it.

So this checks the one remaining unverified link: fetch the address and require the page to identify
itself as the work the entry names.

TWO CLASSES OF ADDRESS, TREATED DIFFERENTLY ON PURPOSE
  * scholarly: aclanthology.org, arxiv.org, doi.org, proceedings.mlr.press, and publisher DOIs. The
    page must carry a title, and that title's significant words must appear in the entry's own text.
    A mismatch fails.
  * resource: standards and model repositories (cldr.unicode.org, unicode.org, iso639-3.sil.org,
    huggingface.co). A specification is not a paper and its title will not appear in a reference
    string, so these are checked for reachability only, and the report says so rather than implying
    a title match happened.

"It could not be read" and "it is correct" never produce the same output: an address that cannot be
fetched is reported as UNREACHABLE, not as a pass.

NETWORK NOTE. This is not part of run_all_guards.py: it depends on remote hosts, and a guard suite
that fails because arXiv is slow teaches its operator to ignore it. Run it before circulating.

NEGATIVE CONTROL
  --negative-test pairs a real entry with the address of a different real paper and requires the
  mismatch to be reported, so the check is known capable of failing before its pass is believed.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import ssl
import sys
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"

SCHOLARLY = ("aclanthology.org", "arxiv.org", "doi.org", "proceedings.mlr.press", "openreview.net",
             "academic.oup.com", "link.springer.com", "dl.acm.org", "ieeexplore.ieee.org",
             "mitpressjournals.org", "direct.mit.edu", "tandfonline.com", "cambridge.org")
RESOURCE = ("cldr.unicode.org", "unicode.org", "iso639-3.sil.org", "huggingface.co", "zenodo.org",
            "docs.python.org", "github.com")

STOP = {"the", "a", "an", "of", "and", "for", "on", "in", "to", "with", "from", "by", "at", "as",
        "is", "are", "be", "that", "this", "its", "it", "we", "our", "using", "based", "toward",
        "towards", "new", "via", "into", "not", "no", "as", "or", "s", "can", "does"}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (compatible; LIMEN-reference-verifier/1.0)"}


def entries(src: str) -> list[tuple[str, str]]:
    i = src.find("  const REFS = [")
    j = src.find("  ];", i)
    blk = src[i:j] if i >= 0 and j > i else ""
    out = []
    for k, t in re.findall(r"\{\s*k:\s*'([^']+)',\s*t:\s*(.*?)\s*\},", blk, re.S):
        text = re.sub(r"'\s*\+\s*'", "", t)
        text = html.unescape(re.sub(r"<[^>]+>", "", text))
        out.append((k, re.sub(r"\s+", " ", text)))
    return out


def fetch(url: str) -> tuple[int | None, str]:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=CTX)
        return r.status, r.read(200_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:  # noqa: BLE001
        return None, ""


def page_title(body: str) -> str:
    for pat in (r'<meta[^>]+name=["\']citation_title["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_title["\']',
                r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
                r"<title[^>]*>(.*?)</title>"):
        m = re.search(pat, body, re.S | re.I)
        if m:
            return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return ""


def sig(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3 and w not in STOP]


def judge(key: str, text: str, url: str) -> tuple[str, str]:
    """Returns (verdict, detail). Verdict: MATCH | MISMATCH | REACHABLE | UNREACHABLE."""
    status, body = fetch(url)
    if status is None:
        return "UNREACHABLE", "no response"
    if status >= 400:
        return "UNREACHABLE", "HTTP %d" % status
    is_resource = any(h in url for h in RESOURCE) and not any(h in url for h in SCHOLARLY)
    if is_resource:
        return "REACHABLE", "HTTP %d (resource page: reachability only)" % status
    title = page_title(body)
    # A paywall serves a login page to a non-browser. That is "could not read", not "wrong work":
    # reporting it as a misattribution would be a false alarm against a correct identifier.
    if any(w in title.lower() for w in ("log in", "login", "sign in", "access denied",
                                        "just a moment", "are you a robot", "captcha", "verify you")):
        return "UNREACHABLE", "HTTP %d but the page is a login or bot wall: %r" % (status, title[:60])
    if not title:
        return "UNREACHABLE", "HTTP %d but the page carries no title to compare" % status
    missing = [w for w in sig(title) if w not in sig(text)]
    if len(missing) > max(1, int(0.34 * len(sig(title)))):
        return "MISMATCH", "%r -- %d of %d significant words absent from the entry" % (
            title[:70], len(missing), len(sig(title)))
    return "MATCH", title[:70]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-test", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()

    if not REPORT.exists():
        print("  [FAIL] report not found: %s" % REPORT)
        return 1
    ents = entries(REPORT.read_text(encoding="utf-8"))
    if not ents:
        print("  [FAIL] no entries parsed from the reference list")
        return 1

    if args.negative_test:
        k, t = next(((k, t) for k, t in ents if k == "kernighan1990"), ents[0])
        # a real entry checked against a real page that is a different work
        verdict, detail = judge(k, t, "https://aclanthology.org/2024.lrec-main.687/")
        if verdict == "MISMATCH":
            print("  [OK] negative control fires: a real page for a different work is reported")
            print("       %s" % detail)
            return 0
        print("  [FAIL] the control was not reported as a mismatch (got %s) -- inert" % verdict)
        return 1

    results, bad = [], 0
    for key, text in ents:
        urls = [u.rstrip(".,;)") for u in re.findall(r"https?://[^\s'\"<>]+", text)]
        if not urls:
            continue
        for u in urls:
            verdict, detail = judge(key, text, u)
            results.append({"key": key, "url": u, "verdict": verdict, "detail": detail})
            mark = {"MATCH": "[OK  ]", "REACHABLE": "[OK  ]", "MISMATCH": "[FAIL]",
                    "UNREACHABLE": "[????]"}[verdict]
            print("  %s %-17s %s" % (mark, key, u[:62]))
            if verdict != "MATCH" and verdict != "REACHABLE":
                print("           %s" % detail)
            if verdict == "MISMATCH":
                bad += 1
    print()
    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("  %d address(es): %s" % (len(results), ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items()))))
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(results, indent=1), encoding="utf-8")
        print("  wrote %s" % args.json)
    if bad:
        print()
        print("  An address that serves a different work is a misattribution: the claim it supports")
        print("  is attached to someone else's result.")
        return 1
    print("  [OK] no address serves a different work than the entry naming it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
