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

A failed launch is kept on disk: the printed line dies with the process, so the
last refusal or real failure is written to the gitignored scratch file
tmp/live-sandbox-failed.json and its path is published as `artifact`. It is NOT
written to preview/live-sandbox.json - that path is a published product whose
byte count the CEO latest-artifact line quotes (measured at R2987).

Usage:
  python tools/ceo_live_shot.py                  # shoot into preview/live/
  python tools/ceo_live_shot.py --prove          # two passes, refuse on drift
  python tools/ceo_live_shot.py --browser chromium
  python tools/ceo_live_shot.py --check          # accepted for compatibility
                                                 # only; a failing face already
                                                 # exits 2 without it
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


def _collision_pairs(raw):
    """Normalize published override duplicates into (port, keys) rows."""
    out = []
    for item in raw or ():
        try:
            port, keys = item
            out.append((int(port), tuple(sorted(str(key) for key in keys))))
        except (TypeError, ValueError):
            continue
    return out


def recorded_collisions(record_path):
    """Name the override collision a launcher record publishes, if any.

    R2983: the machine record is the EARLIEST artifact that carries a
    collision, and this driver - the one a person actually runs - never looked
    at it. R2984 measured the limit of this route: the launcher releases the
    record inside the same finally block that writes the report, so once the
    report is parseable the record is already gone. This reader therefore
    speaks for the report-never-arrives case, and report_collisions speaks for
    the other. Read-only, and a missing or unreadable record answers ()
    instead of raising, because this is a note attached to a failure and a
    note must never replace the failure.
    """
    try:
        with open(record_path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, ValueError):
        return ()
    return tuple(sorted(_collision_pairs(record.get("override_duplicates"))))


def report_collisions(report):
    """Name the override collision a launcher report publishes, if any.

    R2984, measured with a real colliding launcher: of 13 five-millisecond
    samples taken once the report was parseable, zero had the machine record
    still on disk. The report is the only survivor on that path, so a reader
    that only opens the record answers empty exactly when the report is there
    to be read.
    """
    return tuple(sorted(_collision_pairs((report or {}).get(
        "override_duplicates"))))


def published_collisions(record_path, report):
    """Both survivors, each collision named once.

    The record speaks when the report never arrives (R2983); the report speaks
    when it does (R2984). One call site, one named field.

    R2985: a REFUSED launch never claimed the record, so the file on disk
    belongs to the launcher that turned it away. Merging that file into this
    launch's answer credited a stranger's collision to a plan that had none
    (measured: a healthy refusal plus a holder record carrying a collision
    returned the holder's pair). When the report itself says it did not take
    the record, the record is not this launch's to read.
    """
    pairs = set(report_collisions(report))
    registry = (report or {}).get("registry")
    refused_the_record = (isinstance(registry, dict)
                          and registry.get("claimed") is False)
    if not refused_the_record:
        pairs.update(recorded_collisions(record_path))
    return tuple(sorted(pairs))


REFUSAL_CODE = "E_LAUNCHER_ALREADY_RUNNING"


EXIT_OK = 0
EXIT_FACES = 2


def exit_status(payload):
    """The code this run must leave behind, read from the payload alone.

    R2988 measured the defect: the module docstring promised "2 = at least one
    face failed to load or raised", but main() ended with
    `return code if args.check else 0`, so a person running this to CHECK the
    sandbox got the same exit code as a green run. The probe drove the shipped
    main() with the photographic layer stubbed against a real launcher on a
    world where every face failed and measured rc=0 with payload
    ok=False with_errors=9. A missing or shapeless payload answers 2 as well:
    the only value that may mean "everything photographed" is an explicit
    truthy `ok`, never the absence of a verdict.

    Kept as a function so the contract is something a suite can grade instead
    of a sentence in a docstring.
    """
    return EXIT_OK if (payload or {}).get("ok") else EXIT_FACES


