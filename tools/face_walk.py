"""face_walk - open a shipped preview face in a REAL browser and report it.

WHY THIS EXISTS: every evidence file in qa/ (3300+) is a python suite log. Not
one of them ever loaded a preview page in a browser, so "the CEO can open this"
was an assumption, not a measurement. A static page whose JSON fetch fails, whose
script throws, or whose links point at files that are not on disk still reads
"MERGED"/"PASS" in every suite that only greps its source.

This tool loads each named page from disk in headless Chromium (the local Edge
channel by default, so no browser download is required), collects what the page
actually did, writes one full-page PNG per page, and prints one WALK line per
page plus a WALK-TOTAL line. Nothing about a particular page is typed in: the
counts are taken from the browser, the dead-link count is derived from the DOM,
and the screenshot is verified by its PNG signature before it is believed.

Usage:
  python tools/face_walk.py --pages index.html journey-19.9.html --tag R2930
  python tools/face_walk.py --dir DIR --out OUT --pages x.html    # fixture world
  python tools/face_walk.py --json

Verdict: rc=0 when every page rendered with text, zero console errors, zero
failed requests and zero dead local links; rc=2 otherwise; rc=3 when playwright
or its browser is unavailable (refused by name, never silently skipped).

Scope, stated honestly: this tool needs playwright, which is NOT stdlib, and the
battery registry law is stdlib-only - so this face is run on demand and is NOT a
SUITES row. It writes only PNG evidence into --out (default qa/) and never
touches the pages it walks.
"""

import argparse
import json
import os
import sys

BLANK_CHARS = 200
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _die(msg, rc=3):
    print(msg)
    raise SystemExit(rc)


def png_ok(head, size):
    """The screenshot law in one place, so a stdlib suite can grade it."""
    return head == PNG_SIG and size > 0


def dead_targets(page_path, hrefs):
    """Resolve local links the way a BROWSER does: relative to the page dir.

    The R2930 defect was a page inside preview/ linking 'preview/x.html', which
    a browser resolves to preview/preview/x.html. Resolving against the repo
    root instead made that page's own checker agree with its author and
    disagree with its consumer, which is why this law lives here.
    """
    base = os.path.dirname(os.path.abspath(page_path))
    dead = []
    for href in hrefs:
        target = _local_href(href)
        if target is None:
            continue
        resolved = os.path.normpath(os.path.join(base, target.replace("/", os.sep)))
        if not os.path.exists(resolved):
            dead.append(href)
    return dead


def _local_href(href):
    if not href:
        return None
    h = href.strip()
    low = h.lower()
    for skip in ("http://", "https://", "//", "#", "mailto:", "javascript:", "data:", "tel:"):
        if low.startswith(skip):
            return None
    target = h.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    return target


