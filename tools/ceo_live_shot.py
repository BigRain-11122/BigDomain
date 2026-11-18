"""ceo_live_shot - turn the running sandbox into PIXELS a person can look at.

Why this exists: the sandbox already ships seven real faces (hub, lobby, city,
gate, ledger, ugc, checkout) and `start_all.py --check` proves every port
accepts a connection. A listening port is not the same claim as a working
page: a face whose JavaScript throws on load still accepts the connection, and
every round that reported the sandbox as "live" was reporting the socket only.
The CEO face needs the other half - what is actually ON the screen, and whether
the page raised any error while painting it.

This tool starts the shipped launcher in serve mode, opens every face in a real
browser (Edge channel by default - the browser Windows already has), photographs
each one, records every console message and uncaught page error, builds one
gallery page, and tears the sandbox down again. Nothing is stubbed and no face
is special-cased: the tool reads the URL list from the launcher's own report
instead of hardcoding ports.

One pass is a snapshot, and a snapshot cannot tell "this face is alive" apart
from "this face happened to paint cleanly this time". So `--prove` shoots the
same faces TWICE against the SAME sandbox instance - the second pass starts
after the first pass's lobby action - and refuses when the two passes disagree
on any face's HTTP status or error set. Agreement is compared, never asserted.

Usage:
  python tools/ceo_live_shot.py                  # shoot into preview/live/
  python tools/ceo_live_shot.py --check          # shoot, then exit non-zero on
                                                 # any face that raised an error
  python tools/ceo_live_shot.py --prove          # two passes, refuse on drift
  python tools/ceo_live_shot.py --browser chromium
Exit: 0 = every face photographed; 2 = at least one face failed to load or
raised an uncaught error, or the two --prove passes disagreed; 3 = the sandbox
never came up.

Stdlib plus playwright. ASCII source, no network beyond 127.0.0.1.
"""

import argparse
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
START_ALL = os.path.join(REPO, "src", "sandbox", "start_all.py")
PREVIEW = os.path.join(REPO, "preview")
LIVE = os.path.join(PREVIEW, "live")

# The hub is the door; the rest are the faces behind it, in reading order.
# Ordered so the gallery reads as a product tour rather than a port list.
FACES = (
    ("hub", "Hub - the one door", "Every face the sandbox serves, with its own "
                                  "live probe"),
    ("lobby", "Lobby - realtime rooms", "WebSocket rooms, presence and chat"),
    ("city", "City - world read API", "The silicon-city data the lobby reads"),
    ("gate", "Gate - content console", "The msgSecCheck-style admission gate"),
    ("ugc", "UGC - submission console", "Creator submissions through the gate"),
    ("ledger", "Ledger - token console", "The two-form token ledger"),
    ("checkout", "Checkout - 19.9 mock", "The membership purchase demonstrable "
                                         "without a merchant id"),
    ("member", "Member - membership page", "Two-form token balance, tiers and "
                                           "the expiring-reminder face"),
    ("panel", "Panel - control surface", "Start and stop verbs per face, with "
                                         "measured ports"),
)

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def wait_json(path, timeout):
    """Wait for the launcher to publish its report; return the parsed report."""
    deadline = time.time() + float(timeout)
    while time.time() < deadline:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    return json.load(handle)
            except (OSError, ValueError):
                pass
        time.sleep(0.2)
    return None


def drive_lobby(page):
    """Walk the lobby through a real session before it is photographed.

    A screenshot of an empty room proves the page paints, not that the realtime
    loop works. This connects, takes the mock door ticket, and sends one line,
    so the picture carries a presence entry, a message and ledger rows - and
    the returned steps are reported, so a face that failed at step two is not
    silently photographed as if it passed.
    """
    steps = []
    page.fill("#nick", "sandbox-walkthrough")
    page.click("#connect")
    page.wait_for_function(
        "document.querySelector('#state').textContent.trim()"
        ".startsWith('\u5df2\u8fde\u63a5')",
        timeout=8000)
    steps.append("connected")
    page.click("#grant")
    page.wait_for_function(
        "!document.querySelector('#text').disabled", timeout=8000)
    steps.append("ticket")
    page.fill("#text", "R2934 live shot: this line travelled over the real socket")
    page.click("#send")
    page.wait_for_function(
        "document.querySelectorAll('#ledger tr').length > 1", timeout=8000)
    steps.append("message")
    page.wait_for_timeout(400)
    return steps


