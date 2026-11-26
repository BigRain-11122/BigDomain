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

import contextlib
import datetime
import hashlib
import io
import json
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


def plus_one_second(stamp):
    """Arithmetic on a landed stamp, not a clock read: the pinned second must
    be load-bearing, so the negative control needs the neighbouring second."""
    return stamp[:-3] + "%02d" % ((int(stamp[-3:-1]) + 1) % 60) + stamp[-1]


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
    # a synthetic producer that can only write where it likes. R3505: a replay
    # face is graded by AC-PPR9 instead - its producer is a browser shoot, so
    # "render into a scratch directory" is not the shape it can honour.
    rendered_faces = [f for f in FPR.FACES if not f.get("replay")]
    discipline = {f["slug"]: FPR.output_discipline(f) for f in rendered_faces}
    stub = "import os\n\n\ndef main():\n    return 0\n"
    stub_problems = FPR.evaluate_output_discipline(stub, "apimarket-report-questions")
    ok("AC-PPR7",
       all(not v for v in discipline.values()) and len(discipline) == len(rendered_faces)
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

    # AC-PPR9: a live-shoot face is graded by replay, not by a re-shoot. Four
    # things must hold: the page half is rebuilt from the landed report by the
    # producer's own gallery (no browser, no clock), the same report renders the
    # same bytes into two different scratch directories (position independence,
    # which is why the page takes a page_dir), the only tolerated difference is
    # the channel's own shelf stamp - and that tolerance is narrow, because one
    # changed field in the report still reads drift.
    replay_face = [f for f in FPR.FACES if f.get("replay")]
    replay_row = [r for r in rows if r.get("replay")]
    live_html = os.path.join(PREVIEW, "live-sandbox.html")
    live_json = os.path.join(PREVIEW, "live-sandbox.json")
    sig_live_html = sig(live_html)
    sig_live_json = sig(live_json)
    position_ok = narrow_ok = named_ok = False
    ctx = ""
    if replay_face and replay_row:
        face = replay_face[0]
        report = read_bytes(live_json)
        work_a = tempfile.mkdtemp(prefix="fpr3505a-")
        work_b = tempfile.mkdtemp(prefix="fpr3505b-")
        try:
            html_a, _ = FPR.replay_render(face, work_a, report, read_bytes(live_html))
            html_b, _ = FPR.replay_render(face, work_b, report, read_bytes(live_html))
            position_ok = html_a == html_b
            named_ok = b"src='live/hub.png'" in html_a
            neg = json.loads(report.decode("utf-8"))
            neg["shots"][0]["status"] = 599
            html_neg, _ = FPR.replay_render(
                face, work_a, json.dumps(neg).encode("utf-8"), read_bytes(live_html))
            text_neg, _how = FPR.face_backhop.inject_text(
                html_neg.decode("utf-8"), "live-sandbox.html")
            landed_live = read_bytes(live_html)
            narrow_ok = (FPR.shelf_normalised(text_neg.encode("utf-8"))
                         != FPR.shelf_normalised(landed_live))
            ctx = "pos=%s named=%s narrow=%s" % (position_ok, named_ok, narrow_ok)
        finally:
            shutil.rmtree(work_a, ignore_errors=True)
            shutil.rmtree(work_b, ignore_errors=True)
    live_row = [r for r in replay_row if r["slug"] == "live-sandbox"]
    ok("AC-PPR9",
       bool(replay_face) and bool(live_row)
       and live_row[0]["verdict"] == "one-derivation"
       and live_row[0].get("receipt") == "channel-shelf-stamp"
       and isinstance(live_row[0].get("shelf_stamp_landed"), int)
       and isinstance(live_row[0].get("shelf_stamp_now"), int)
       and not live_row[0].get("replay") is None
       and position_ok and named_ok and narrow_ok
       and sig(live_html) == sig_live_html and sig(live_json) == sig_live_json,
       "replay_faces=%d verdict=%s receipt=%s shelf=%s->%s %s untouched=%s"
       % (len(replay_face), live_row[0]["verdict"] if live_row else "-",
          live_row[0].get("receipt") if live_row else "-",
          live_row[0].get("shelf_stamp_landed") if live_row else "-",
          live_row[0].get("shelf_stamp_now") if live_row else "-", ctx,
          sig(live_html) == sig_live_html and sig(live_json) == sig_live_json))

    # AC-PPR10: a live-run producer is replayed from the report it shipped
    # beside, and the claim is two half-claims: the page equals the producer's
    # render plus the shipped channel block up to the channel's own shelf
    # stamp, AND the report half reproduces the landed json byte for byte once
    # the working tree's newline is adopted. The second half is the strongest
    # reading any face on this page has, so it is pinned rather than described.
    # Negative control: one changed fact in the report still reads drift.
    facts_faces = [f for f in FPR.FACES
                   if (f.get("replay") or {}).get("kind") == "facts-report"]
    facts_rows = [r for r in rows if r.get("replay") == "render_html-from-report"]
    facts_html = os.path.join(PREVIEW, "city-face-report.html")
    facts_json = os.path.join(PREVIEW, "city-face-report.json")
    sig_facts_html = sig(facts_html)
    sig_facts_json = sig(facts_json)
    facts_position = facts_narrow = False
    fctx = ""
    if facts_faces:
        face = facts_faces[0]
        report = read_bytes(facts_json)
        page = read_bytes(facts_html)
        work_c = tempfile.mkdtemp(prefix="fpr3506a-")
        work_d = tempfile.mkdtemp(prefix="fpr3506b-")
        try:
            html_c, json_c = FPR.replay_render(face, work_c, report, page)
            html_d, json_d = FPR.replay_render(face, work_d, report, page)
            facts_position = html_c == html_d and json_c == json_d
            neg = json.loads(report.decode("utf-8"))
            neg["facts"]["compliance"]["ai_label"] = "PROBE"
            html_neg, _ = FPR.replay_render(
                face, work_c, json.dumps(neg, ensure_ascii=False).encode("utf-8"), page)
            text_neg, _how = FPR.face_backhop.inject_text(
                html_neg.decode("utf-8"), "city-face-report.html")
            facts_narrow = (FPR.shelf_normalised(text_neg.encode("utf-8"))
                            != FPR.shelf_normalised(page))
            fctx = "pos=%s narrow=%s json_same=%s" % (
                facts_position, facts_narrow,
                bool(facts_rows) and facts_rows[0].get("json_same_as_render"))
        finally:
            shutil.rmtree(work_c, ignore_errors=True)
            shutil.rmtree(work_d, ignore_errors=True)
    ok("AC-PPR10",
       bool(facts_faces) and bool(facts_rows)
       and facts_rows[0]["verdict"] == "one-derivation"
       and facts_rows[0].get("receipt") == "channel-shelf-stamp"
       and facts_rows[0].get("json_same_as_render") is True
       and facts_rows[0].get("rendered_json_bytes") == facts_rows[0].get("landed_json_bytes")
       and facts_position and facts_narrow
       and sig(facts_html) == sig_facts_html and sig(facts_json) == sig_facts_json,
       "facts_faces=%d verdict=%s receipt=%s %s untouched=%s"
       % (len(facts_faces), facts_rows[0]["verdict"] if facts_rows else "-",
          facts_rows[0].get("receipt") if facts_rows else "-", fctx,
          sig(facts_html) == sig_facts_html and sig(facts_json) == sig_facts_json))

    # AC-PPR11: a producer that reads live inputs and prints its own byte sizes
    # into BOTH halves cannot be compared against one self-reference - the
    # landed page keeps the pre-channel pair (3911/2600, LF) while the landed
    # report keeps the post-channel pair (4593/2701, working-tree CRLF). The
    # replay therefore reads the sizes OFF THE LANDED PAGE, and the report half
    # must still equal the landed bytes after the working-tree newline and the
    # channel's size patch. Negative control: one changed carrier fact reads
    # drift, so the tolerance cannot hide a real difference.
    doc_faces = [f for f in FPR.FACES
                 if (f.get("replay") or {}).get("kind") == "landed-document"]
    doc_rows = [r for r in rows if r.get("replay") == "render_html-from-landed-document"]
    doc_html = os.path.join(PREVIEW, "first-yuan.html")
    doc_json = os.path.join(PREVIEW, "first-yuan.json")
    sig_doc_html = sig(doc_html)
    sig_doc_json = sig(doc_json)
    doc_position = doc_narrow = doc_stamp = False
    dctx = ""
    if doc_faces:
        face = doc_faces[0]
        report = read_bytes(doc_json)
        page = read_bytes(doc_html)
        work_e = tempfile.mkdtemp(prefix="fpr3507a-")
        work_f = tempfile.mkdtemp(prefix="fpr3507b-")
        try:
            html_e, json_e = FPR.replay_render(face, work_e, report, page)
            html_f, json_f = FPR.replay_render(face, work_f, report, page)
            doc_position = html_e == html_f and json_e == json_f
            stamp = FPR.self_sizes_from_page(page)
            doc_stamp = (stamp is not None
                         and len(html_e) == stamp["html"])
            neg = json.loads(report.decode("utf-8").replace("\r\n", "\n"))
            neg["carriers"][0]["state"] = "verdict=PROBE"
            probe = (json.dumps(neg, ensure_ascii=False, indent=2, sort_keys=True)
                     + "\n").encode("utf-8")
            html_neg, _ = FPR.replay_render(face, work_e, probe, page)
            text_neg, _how = FPR.face_backhop.inject_text(
                html_neg.decode("utf-8"), "first-yuan.html")
            doc_narrow = (FPR.shelf_normalised(text_neg.encode("utf-8"))
                          != FPR.shelf_normalised(page))
            dctx = "pos=%s stamp=%s narrow=%s json_same=%s" % (
                doc_position, doc_stamp, doc_narrow,
                bool(doc_rows) and doc_rows[0].get("json_same_as_render"))
        finally:
            shutil.rmtree(work_e, ignore_errors=True)
            shutil.rmtree(work_f, ignore_errors=True)
    ok("AC-PPR11",
       bool(doc_faces) and bool(doc_rows)
       and doc_rows[0]["verdict"] == "one-derivation"
       and doc_rows[0].get("receipt") == "channel-shelf-stamp"
       and doc_rows[0].get("json_same_as_render") is True
       and doc_rows[0].get("rendered_json_bytes") == doc_rows[0].get("landed_json_bytes")
       and doc_position and doc_stamp and doc_narrow
       and sig(doc_html) == sig_doc_html and sig(doc_json) == sig_doc_json,
       "doc_faces=%d verdict=%s receipt=%s %s untouched=%s"
       % (len(doc_faces), doc_rows[0]["verdict"] if doc_rows else "-",
          doc_rows[0].get("receipt") if doc_rows else "-", dctx,
          sig(doc_html) == sig_doc_html and sig(doc_json) == sig_doc_json))

    # AC-PPR12: a facts-report face whose page carries NO loopback port stamp
    # (R3509, membership-benefit-report). AC-PPR10 pinned the port as mandatory,
    # which graded a producer that measures its world in process as
    # unreproducible for a shape difference rather than a derivation gap. The
    # relaxation is narrow and pinned here: a face that declares port=False may
    # only use the stamps its own landed report records, every declared key must
    # be present (a report missing one is refused, not replayed with a guess),
    # and a face that declares port=True still refuses a page without its port.
    naked = [f for f in FPR.FACES
             if (f.get("replay") or {}).get("kind") == "facts-report"
             and not f["replay"].get("port", True)]
    naked_rows = [r for r in rows if r.get("slug") in [f["slug"] for f in naked]]
    naked_html = os.path.join(PREVIEW, naked[0]["slug"] + ".html") if naked else None
    naked_json = os.path.join(PREVIEW, naked[0]["slug"] + ".json") if naked else None
    sig_nh = sig(naked_html) if naked_html else None
    sig_nj = sig(naked_json) if naked_json else None
    naked_stamps = naked_refuse = port_still_required = False
    nctx = "no portless face"
    if naked:
        face = naked[0]
        report = read_bytes(naked_json)
        page = read_bytes(naked_html)
        work_g = tempfile.mkdtemp(prefix="fpr3509a-")
        work_h = tempfile.mkdtemp(prefix="fpr3509b-")
        try:
            html_g, json_g = FPR.replay_render(face, work_g, report, page)
            html_h, json_h = FPR.replay_render(face, work_h, report, page)
            position = html_g == html_h and json_g == json_h
            want = ["generated_utc"] + list(face["replay"].get("stamp_keys") or [])
            naked_stamps = (bool(naked_rows) and position
                            and naked_rows[0].get("replay_stamps") == want
                            and naked_rows[0]["verdict"] == "one-derivation"
                            and naked_rows[0].get("json_same_as_render") is True
                            and naked_rows[0].get("rendered_json_bytes")
                            == naked_rows[0].get("landed_json_bytes"))
            broken = json.loads(report.decode("utf-8").replace("\r\n", "\n"))
            for key in face["replay"].get("stamp_keys") or []:
                broken.pop(key, None)
            try:
                FPR.replay_render(face, work_g,
                                  json.dumps(broken, ensure_ascii=False).encode("utf-8"),
                                  page)
                naked_refuse = False
            except ValueError:
                naked_refuse = True
            nctx = "stamps=%s pos=%s refuse=%s json_same=%s" % (
                naked_rows[0].get("replay_stamps") if naked_rows else "-", position,
                naked_refuse,
                bool(naked_rows) and naked_rows[0].get("json_same_as_render"))
        finally:
            shutil.rmtree(work_g, ignore_errors=True)
            shutil.rmtree(work_h, ignore_errors=True)
    ported = [f for f in FPR.FACES
              if (f.get("replay") or {}).get("kind") == "facts-report"
              and f["replay"].get("port", True)]
    if ported:
        face = ported[0]
        work_i = tempfile.mkdtemp(prefix="fpr3509c-")
        try:
            ported_page = read_bytes(os.path.join(PREVIEW, face["slug"] + ".html"))
            ported_json = read_bytes(os.path.join(PREVIEW, face["slug"] + ".json"))
            stripped = re.sub(rb"127\.0\.0\.1:\d+", b"127.0.0.1", ported_page)
            try:
                FPR.replay_render(face, work_i, ported_json, stripped)
                port_still_required = False
            except ValueError:
                port_still_required = True
        finally:
            shutil.rmtree(work_i, ignore_errors=True)
    ok("AC-PPR12",
       bool(naked) and bool(naked_rows) and naked_stamps and naked_refuse
       and port_still_required
       and sig(naked_html) == sig_nh and sig(naked_json) == sig_nj,
       "portless=%d %s port_required=%s untouched=%s"
       % (len(naked), nctx, port_still_required,
          naked_html is not None and sig(naked_html) == sig_nh
          and sig(naked_json) == sig_nj))

    # AC-PPR13: a producer whose every tx id is a content hash over the write
    # second (ledger_business_report) cannot be reproduced by a later run unless
    # the ledger clock is pinned to the second its own landed report records.
    # The arm proves the pin is load-bearing rather than decorative: the same
    # replay one second later must NOT reproduce the three landed tx ids, and a
    # report that carries no clock stamp is refused by name.
    clock_faces = [f for f in FPR.FACES
                   if (f.get("replay") or {}).get("kind") == "clock-identity"]
    clock_rows = [r for r in rows
                  if (r.get("replay") or "").endswith("-clock-pin")]
    clock_html = os.path.join(PREVIEW, "ledger-business-report.html")
    clock_json = os.path.join(PREVIEW, "ledger-business-report.json")
    sig_ch = sig(clock_html)
    sig_cj = sig(clock_json)
    c_pin = c_ids = c_narrow = c_refuse = False
    cctx = ""
    if clock_faces:
        face = clock_faces[0]
        page = read_bytes(clock_html)
        report = read_bytes(clock_json)
        doc_c = json.loads(report.decode("utf-8").replace("\r\n", "\n"))
        work_j = tempfile.mkdtemp(prefix="fpr3510a-")
        work_k = tempfile.mkdtemp(prefix="fpr3510b-")
        try:
            html_j, json_j = FPR.replay_render(face, work_j, report, page)
            html_k, json_k = FPR.replay_render(face, work_k, report, page)
            pin_name = "generated_utc=%s (clock pin)" % doc_c["generated_utc"]
            c_pin = (html_j == html_k and json_j == json_k and bool(clock_rows)
                     and clock_rows[0].get("replay_stamps") == [pin_name])
            landed_ids = set(re.findall(r"<code>([0-9a-f]{12})</code>",
                                        page.decode("utf-8")))
            shown_ids = set(re.findall(r"<code>([0-9a-f]{12})</code>",
                                       html_j.decode("utf-8")))
            c_ids = bool(landed_ids) and landed_ids == shown_ids
            shifted = dict(doc_c)
            shifted["generated_utc"] = plus_one_second(doc_c["generated_utc"])
            probe = (json.dumps(shifted, ensure_ascii=False, indent=1)
                     + "\n").encode("utf-8")
            html_n, _json_n = FPR.replay_render(face, work_j, probe, page)
            neg_ids = set(re.findall(r"<code>([0-9a-f]{12})</code>",
                                     html_n.decode("utf-8")))
            c_narrow = bool(landed_ids) and neg_ids != landed_ids
            naked = dict(doc_c)
            naked.pop("generated_utc", None)
            try:
                FPR.replay_render(face, work_j,
                                  json.dumps(naked, ensure_ascii=False).encode("utf-8"),
                                  page)
                c_refuse = False
            except ValueError:
                c_refuse = True
            cctx = "pin=%s ids=%d narrow=%s refuse=%s row=%s" % (
                c_pin, len(landed_ids), c_narrow, c_refuse,
                clock_rows[0].get("replay_stamps") if clock_rows else "-")
        finally:
            shutil.rmtree(work_j, ignore_errors=True)
            shutil.rmtree(work_k, ignore_errors=True)
    ok("AC-PPR13",
       bool(clock_faces) and bool(clock_rows)
       and clock_rows[0]["verdict"] == "one-derivation"
       and clock_rows[0].get("receipt") == "channel-shelf-stamp"
       and clock_rows[0].get("json_same_as_render") is True
       and clock_rows[0].get("rendered_json_bytes") == clock_rows[0].get("landed_json_bytes")
       and c_pin and c_ids and c_narrow and c_refuse
       and sig(clock_html) == sig_ch and sig(clock_json) == sig_cj,
       "clock_faces=%d verdict=%s receipt=%s %s untouched=%s"
       % (len(clock_faces), clock_rows[0]["verdict"] if clock_rows else "-",
          clock_rows[0].get("receipt") if clock_rows else "-", cctx,
          sig(clock_html) == sig_ch and sig(clock_json) == sig_cj))

    # AC-PPR14 (R3512, payment-gate-report): a producer whose clock is read from
    # TWO packages - its own generated_utc stamp and the stale-timestamp refusals
    # inside the shipped payment sandbox - is reproduced only when BOTH are
    # pinned to the second the landed report records. The arm proves the second
    # clock is load-bearing (pinning only the producer leaves the stale-delta
    # text different from the landed report), that a one-second shift reddens
    # the pair, and that the report's self-stamps (two sizes, the producer's own
    # source sha256) are recorded rather than equalised.
    pin_faces = [f for f in FPR.FACES
                 if (f.get("replay") or {}).get("kind") == "clock-pin"]
    pin_rows = [r for r in rows
                if (r.get("replay") or "").endswith("-two-clock-pin")]
    pin_html = os.path.join(PREVIEW, "payment-gate-report.html")
    pin_json = os.path.join(PREVIEW, "payment-gate-report.json")
    sig_ph = sig(pin_html)
    sig_pj = sig(pin_json)
    p_ok = p_two = p_narrow = p_honest = False
    pctx = ""
    if pin_faces:
        face = pin_faces[0]
        page = read_bytes(pin_html)
        report = read_bytes(pin_json)
        doc_p = json.loads(report.decode("utf-8").replace("\r\n", "\n"))
        work_p = tempfile.mkdtemp(prefix="fpr3512-")
        try:
            html_p, json_p = FPR.replay_render(face, work_p, report, page)
            html_q, json_q = FPR.replay_render(face, work_p, report, page)
            p_two = (html_p == html_q and json_p == json_q)
            # Narrowness: one second later is a different report.
            shifted = dict(doc_p)
            shifted["generated_utc"] = plus_one_second(doc_p["generated_utc"])
            _h, json_s = FPR.replay_render(
                face, work_p,
                (json.dumps(shifted, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                page)
            p_narrow = json_s != json_p
            # The second clock: pin only the producer and the stale-delta text
            # that the sandbox computes must stop matching the landed report.
            module = FPR.load_module(os.path.join(ROOT, face["producer"]),
                                     "fpr3512_single")
            import adapters
            stamp = doc_p["generated_utc"]
            single = os.path.join(work_p, "single")
            os.makedirs(single, exist_ok=True)
            real_sandbox_now = adapters.now_utc
            original_now = module._now
            module._now = lambda: datetime.datetime.strptime(
                stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    module.main(["--out", os.path.join(single, "s.html"),
                                 "--json", os.path.join(single, "s.json")])
            finally:
                module._now = original_now
                adapters.now_utc = real_sandbox_now
            one = json.loads(read_bytes(os.path.join(single, "s.json")).decode("utf-8"))
            landed_stale = doc_p["legacy_negative"][2]["detail"]
            single_stale = one["legacy_negative"][2]["detail"]
            p_ok = single_stale != landed_stale
            p_honest = (pin_rows and pin_rows[0].get("json_same_as_render") is False
                        and set((pin_rows[0].get("self_stamps") or {}).keys())
                        == {"landed", "rendered"}
                        and pin_rows[0]["self_stamps"]["landed"]["sizes"]
                        != pin_rows[0]["self_stamps"]["rendered"]["sizes"])
            pctx = "two=%s narrow=%s single_clock_differs=%s honest=%s" % (
                p_two, p_narrow, p_ok, p_honest)
        finally:
            shutil.rmtree(work_p, ignore_errors=True)
    ok("AC-PPR14",
       bool(pin_faces) and bool(pin_rows)
       and pin_rows[0]["verdict"] == "one-derivation"
       and pin_rows[0].get("receipt") == "channel-shelf-stamp"
       and p_two and p_narrow and p_ok and p_honest
       and sig(pin_html) == sig_ph and sig(pin_json) == sig_pj,
       "pin_faces=%d verdict=%s %s untouched=%s"
       % (len(pin_faces), pin_rows[0]["verdict"] if pin_rows else "-", pctx,
          sig(pin_html) == sig_ph and sig(pin_json) == sig_pj))

    # AC-PPR15 (R3513, platform-live-report): a live-run report whose facts sit
    # at the TOP level and which carries no evidence block at all. Four arms:
    # the replay is stable across two reads; the report's own fingerprint (which
    # pins what the run proved and never the ephemeral ports) is reproduced from
    # the landed facts; a moved port that is NOT the hub still reddens the pair
    # (so the fingerprint pin is not doing the comparison's work for it); and a
    # hub port the landed page never printed is refused rather than guessed.
    spread_faces = [f for f in FPR.FACES
                    if (f.get("replay") or {}).get("kind") == "facts-spread-report"]
    spread_rows = [r for r in rows
                   if (r.get("replay") or "").endswith("-from-report-facts-spread")]
    spread_html = os.path.join(PREVIEW, "platform-live-report.html")
    spread_json = os.path.join(PREVIEW, "platform-live-report.json")
    sig_sh = sig(spread_html)
    sig_sj = sig(spread_json)
    s_repeat = s_fp = s_narrow = s_refuse = False
    sctx = ""
    if spread_faces:
        face = spread_faces[0]
        page = read_bytes(spread_html)
        report = read_bytes(spread_json)
        doc_s = json.loads(report.decode("utf-8"))
        work_s = tempfile.mkdtemp(prefix="fpr3513-")
        try:
            html_s, json_s = FPR.replay_render(face, work_s, report, page)
            html_t, json_t = FPR.replay_render(face, work_s, report, page)
            s_repeat = (html_s == html_t and json_s == json_t)
            s_fp = (json.loads(json_s.decode("utf-8")).get("fingerprint")
                    == doc_s.get("fingerprint"))
            moved = json.loads(json.dumps(doc_s))
            moved["ports"]["web"] = int(moved["ports"]["web"]) + 1
            _h, json_m = FPR.replay_render(
                face, work_s,
                (json.dumps(moved, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
                page)
            s_narrow = json_m != json_s
            unprinted = json.loads(json.dumps(doc_s))
            unprinted["ports"]["hub"] = 1
            try:
                FPR.replay_render(
                    face, work_s,
                    (json.dumps(unprinted, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
                    page)
                s_refuse = False
            except ValueError:
                s_refuse = True
            sctx = "repeat=%s fingerprint=%s narrow=%s refuse=%s row_fp=%s" % (
                s_repeat, s_fp, s_narrow, s_refuse,
                spread_rows[0].get("fingerprint_same") if spread_rows else "-")
        finally:
            shutil.rmtree(work_s, ignore_errors=True)
    ok("AC-PPR15",
       bool(spread_faces) and bool(spread_rows)
       and spread_rows[0]["verdict"] == "one-derivation"
       and spread_rows[0].get("receipt") == "channel-shelf-stamp"
       and spread_rows[0].get("fingerprint_same") is True
       and spread_rows[0].get("json_same_as_render") is True
       and s_repeat and s_fp and s_narrow and s_refuse
       and sig(spread_html) == sig_sh and sig(spread_json) == sig_sj,
       "spread_faces=%d verdict=%s %s untouched=%s"
       % (len(spread_faces), spread_rows[0]["verdict"] if spread_rows else "-",
          sctx, sig(spread_html) == sig_sh and sig(spread_json) == sig_sj))

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