def walk_page(browser, page_path, dir_path, out_dir, tag, take_shot=True):
    from urllib.parse import urljoin

    url = "file:///" + os.path.abspath(page_path).replace("\\", "/")
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    fails = []

    def on_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    def on_pageerror(exc):
        errors.append(str(exc))

    def on_requestfailed(req):
        fails.append(req.url)

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("requestfailed", on_requestfailed)

    row = {
        "page": os.path.basename(page_path),
        "url": url,
        "chars": 0,
        "errors": 0,
        "failed": 0,
        "dead": 0,
        "dead_targets": [],
        "shot": None,
        "shot_bytes": 0,
        "png_ok": False,
        "load_error": None,
    }
    try:
        page.goto(url, wait_until="load", timeout=20000)
        chars = page.evaluate(
            "() => { const b = document.body; return b ? (b.innerText || '').trim().length : 0; }"
        )
        row["chars"] = int(chars or 0)
        hrefs = page.eval_on_selector_all(
            "a[href]", "els => els.map(e => e.getAttribute('href'))"
        )
        dead = dead_targets(page_path, hrefs)
        row["dead"] = len(dead)
        if dead:
            row["dead_targets"] = dead[:12]
        if take_shot:
            stem = os.path.splitext(os.path.basename(page_path))[0]
            shot = os.path.join(out_dir, "%s-%s.png" % (tag, stem))
            page.screenshot(path=shot, full_page=True)
            row["shot"] = shot
            if os.path.exists(shot):
                with open(shot, "rb") as fh:
                    head = fh.read(8)
                row["shot_bytes"] = os.path.getsize(shot)
                row["png_ok"] = png_ok(head, row["shot_bytes"])
    except Exception as exc:  # a page that will not even load is a finding
        row["load_error"] = "%s: %s" % (type(exc).__name__, exc)
    finally:
        row["errors"] = len(errors)
        row["failed"] = len(fails)
        if errors:
            row["error_sample"] = errors[:3]
        if fails:
            row["failed_sample"] = fails[:3]
        page.close()

    row["ok"] = (
        row["load_error"] is None
        and row["chars"] >= BLANK_CHARS
        and row["errors"] == 0
        and row["failed"] == 0
        and row["dead"] == 0
        and (row["png_ok"] or not take_shot)
    )
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--root", default=None, help="repo root (default: parent of tools/)")
    ap.add_argument("--dir", default="preview", help="directory holding the pages")
    ap.add_argument("--out", default="qa", help="directory for PNG evidence")
    ap.add_argument("--pages", nargs="+", required=True, help="page file names")
    ap.add_argument("--tag", default="walk", help="evidence file prefix")
    ap.add_argument("--channel", default="msedge", help="browser channel (default msedge)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--no-shot",
        action="store_true",
        help="census mode: measure pages without writing PNG evidence",
    )
    args = ap.parse_args(argv)

    root = args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    page_dir = args.dir if os.path.isabs(args.dir) else os.path.join(root, args.dir)
    out_dir = args.out if os.path.isabs(args.out) else os.path.join(root, args.out)
    if not os.path.isdir(page_dir):
        _die("E_FW_NO_DIR %s" % page_dir)
    os.makedirs(out_dir, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        _die("E_FW_NO_PLAYWRIGHT %s" % exc)

    rows = []
    pw = sync_playwright().start()
    try:
        try:
            browser = pw.chromium.launch(channel=args.channel)
        except Exception as exc:
            _die("E_FW_NO_BROWSER channel=%s %s" % (args.channel, exc))
        try:
            for name in args.pages:
                path = os.path.join(page_dir, name)
                if not os.path.exists(path):
                    rows.append(
                        {
                            "page": name,
                            "chars": 0,
                            "errors": 0,
                            "failed": 0,
                            "dead": 0,
                            "shot": None,
                            "shot_bytes": 0,
                            "png_ok": False,
                            "load_error": "E_FW_MISSING_PAGE",
                            "ok": False,
                        }
                    )
                    continue
                rows.append(
                    walk_page(
                        browser,
                        path,
                        page_dir,
                        out_dir,
                        args.tag,
                        take_shot=not args.no_shot,
                    )
                )
        finally:
            browser.close()
    finally:
        pw.stop()

    pages = len(rows)
    ok = sum(1 for r in rows if r["ok"])
    blank = sum(1 for r in rows if r.get("chars", 0) < BLANK_CHARS)
    errors = sum(r.get("errors", 0) for r in rows)
    failed = sum(r.get("failed", 0) for r in rows)
    dead = sum(r.get("dead", 0) for r in rows)
    shots = sum(1 for r in rows if r.get("png_ok"))

    for r in rows:
        print(
            "WALK page=%s chars=%d errors=%d failed=%d dead=%d shot=%s bytes=%d %s"
            % (
                r.get("page"),
                r.get("chars", 0),
                r.get("errors", 0),
                r.get("failed", 0),
                r.get("dead", 0),
                (r.get("shot") or "none").replace("\\", "/"),
                r.get("shot_bytes", 0),
                "OK" if r["ok"] else ("FAIL %s" % (r.get("load_error") or "see counts")),
            )
        )
    print(
        "WALK-TOTAL pages=%d ok=%d blank=%d errors=%d failed=%d dead_links=%d shots=%d rc=%d"
        % (pages, ok, blank, errors, failed, dead, shots, 0 if ok == pages else 2)
    )
    if args.json:
        print(json.dumps({"rows": rows, "pages": pages, "ok": ok}, ensure_ascii=True))
    return 0 if ok == pages else 2


if __name__ == "__main__":
    raise SystemExit(main())
