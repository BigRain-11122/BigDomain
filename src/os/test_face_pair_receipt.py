"""Battery suite for the per-face pair receipt - AC-PPR1..AC-PPR7 (R3500, R3501).

Six arms were pinned in src/os/backlog.md at R3500 BEFORE tools/face_pair_receipt.py
existed, and AC-PPR7 was pinned at R3501 before the second face was registered:
a producer may only be receipted when it can render into a scratch directory
without touching the tree. The suite exists because the board's question ("is
this pair one derivation, or must it be re-derived?") can only be answered by
three readings a reader can re-check: the producer's own html, that html plus
the shipped post-render channel, and the landed bytes.

Nothing here rewrites a preview page. The tool renders into the system temp
directory; --check re-derives both receipt halves in memory and compares.

Source discipline: pure ASCII, stdlib only, no clock read of its own, no
network, no shell.
"""

import hashlib
import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
TOOL = os.path.join(TOOLS, "face_pair_receipt.py")
PREVIEW = os.path.join(ROOT, "preview")
JSON_HALF = os.path.join(PREVIEW, "face-pair-receipt.json")
HTML_HALF = os.path.join(PREVIEW, "face-pair-receipt.html")
CENSUS_JSON = os.path.join(PREVIEW, "preview-pair-census.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
FACE_HTML = os.path.join(PREVIEW, "apimarket-report-refunds.html")
FACE_JSON = os.path.join(PREVIEW, "apimarket-report-refunds.json")
sys.path.insert(0, TOOLS)

import face_pair_receipt as FPR  # noqa: E402
import preview_pair_census as PPC  # noqa: E402

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
        print("FAIL %s %s" % (name, detail))
    else:
        print("PASS %s %s" % (name, detail))


def read_bytes(path):
    with io.open(path, "rb") as f:
        return f.read()


def sig(path):
    try:
        data = read_bytes(path)
    except OSError:
        return None
    return (len(data), hashlib.sha256(data).hexdigest()[:16])


def main():
    sig_tool = sig(TOOL)
    sig_json = sig(JSON_HALF)
    sig_html = sig(HTML_HALF)
    sig_census = sig(CENSUS_JSON)
    sig_state = sig(STATE)
    sig_face_html = sig(FACE_HTML)
    sig_face_json = sig(FACE_JSON)

    payload = FPR.receipt()
    rows = payload["faces"]
    row = rows[0]
    landed = read_bytes(FACE_HTML)

    # AC-PPR1: the three readings exist and are numbers a reader can re-check.
    ok("AC-PPR1",
       row["rendered_html_bytes"] > 0 and len(row["rendered_html_sha256"]) == 64
       and row["spliced_html_bytes"] > 0 and len(row["spliced_html_sha256"]) == 64
       and row["landed_html_bytes"] == len(landed)
       and row["landed_html_sha256"] == hashlib.sha256(landed).hexdigest()
       and row.get("channel_block_bytes", 0) > 0,
       "rendered=%d spliced=%d landed=%d block=%d"
       % (row["rendered_html_bytes"], row["spliced_html_bytes"],
          row["landed_html_bytes"], row.get("channel_block_bytes", 0)))

    # AC-PPR2: the verdict follows from the readings, and the recorded json is
    # the landed json (a receipt describing other bytes is not a receipt).
    same = row["spliced_html_sha256"] == row["landed_html_sha256"]
    ok("AC-PPR2",
       row["verdict"] in ("one-derivation", "version-drift", "drift", "channel-noop")
       and (row["verdict"] == "one-derivation") == same
       and row["landed_json_sha256"] == hashlib.sha256(read_bytes(FACE_JSON)).hexdigest(),
       "verdict=%s spliced_equals_landed=%s" % (row["verdict"], same))

    # AC-PPR3: negative control - the un-injected render must differ from the
    # landed page (the comparison is not trivially true), and the channel must
    # splice exactly the block it measured, so "byte for byte" is not empty.
    splice = row["splice_offset"]
    raw = row["raw_first_diff_offset"]
    splice_ok = False
    work = tempfile.mkdtemp(prefix="fpr3500-")
    try:
        try:
            rendered_text, _ = FPR.render(FPR.FACES[0], work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    except Exception:
        rendered_text = None
    if rendered_text is not None and splice is not None:
        channel, _how = FPR.face_backhop.inject_text(
            rendered_text.decode("utf-8"), row["slug"] + ".html")
        block = channel.encode("utf-8")[splice:splice + row["channel_block_bytes"]]
        rebuilt = (rendered_text[:splice] + block + rendered_text[splice:])
        splice_ok = (raw is not None and raw >= 0
                     and len(block) == row["channel_block_bytes"]
                     and hashlib.sha256(rebuilt).hexdigest() == row["spliced_html_sha256"])
    ok("AC-PPR3", splice_ok,
       "raw_first_diff=%s splice=%s block=%d spliced_sha=%s"
       % (raw, splice, row.get("channel_block_bytes", 0), row["spliced_html_sha256"][:12]))

    # AC-PPR4: read-only run and a source that cannot reach the network or a
    # child process (the "no git, no shell" promise is scanned, not promised).
    source = io.open(TOOL, encoding="utf-8").read()
    banned = [m for m in ("import subprocess", "import socket", "import urllib",
                          "import http", "os.system", "os.popen") if m in source]
    rc = FPR.main(["--check"])
    same_after = (sig(TOOL) == sig_tool and sig(JSON_HALF) == sig_json
                  and sig(HTML_HALF) == sig_html and sig(CENSUS_JSON) == sig_census
                  and sig(STATE) == sig_state and sig(FACE_HTML) == sig_face_html
                  and sig(FACE_JSON) == sig_face_json)
    ok("AC-PPR4", rc == 0 and not banned and same_after,
       "check_rc=%d banned=%s repo_untouched=%s" % (rc, banned, same_after))

    # AC-PPR5: the census link works both ways - a receipt that reproduces the
    # landed bytes excuses the split, and one that only explains it must not.
    census = PPC.census()
    census_row = [r for r in census["pairs"] if r["name"] == row["slug"]][0]
    landed_sha = hashlib.sha256(landed).hexdigest()
    excused = {"verdict": "history-split", "delta_seconds": 9999}
    PPC.apply_receipt(excused, FACE_HTML,
                      {os.path.basename(FACE_HTML): {"verdict": "one-derivation",
                                                     "landed_html_sha256": landed_sha}})
    explained = {"verdict": "history-split", "delta_seconds": 9999}
    PPC.apply_receipt(explained, FACE_HTML,
                      {os.path.basename(FACE_HTML): {"verdict": "version-drift",
                                                     "landed_html_sha256": landed_sha}})
    stale = {"verdict": "history-split", "delta_seconds": 9999}
    PPC.apply_receipt(stale, FACE_HTML,
                      {os.path.basename(FACE_HTML): {"verdict": "one-derivation",
                                                     "landed_html_sha256": "0" * 64}})
    ok("AC-PPR5",
       census_row["verdict"] == "history-split"
       and census_row.get("pair_receipt") == row["verdict"]
       and excused["verdict"] == "channel-receipt"
       and explained["verdict"] == "history-split"
       and stale["verdict"] == "history-split",
       "landed=%s receipt=%s excused=%s explained=%s stale=%s"
       % (census_row["verdict"], census_row.get("pair_receipt"), excused["verdict"],
          explained["verdict"], stale["verdict"]))

    # AC-PPR6: a producer that cannot run is 'unreproducible' and never an
    # excuse; and the receipt page is one derivation with two halves.
    missing = dict(FPR.FACES[0])
    missing = {"slug": "apimarket-report-refunds",
               "producer": os.path.join("src", "os", "no-such-producer-R3500.py"),
               "why": "negative control"}
    unreach = FPR.measure(missing)
    fresh_json = FPR.dumps(payload).encode("utf-8")
    fresh_html = FPR.html_of(payload).encode("utf-8")
    pair_ok = (FPR.normalized(read_bytes(JSON_HALF)) == FPR.normalized(fresh_json)
               and FPR.normalized(read_bytes(HTML_HALF)) == FPR.normalized(fresh_html))
    ok("AC-PPR6", unreach["verdict"] == "unreproducible" and pair_ok
       and re.search(r"\d+\s*B", read_bytes(HTML_HALF).decode("utf-8")) is not None,
       "unreproducible=%s pair=%s" % (unreach["verdict"], pair_ok))

    # AC-PPR7: every registered producer can be rendered into a scratch
    # directory (two defaulted outputs) and its own defaults still name the
    # landed halves, so a no-argument run is unchanged; the negative control is
    # a synthetic producer that can only write where it likes.
    discipline = {f["slug"]: FPR.output_discipline(f) for f in FPR.FACES}
    stub = "import os\n\n\ndef main():\n    return 0\n"
    stub_problems = FPR.evaluate_output_discipline(stub, "apimarket-report-questions")
    ok("AC-PPR7",
       all(not v for v in discipline.values()) and len(discipline) == len(FPR.FACES)
       and bool(stub_problems),
       "faces=%s stub_refused=%s" % (sorted(discipline), bool(stub_problems)))

    # AC-PPR8: a producer that applies the channel itself is compared directly.
    # Measured on the fifth face (a live sandbox session): its own html must
    # equal the landed page, and one byte changed OUTSIDE the block must still
    # read drift at that exact offset - the direct comparison is not a formality.
    applied = [r for r in rows if r.get("splice_offset") is None]
    fifth = [r for r in rows if r["slug"] == "lobby-session-trace"]
    verdict_a = offset_a = verdict_b = offset_b = None
    if fifth:
        landed5 = read_bytes(os.path.join(PREVIEW, "lobby-session-trace.html"))
        work = tempfile.mkdtemp(prefix="fpr3504-")
        try:
            try:
                rendered5, _ = FPR.render([f for f in FPR.FACES
                                           if f["slug"] == "lobby-session-trace"][0], work)
            finally:
                shutil.rmtree(work, ignore_errors=True)
        except Exception:
            rendered5 = None
        if rendered5 is not None:
            verdict_a, offset_a = FPR.applied_channel_verdict(rendered5, landed5)
            tampered = bytearray(landed5)
            tampered[10] = tampered[10] ^ 0x01
            verdict_b, offset_b = FPR.applied_channel_verdict(rendered5, bytes(tampered))
    ok("AC-PPR8",
       bool(applied) and fifth and fifth[0]["verdict"] == "one-derivation"
       and fifth[0].get("receipt") == "producer-applies-channel"
       and verdict_a == "one-derivation" and offset_a is None
       and verdict_b == "drift" and offset_b == 10,
       "applied_faces=%d fifth=%s direct=%s@%s tampered=%s@%s"
       % (len(applied), fifth[0]["verdict"] if fifth else "-", verdict_a, offset_a,
          verdict_b, offset_b))

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
