#!/usr/bin/env python3
"""Read-only check that the API-market current-reading face is honest.

R3291 put one link on each of thirteen frozen snapshots pointing at
preview/apimarket-report.html and said "that is what the current generator
renders".  The target page answered nothing: measured at R3292 it carried
zero occurrences of the word "schema", so a reader arriving from a banner
promise could not verify it, and nobody could say which world it came from.

This round the generator prints its own REPORT_SCHEMA plus the sentence
"schemA N - this page is a static file rendered by the current code, not a
live reading", src/os/preview_R3292.py carries the reproducible recipe, and
this tool grades the pair.

Criteria AC-ACF1..10 (pre-registered in src/os/backlog.md before this file):
  ACF1 the page carries exactly one data-report-schema badge
  ACF2 the printed number == REPORT_SCHEMA parsed from the generator source
       (never hardcoded here) and == the sibling json's schema_version
  ACF3 the visible sentence is the generator's template rendered with that
       same number and date, and contains the literal "not a live reading"
  ACF4 the sibling sizes block == the bytes of both files on disk
  ACF5 the page is byte-identical to (fresh seed_demo render + back-hop
       injection), rendered with the date the page itself claims - the date
       is an input, not a clock read, so byte identity still means something
  ACF6 both files are bare LF (no CR), UTF-8 decodable, and .gitattributes
       pins both paths to text eol=lf (sizes are byte counts; a checkout
       must not rewrite the endings)
  ACF7 --check writes nothing and leaves the thirteen frozen faces byte
       identical to state/apimarket-face-freeze.json
  ACF8 exactly one data-rendered-on on the page, equal to the sibling json's
       rendered_on, and a real calendar date (2026-02-30 is red)
  ACF9 the json's source_sha256 names the generator, the injector and this
       producer, and each equals the sha256 of the file on disk now - this is
       what catches "the gate moved after the render" instead of letting an
       untouched page pass forever
  ACF10 the date is not older than the day the stamp shipped, and not later
       than the machine local day at check time (a page cannot claim to have
       been rendered tomorrow)

What this does NOT prove: that the numbers inside the report are correct, that
they were a live reading on the printed date, or that a buyer can pay. All
three stay false until the physical set arrives.
"""