def compare_runs(first, second):
    """Compare two photography passes, one disagreement row per drifting face.

    Pure on purpose: no browser, no disk, no clock, so a stdlib suite can grade
    the law itself instead of grading the network. `--prove` is only worth
    running if this comparison has been seen to say NO, hence the fixtures in
    src/os/test_live_proof.py.

    Kinds, decided in this order and only the first one that fires is reported:
    "missing" (a face is present in one pass and absent from the other),
    "status" (different HTTP status), "errors" (different error SET - sorted, so
    ordering is not drift), "ok" (same status and errors, different verdict).

    One row per face is deliberate: it keeps `agreements + len(disagreements)
    == faces` an identity the report can be checked against, so a face that
    drifted in two ways cannot be miscounted as two faces.
    """
    left = {row.get("face"): row for row in first}
    right = {row.get("face"): row for row in second}
    order = [row.get("face") for row in first]
    for row in second:
        if row.get("face") not in order:
            order.append(row.get("face"))
    out = []
    for face in order:
        a = left.get(face)
        b = right.get(face)
        if a is None or b is None:
            out.append({"face": face, "kind": "missing",
                        "first": "present" if a else "absent",
                        "second": "present" if b else "absent"})
            continue
        if (a.get("status") or 0) != (b.get("status") or 0):
            out.append({"face": face, "kind": "status",
                        "first": a.get("status"), "second": b.get("status")})
            continue
        left_errors = sorted(a.get("errors") or [])
        right_errors = sorted(b.get("errors") or [])
        if left_errors != right_errors:
            out.append({"face": face, "kind": "errors",
                        "first": left_errors, "second": right_errors})
            continue
        if bool(a.get("ok")) != bool(b.get("ok")):
            out.append({"face": face, "kind": "ok",
                        "first": a.get("ok"), "second": b.get("ok")})
    return out


def shoot(browser_name, report, settle_ms, width, out_dir, pass_no=1):
    """Photograph every face and collect what the page said while painting."""
    from playwright.sync_api import sync_playwright

    faces = report.get("faces") or {}
    rows = []
    with sync_playwright() as play:
        if browser_name == "chromium":
            browser = play.chromium.launch(channel="msedge")
        else:
            browser = play.chromium.launch(channel="msedge")
        for key, title, blurb in FACES:
            # The launcher publishes the six faces behind the door in `faces`,
            # but the door itself only as `hub_url` - a shape difference that
            # would otherwise photograph six faces and quietly skip the one a
            # person is told to open first.
            if key == "hub":
                url = report.get("hub_url")
            else:
                url = faces.get(key)
            row = {"face": key, "title": title, "blurb": blurb, "url": url,
                   "pass": pass_no, "png": None, "status": None,
                   "console": [], "errors": [], "acted": [], "ok": False,
                   "why": ""}
            if not url:
                row["why"] = "face not published by the launcher"
                rows.append(row)
                continue
            messages = []
            errors = []
            # One page per face so listeners die with the page: a shared page
            # keeps every earlier face's handlers alive and its error list
            # would then be fed by any later redirect.
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("console", lambda msg: messages.append(
                msg.type + ": " + msg.text))
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            try:
                response = page.goto(url, wait_until="load", timeout=20000)
                page.wait_for_timeout(settle_ms)
                if key == "lobby":
                    row["acted"] = drive_lobby(page)
                png = os.path.join(
                    out_dir, key + (".png" if pass_no == 1
                                    else "-p%d.png" % pass_no))
                page.screenshot(path=png, full_page=True)
                row["png"] = os.path.relpath(png, REPO).replace("\\", "/")
                row["status"] = response.status if response else None
                row["ok"] = not errors and (row["status"] or 0) < 400
            except Exception as exc:  # noqa: BLE001 - name it, never swallow
                row["why"] = type(exc).__name__ + ": " + str(exc)[:200]
            row["console"] = messages[-8:]
            row["errors"] = errors[-5:]
            page.close()
            rows.append(row)
        browser.close()
    return rows