def refusal_of(report):
    """Name a launch that was TURNED AWAY before any child existed.

    R2986 measured three real launches: a kernel-claim refusal, a machine-
    record refusal and a real failure all reached this driver as the same
    printed line (`why: sandbox never proved ready`, empty collisions), with
    the difference buried in the nested report. A person running this to see
    the sandbox could not tell "another launcher is already serving" from
    "this sandbox is broken" - two situations that need opposite reactions.

    The launcher publishes the distinction itself: both refusal doors put
    E_LAUNCHER_ALREADY_RUNNING in `errors` and leave `registry.claimed` False
    (nothing was claimed, no child was started), while a real failure claims
    the record (claimed True) and reports faces that never came up. Missing
    keys answer None rather than raising: a note must never replace the
    failure it is attached to.
    """
    report = report or {}
    errors = report.get("errors") or []
    detail = None
    for item in errors:
        if str(item).startswith(REFUSAL_CODE):
            detail = str(item)
            break
    if detail is None:
        return None
    registry = report.get("registry")
    if not isinstance(registry, dict) or registry.get("claimed") is not False:
        return None
    fields = {}
    for part in detail.split():
        if "=" in part:
            key, value = part.split("=", 1)
            fields.setdefault(key, value)
    if fields.get("source") == "mutex":
        door = "kernel-mutex"
    elif fields.get("reason"):
        door = "machine-record"
    else:
        door = "unnamed-door"
    return {"code": REFUSAL_CODE, "door": door,
            "source": fields.get("source"),
            "reason": fields.get("reason"),
            "detail": detail}


# R2987: the failure line is printed and then lost with the process. The


# launcher's own --report-json is the SUCCESS product, and it is published:


# export_round._pairs puts that file's on-disk byte count straight onto the CEO


# latest-artifact line and tools/deliverable_index.py derives the newest


# preview artifact from a fresh mtime scan of preview/*.json. Measured in a


# throwaway world (tmp/probe_R2987.py): rewriting that one file with a failure


# payload moved both published numbers 126B -> 199B, i.e. the failure would be


# named and sized as the newest product while its gallery half still shows a


# healthy run - and the tracked file would sit dirty in git. A json with no


# sibling html is invisible to both derivers, so the payload goes to the


# gitignored scratch dir under ONE stable name: the last failure is always at


# the same path, and nothing derives from it.


FAILURE_NAME = "live-sandbox-failed.json"


SCRATCH = os.path.join(REPO, "tmp")




def failure_artifact_path():


    """Where the LAST failed launch is kept, for a person re-reading it."""


    return os.path.join(SCRATCH, FAILURE_NAME)




def write_failure(record_path, report, path=None):


    """Publish the failure payload on disk and name the file it went to.



    Same body the driver prints, minus the `artifact` key that points here.


    Atomic (write beside, then replace), and it never raises: this note is


    attached to a failure and a note must never replace the failure. A target


    whose directory does not exist answers None rather than creating a tree -


    the caller decides where its artifacts may live, not this writer.


    """


    payload = {"ok": False,


               "why": "sandbox never proved ready",


               "refusal": refusal_of(report),


               "record_collisions": [list(item) for item in


                                     published_collisions(record_path, report)],


               "report": report}


    target = path or failure_artifact_path()


    holder = target + ".tmp"


    try:


        with open(holder, "w", encoding="utf-8", newline="\n") as handle:


            json.dump(payload, handle, ensure_ascii=False, sort_keys=True,


                      indent=2)


            handle.write("\n")


        os.replace(holder, target)


    except OSError:


        return None


    return os.path.relpath(target, REPO).replace("\\", "/")




def launcher_record_path():


    """Ask the launcher registry where it writes, without importing at load.
    """
    sandbox = os.path.join(REPO, "src", "sandbox")
    if sandbox not in sys.path:
        sys.path.insert(0, sandbox)
    import launcher_registry
    return launcher_registry.default_path()


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
            # R2988: the gallery sits in preview/ while the shots live in
            # preview/live/, so a bare basename pointed every <img> at a file
            # that does not exist (measured on the round's own real run: nine
            # empty frames). Resolve from the page's own directory instead.
            src = os.path.relpath(os.path.join(REPO, row["png"]),
                                  os.path.dirname(path))
            parts.append("<img src='%s' alt='%s'>"
                         % (src.replace("\\", "/"), row["title"]))
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
                        help="accepted for compatibility only: a face that "
                             "failed to load or raised already exits 2 "
                             "without this flag")
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
            record_path = launcher_record_path()
            collisions = published_collisions(record_path, report)
            artifact = write_failure(record_path, report)
            # R2986: the two refusal doors and a real failure used to print
            # one identical line. `refusal` names the first two (nothing was
            # started); null means the sandbox itself failed.
            # R2987: artifact = where to re-read.
            print(json.dumps({"ok": False,
                              "why": "sandbox never proved ready",
                              "refusal": refusal_of(report),
                              "record_collisions": [list(item)
                                                    for item in collisions],
                              "artifact": artifact,
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
        # R2988: the face verdict now reaches the exit code without a flag.
        # `args.check` is still parsed so old command lines keep working, but
        # it no longer decides whether a failure is told or swallowed.
        code = exit_status(payload)
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
    return code


if __name__ == "__main__":
    sys.exit(main())