import argparse
import ast
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")
for _d in (TOOLS, LEDGER, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import apimarket_report as R  # noqa: E402
import face_backhop as B      # noqa: E402

FACE = "apimarket-report.html"
BADGE_RE = re.compile(
    r'<div class="sub schema-badge" data-report-schema="(\d+)"'
    r' data-rendered-on="([^"]*)">(.*?)</div>',
    re.S)
SCHEMA_RE = re.compile(r"^REPORT_SCHEMA = (\d+)$", re.M)
PIN_RE = re.compile(r"^preview/apimarket-report\.(?:html|json)\s+text\s+eol=lf\s*$",
                    re.M)
# The day the render stamp shipped. Chosen when the criterion was written, not
# derived from anything: a page cannot claim to predate the feature.
STAMP_FLOOR = "2026-11-22"
SOURCE_KEYS = ("generator", "injector", "producer")


def set_root(root):
    """Point the paths at another tree (negative controls only)."""
    global ROOT, TOOLS, LEDGER, LOBBY
    ROOT = os.path.abspath(root)
    TOOLS = os.path.join(ROOT, "tools")
    LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
    LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")


def paths():
    return {
        "html": os.path.join(ROOT, "preview", FACE),
        "json": os.path.join(ROOT, "preview", "apimarket-report.json"),
        "report": os.path.join(LEDGER, "apimarket_report.py"),
        "generator": os.path.join(LEDGER, "apimarket_report.py"),
        "injector": os.path.join(TOOLS, "face_backhop.py"),
        "producer": os.path.join(ROOT, "src", "os",
                                 "preview_apimarket_current.py"),
        "attrs": os.path.join(ROOT, ".gitattributes"),
        "freeze": os.path.join(ROOT, "state", "apimarket-face-freeze.json"),
    }


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_facts(path):
    """REPORT_SCHEMA and SCHEMA_BADGE read out of the generator source."""
    text = io.open(path, "r", encoding="utf-8").read()
    found = {}
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in (
                    "REPORT_SCHEMA", "SCHEMA_BADGE"):
                found[target.id] = ast.literal_eval(node.value)
    return found.get("REPORT_SCHEMA"), found.get("SCHEMA_BADGE")


def expected_page(report_source, stamp=None):
    """(fresh render + back-hop injection) from a temp demo world.

    The date is passed in, never read from the clock here: a rerun of the
    recipe must land on the bytes on disk whatever day it is.
    """
    tmp = tempfile.mkdtemp(prefix="apimarket-current-face-check-")
    try:
        db = os.path.join(tmp, "ledger.db")
        led, mtr, dk, am = R.build_stack(db)
        try:
            R.seed_demo(am, led, dk)
        finally:
            am.close()
            dk.close()
            mtr.close()
            led.close()
        out_html = os.path.join(tmp, FACE)
        out_json = os.path.join(tmp, "apimarket-report.json")
        argv = ["--db", db, "--out", out_html, "--json-out", out_json]
        if stamp:
            argv.extend(["--rendered-on", stamp])
        R.main(argv)
        text = io.open(out_html, "r", encoding="utf-8", newline="").read()
        text, how = B.inject_text(text, FACE)
        return text.encode("utf-8"), how
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def frozen_snapshot(freeze_path):
    """{path: (bytes, sha256)} for the frozen faces, or None if unreadable."""
    try:
        doc = json.loads(io.open(freeze_path, "r", encoding="utf-8").read())
    except (OSError, ValueError):
        return None
    out = {}
    for row in doc.get("faces") or []:
        rel = row.get("html")
        if not rel:
            continue
        full = os.path.join(ROOT, rel)
        if os.path.isfile(full):
            raw = read_bytes(full)
            out[rel] = (len(raw), sha256(raw))
        else:
            out[rel] = (None, None)
    return out


def check():
    p = paths()
    fails = []
    raw_html = read_bytes(p["html"])
    raw_json = read_bytes(p["json"])
    text = raw_html.decode("utf-8", "replace")
    try:
        doc = json.loads(raw_json.decode("utf-8", "replace"))
    except ValueError as exc:
        # A truncated or garbled sibling must be NAMED by this tool (the
        # first negative-control run crashed here with a traceback instead
        # of a verdict, which is a defect in the checker, not the tree).
        doc = {}
        doc_error = "E_ACF2 json unreadable: %s" % exc
    else:
        doc_error = None

    # ACF1 one badge
    badges = BADGE_RE.findall(text)
    if len(badges) != 1:
        fails.append("E_ACF1 %d schema badges on the page (want 1)"
                     % len(badges))
    printed = int(badges[0][0]) if len(badges) == 1 else None
    stamp = badges[0][1] if len(badges) == 1 else ""
    sentence = badges[0][2] if len(badges) == 1 else ""
    date_ok = False
    if len(badges) == 1:
        try:
            datetime.date.fromisoformat(stamp)
            date_ok = True
        except ValueError:
            date_ok = False

    # ACF2 the number is read from the generator, and the json agrees
    if doc_error:
        fails.append(doc_error)
    schema, template = source_facts(p["report"])
    if schema is None:
        fails.append("E_ACF2 REPORT_SCHEMA not found in %s"
                     % os.path.basename(p["report"]))
    else:
        if printed is not None and printed != schema:
            fails.append("E_ACF2 badge says %s, source says %d"
                         % (printed, schema))
        sibling = doc.get("schema_version")
        if sibling != schema:
            fails.append("E_ACF2 json schema_version %r != source %d"
                         % (sibling, schema))

    # ACF3 the sentence is the template rendered with that number
    if template is None:
        fails.append("E_ACF3 SCHEMA_BADGE template not found in the source")
    elif schema is not None:
        want = (template % (schema, stamp)).replace("\n", "")
        if sentence.replace("\n", "").strip() != want.strip():
            fails.append("E_ACF3 badge sentence is not the fresh-derived one")
    if "not a live reading" not in sentence:
        fails.append("E_ACF3 badge does not say 'not a live reading'")

    # ACF4 the sizes block equals the bytes on disk
    sizes = doc.get("sizes")
    if not isinstance(sizes, dict):
        fails.append("E_ACF4 json carries no sizes block")
    else:
        want_html, want_json = len(raw_html), len(raw_json)
        if sizes.get("html") != want_html:
            fails.append("E_ACF4 sizes.html %r != %d on disk"
                         % (sizes.get("html"), want_html))
        if sizes.get("json") != want_json:
            fails.append("E_ACF4 sizes.json %r != %d on disk"
                         % (sizes.get("json"), want_json))

    # ACF5 the page is what this tree renders now, injection included.
    # The page's own date is passed into the render: the date is an input of
    # the recipe, so a byte comparison still means "this recipe made this".
    # A page claiming an impossible date cannot be reproduced from it, and
    # handing that date to the generator only crashed the checker (measured in
    # the R3293 negative controls), so it is graded here instead of thrown.
    if stamp and not date_ok:
        expected, how = b"", "unreproducible-date"
    else:
        expected, how = expected_page(p["report"], stamp or None)
    if expected != raw_html:
        fails.append("E_ACF5 page differs from (render + %s): %d vs %d bytes"
                     % (how, len(raw_html), len(expected)))
        a = expected.decode("utf-8", "replace").splitlines()
        b = text.splitlines()
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                fails.append("E_ACF5 first difference at line %d: %r vs %r"
                             % (i + 1, a[i][:90], b[i][:90]))
                break

    # ACF6 dialect + the pin that keeps it host independent
    for label, raw in (("html", raw_html), ("json", raw_json)):
        if b"\r" in raw:
            fails.append("E_ACF6 %s carries %d CR bytes"
                         % (label, raw.count(b"\r")))
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            fails.append("E_ACF6 %s is not UTF-8: %s" % (label, exc))
    try:
        attrs = io.open(p["attrs"], "r", encoding="utf-8").read()
    except OSError:
        attrs = ""
    pinned = PIN_RE.findall(attrs)
    if len(pinned) != 2:
        fails.append("E_ACF6 .gitattributes pins %d of 2 paths to text eol=lf"
                     % len(pinned))

    # ACF8 the page and the json tell the same date, and it is a real date
    if len(badges) == 1:
        if not date_ok:
            fails.append("E_ACF8 data-rendered-on %r is not a calendar date"
                         % stamp)
        recorded = doc.get("rendered_on")
        if not isinstance(recorded, str) or recorded != stamp:
            fails.append("E_ACF8 json rendered_on %r != page %r"
                         % (recorded, stamp))

    # ACF9 the recorded sources still are the files on disk. This is the arm
    # that catches "the gate moved after the render": the page can be
    # byte-identical to its own recipe and still be describing an older one.
    recorded_sources = doc.get("source_sha256")
    if not isinstance(recorded_sources, dict):
        fails.append("E_ACF9 json carries no source_sha256 block")
    else:
        for key in SOURCE_KEYS:
            if key not in recorded_sources:
                fails.append("E_ACF9 source_sha256 has no %r" % key)
                continue
            path = p[key]
            if not os.path.isfile(path):
                fails.append("E_ACF9 %s missing at %s" % (key, path))
                continue
            now = sha256(read_bytes(path))
            if now != recorded_sources[key]:
                fails.append(
                    "E_ACF9 %s changed since the render (%s vs %s):"
                    " re-render required"
                    % (key, str(recorded_sources[key])[:12], now[:12]))
        extra = sorted(k for k in recorded_sources if k not in SOURCE_KEYS)
        if extra:
            fails.append("E_ACF9 source_sha256 has unknown keys %r" % extra)

    # ACF10 the date sits between the day the stamp shipped and the local day
    if date_ok:
        if stamp < STAMP_FLOOR:
            fails.append("E_ACF10 rendered_on %s predates the stamp (%s)"
                         % (stamp, STAMP_FLOOR))
        today = datetime.date.today().isoformat()
        if stamp > today:
            fails.append("E_ACF10 rendered_on %s is in the future"
                         " (machine local day %s)" % (stamp, today))

    return {
        "schema": schema,
        "printed": printed,
        "stamp": stamp,
        "html_bytes": len(raw_html),
        "json_bytes": len(raw_json),
        "sizes": sizes,
        "how": how,
        "fails": fails,
    }


def check_frozen_untouched(before):
    after = frozen_snapshot(paths()["freeze"])
    if after is None or before is None:
        return ["E_ACF7 freeze manifest unreadable"]
    moved = [rel for rel in before if before[rel] != after.get(rel)]
    return ["E_ACF7 frozen face %s moved" % rel for rel in moved]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="read-only verification of AC-ACF1..10")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-repro", action="store_true",
                        help="skip the render (ACF5) for a quick reading")
    parser.add_argument("--root", default=None,
                        help="operate on another tree (negative controls)")
    args = parser.parse_args(argv)
    if not args.check:
        parser.print_usage(sys.stderr)
        return 2
    if args.root:
        set_root(args.root)
    p = paths()
    frozen_before = frozen_snapshot(p["freeze"])
    stamp_before = {}
    for key in ("html", "json"):
        raw = read_bytes(p[key])
        stamp_before[key] = (len(raw), sha256(raw), os.stat(p[key]).st_mtime_ns)
    reading = check()
    fails = list(reading["fails"])
    if args.no_repro:
        fails = [row for row in fails if "E_ACF5" not in row]
    stamp_after = {}
    for key in ("html", "json"):
        raw = read_bytes(p[key])
        stamp_after[key] = (len(raw), sha256(raw), os.stat(p[key]).st_mtime_ns)
    if stamp_before != stamp_after:
        fails.append("E_ACF7 --check modified the artifacts it graded")
    fails.extend(check_frozen_untouched(frozen_before))

    if args.json:
        print(json.dumps({"schema": reading["schema"],
                          "printed": reading["printed"],
                          "stamp": reading["stamp"],
                          "how": reading["how"],
                          "fails": fails}, sort_keys=True))
    else:
        print("API MARKET CURRENT FACE CHECK schema=%s printed=%s stamp=%s"
              " html=%dB json=%dB injection=%s fails=%d"
              % (reading["schema"], reading["printed"], reading["stamp"],
                 reading["html_bytes"], reading["json_bytes"],
                 reading["how"], len(fails)))
        for row in fails:
            print("  %s" % row)
    if not fails:
        print("VERDICT PASS criteria=10")
        return 0
    print("VERDICT FAIL")
    return 2


if __name__ == "__main__":
    sys.exit(main())