def gallery(rows, report, path, proof=None):
    """One page a person can scroll instead of seven tabs."""
    total = len(rows)
    good = sum(1 for row in rows if row["ok"])
    parts = [
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>",
        "<title>BigDomain sandbox - live faces</title>",
        "<style>",
        "body{font-family:system-ui,Segoe UI,sans-serif;margin:0;background:#0f1117;"
        "color:#e8eaf0}header{padding:28px 32px;border-bottom:1px solid #232838}",
        "h1{margin:0 0 6px;font-size:22px}p{margin:4px 0;color:#9aa3b5}",
        ".k{color:#7ee0a0;font-weight:600}.bad{color:#ff7b7b;font-weight:600}",
        "section{padding:20px 32px;border-bottom:1px solid #1c2030}",
        "h2{margin:0 0 4px;font-size:16px}code{background:#1a1f2c;padding:2px 6px;"
        "border-radius:4px;font-size:12px}img{width:100%;max-width:1100px;"
        "border:1px solid #232838;border-radius:8px;margin-top:10px}",
        "ul{margin:6px 0;padding-left:18px;font-size:12px;color:#8b93a7}",
        "</style></head><body>",
        "<header><h1>BigDomain sandbox - photographed live</h1>",
        "<p>Faces photographed: <span class='k'>%d/%d</span> - sandbox report "
        "<code>ok=%s</code>, mock only, no charge, no merchant id needed.</p>"
        % (good, total, str(report.get("ok"))),
        "<p>Run it yourself: <code>python src/sandbox/start_all.py</code> then "
        "open the URL it prints. This page is a snapshot, not a server.</p>",
        "</header>",
    ]
    if proof is not None:
        # A snapshot is one frame; this line says whether a second frame of the
        # same sandbox agreed. Nothing here is typed: both numbers are counted.
        mark = ("<span class='k'>two passes agree</span>" if proof["ok"]
                else "<span class='bad'>passes DISAGREE</span>")
        parts.insert(-1, "<p>Repeatable proof: %s - %d/%d faces agreed across "
                         "two passes on the same sandbox (second pass shot "
                         "after the lobby action; its images are "
                         "<code>*-p2.png</code>).</p>"
                         % (mark, proof["agreements"], proof["faces"]))
        if proof["disagreed"]:
            parts.insert(-1, "<p class='bad'>drifted: %s</p>"
                             % ", ".join(proof["disagreed"]))
    for row in rows:
        mark = ("<span class='k'>ok</span>" if row["ok"]
                else "<span class='bad'>failed</span>")
        parts.append("<section><h2>%s - %s</h2>" % (row["title"], mark))
        parts.append("<p>%s</p><p><code>%s</code> - http %s</p>"
                     % (row["blurb"], row["url"] or "-", row["status"]))
        if row["why"]:
            parts.append("<p class='bad'>%s</p>" % row["why"])
        if row["png"]:
            parts.append("<img src='%s' alt='%s'>"
                         % (os.path.basename(row["png"]), row["title"]))
        if row["errors"]:
            parts.append("<ul>" + "".join("<li>%s</li>" % e
                                          for e in row["errors"]) + "</ul>")
        parts.append("</section>")
    parts.append("</body></html>")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(parts) + "\n")
    os.replace(tmp, path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="photograph every live sandbox face and build a gallery")
    parser.add_argument("--check", action="store_true",
                        help="exit 2 when any face failed to load or raised")
    parser.add_argument("--prove", action="store_true",
                        help="shoot every face twice on the same sandbox and "
                             "refuse when the two passes disagree")
    parser.add_argument("--browser", default="edge", choices=("edge",))
    parser.add_argument("--settle-ms", type=int, default=1200)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--out-dir", default=LIVE)
    parser.add_argument("--report-json", default=os.path.join(
        PREVIEW, "live-sandbox.json"))
    args = parser.parse_args(argv)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    tmp_dir = os.path.join(REPO, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    report_path = os.path.join(tmp_dir, "live-shot-report-%s.json" % stamp)
    stop_path = os.path.join(tmp_dir, "live-shot-stop-%s" % stamp)
    for path in (report_path, stop_path):
        if os.path.exists(path):
            os.remove(path)

    launcher = subprocess.Popen(
        [sys.executable, START_ALL,
         "--report-json", report_path, "--stop-file", stop_path,
         "--timeout", "30"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, creationflags=NO_WINDOW,
    )
    code = 3
    try:
        report = wait_json(report_path, args.timeout)
        if not report or not report.get("ok"):
            print(json.dumps({"ok": False,
                              "why": "sandbox never proved ready",
                              "report": report}, ensure_ascii=False))
            return 3
        first = shoot(args.browser, report, args.settle_ms, args.width,
                      out_dir, 1)
        rows = first
        proof = None
        if args.prove:
            # The second pass runs AFTER the first one drove the lobby through
            # a real session, so the sandbox is no longer the world the first
            # pass photographed. What must not change is each face's verdict.
            second = shoot(args.browser, report, args.settle_ms, args.width,
                           out_dir, 2)
            disagreements = compare_runs(first, second)
            disagreed = sorted(item["face"] for item in disagreements)
            proof = {
                "passes": 2,
                "faces": len(first),
                "agreements": len(first) - len(disagreed),
                "disagreed": disagreed,
                "disagreements": disagreements,
                "first_ok": all(row["ok"] for row in first),
                "second_ok": all(row["ok"] for row in second),
            }
            proof["ok"] = (proof["agreements"] == proof["faces"]
                           and proof["first_ok"] and proof["second_ok"])
            rows = first + second
        shot = [{"face": row["face"], "pass": row.get("pass", 1),
                 "url": row["url"], "png": row["png"],
                 "status": row["status"], "ok": row["ok"],
                 "acted": row["acted"], "why": row["why"],
                 "errors": row["errors"]}
                for row in rows]
        payload = {
            # Counted by distinct face, not by shot: in --prove mode `rows`
            # holds two passes, and the earlier len(rows) == len(FACES) test
            # read a healthy two-pass run as a failure (caught live at R2935).
            "ok": (all(row["ok"] for row in rows)
                   and len({row["face"] for row in rows}) == len(FACES)),
            "shots": shot,
            "faces": len({row["face"] for row in rows}),
            "shots_total": len(rows),
            "photographed": sum(1 for row in rows if row["png"]),
            "with_errors": sum(1 for row in rows if row["errors"]),
            "hub_url": report.get("hub_url"),
            "gallery": os.path.relpath(
                os.path.join(PREVIEW, "live-sandbox.html"), REPO
            ).replace("\\", "/"),
            "mock": True,
            "chargeable": False,
            "shoot_ts": stamp,
        }
        if proof is not None:
            payload["proof"] = proof
            payload["ok"] = payload["ok"] and proof["ok"]
        gallery(first, report, os.path.join(PREVIEW, "live-sandbox.html"),
                proof=proof)
        tmp = args.report_json + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True,
                      indent=2)
            handle.write("\n")
        os.replace(tmp, args.report_json)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        code = 0 if payload["ok"] else 2
    finally:
        open(stop_path, "w", encoding="utf-8").close()
        deadline = time.time() + 15.0
        while launcher.poll() is None and time.time() < deadline:
            time.sleep(0.2)
        if launcher.poll() is None:
            launcher.kill()
        for path in (report_path, stop_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
    return code if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
