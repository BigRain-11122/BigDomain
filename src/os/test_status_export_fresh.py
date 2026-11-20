"""Battery suite for tools/status_export_fresh.py - criteria AC-SXFB1..AC-SXFB16.

WHY THIS SUITE EXISTS (measured at R2821, not hypothesised): the CEO three-line
face read VERDICT R2820 PASS while the same document carried two provable
falsehoods - state_bytes=65089 against a real 81159, and a top-level "current"
leading with R2814 against a live R2820 - because check() graded only two of the
three synonym fields and never compared a derived count to its source. A third
of the story was size: one "results" key held 332486 of 372300 bytes, unmaintained
by any round and watched by no gate, so the file the CEO downloads was 89 percent
history nobody reads.

WHAT IS PROVED HERE: each of the new criteria is driven in a PRIVATE world and
each is proved CARRYING WEIGHT by a tamper that it is supposed to catch. A
criterion that stays green on its own tamper is decoration and would be reported
rather than hidden by AC-SXFB2..AC-SXFB6. AC-SXFB7 proves the archive is
lossless (every entry kept, live count equal, no key drift). AC-SXFB8 proves
--check writes nothing. AC-SXFB9 proves the fail-closed path. AC-SXFB10 asserts
the registry row exists, which is the only hook that makes this suite run.

Isolation: the tool's STATE / EXPORT / BACKLOG / PREVIEW / ARCHIVE_DIR / ROOT
globals are rebound to a fresh temp directory and restored in a finally block.
The real docs/status-export.json and src/os/state.json are snapshotted by size
and mtime_ns before and after and must be identical.
"""

import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, BASE)

import status_export_fresh as sx  # noqa: E402

REAL_EXPORT = os.path.join(REPO, "docs", "status-export.json")
REAL_STATE = os.path.join(REPO, "src", "os", "state.json")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

NARRATIVE = "R2821 ENGINEERING: fixture narrative for the private world at length"
LEGACY = [
    {"round": "1001", "text": "first frozen narrative"},
    {"round": "1002", "text": "second frozen narrative"},
    {"round": "1003", "text": "third frozen narrative"},
]

results = []


def record(name, ok, detail):
    results.append((name, ok, detail))
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))


def snapshot(path):
    if not os.path.isfile(path):
        return None
    stat = os.stat(path)
    return (stat.st_size, stat.st_mtime_ns)


def write_json(path, payload):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def build_world(root):
    for part in ("src/os", "docs", "preview", "logs"):
        os.makedirs(os.path.join(root, part), exist_ok=True)
    state = {"tick": 1, "log": [NARRATIVE]}
    write_json(os.path.join(root, "src", "os", "state.json"), state)
    with io.open(os.path.join(root, "preview", "fixture.html"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("<html>fixture</html>\n")
    # AC-SXF13 derives the published pair from src/os/export_round.py, which only
    # accepts a preview/X.html that HAS a sibling X.json - so the fixture world
    # carries the pair, not a lone html (the shape moved with the definition).
    with io.open(os.path.join(root, "preview", "fixture.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("{}\n")
    with io.open(os.path.join(root, "src", "os", "backlog.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("- [ ] [R2821] next window (<=12h): fixture milestone row\n")
    # AC-SXFB14/15: the fixture is a HEALTHY document, so both copies of the two
    # rows that used to be ungraded carry the derived value here. Building the
    # fixture from the derivation (rather than hand-writing a sentence that has to
    # be kept in step) is also what the real writer now does.
    derived_artifact = sx.newest_artifact(os.path.join(root, "preview"))["line"]
    derived_milestone = sx.next_milestone(os.path.join(root, "src", "os", "backlog.md"))["text"]
    doc = {
        "export_ts": "2026-11-16T00:00:00+08:00",
        "do": NARRATIVE,
        "ceo_face": {
            "current": NARRATIVE,
            "latest_artifact": derived_artifact,
            "last_artifact": derived_artifact,
            "latest_artifact_abs": os.path.join(root, "preview", "fixture.html"),
            "next_milestone": derived_milestone,
            "next_milestone_due": "2026-11-16T12:00:00+08:00",
            "updated_at": "2026-11-16T00:00:00+08:00",
        },
        "current": NARRATIVE,
        "latest_artifact": derived_artifact,
        "next_milestone": derived_milestone,
        "next_milestone_due": "2026-11-16T12:00:00+08:00",
        "depts": [],
        "outs": [],
        "results": LEGACY,
        "self_drive": {},
        "state_bytes": os.path.getsize(os.path.join(root, "src", "os", "state.json")),
        "queue": {},
    }
    export = os.path.join(root, "docs", "status-export.json")
    write_json(export, doc)
    return export, doc


def rebind(root):
    saved = {name: getattr(sx, name) for name in
             ("ROOT", "STATE", "EXPORT", "BACKLOG", "PREVIEW", "ARCHIVE_DIR")}
    sx.ROOT = root
    sx.STATE = os.path.join(root, "src", "os", "state.json")
    sx.EXPORT = os.path.join(root, "docs", "status-export.json")
    sx.BACKLOG = os.path.join(root, "src", "os", "backlog.md")
    sx.PREVIEW = os.path.join(root, "preview")
    sx.ARCHIVE_DIR = os.path.join(root, "logs")
    return saved


def restore(saved):
    for name, value in saved.items():
        setattr(sx, name, value)


def run(root):
    export, doc = build_world(root)

    # AC-SXFB2 (AC-SXF6): the third synonym must be graded. Measured both ways.
    rewound = json.loads(json.dumps(doc))
    rewound["current"] = "R2814 ENGINEERING: a sentence six rounds old"
    write_json(export, rewound)
    rc_red = sx.check(export, sx.STATE)
    write_json(export, doc)
    rc_green = sx.check(export, sx.STATE)
    record("AC-SXFB2", rc_red == 2 and rc_green == 0,
           "rewound=%d restored=%d" % (rc_red, rc_green))

    # AC-SXFB3 (AC-SXF7): state_bytes must equal the real size, and --apply recomputes.
    skewed = json.loads(json.dumps(doc))
    skewed["state_bytes"] = int(skewed["state_bytes"]) + 1
    write_json(export, skewed)
    rc_bad = sx.check(export, sx.STATE)
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_fix = sx.check(export, sx.STATE)
    fixed = json.loads(io.open(export, encoding="utf-8").read())
    record("AC-SXFB3", rc_bad == 2 and rc_fix == 0
           and fixed["state_bytes"] == os.path.getsize(sx.STATE),
           "skewed=%d applied=%d state_bytes=%d" % (rc_bad, rc_fix, fixed["state_bytes"]))

    # AC-SXFB4 (AC-SXF8a): a pointer whose sha256 no longer matches disk reddens.
    # Baseline for AC-SXFB7 is the document as it stands IMMEDIATELY before the
    # archive, not the pre-apply fixture: --apply legitimately moves the clock
    # fields, and comparing against the older copy reddened AC-SXFB7 for my own
    # mistake in the first run rather than for a defect in the tool.
    pre_archive = json.loads(io.open(export, encoding="utf-8").read())
    sx.archive_legacy(export, confirm=True)
    doc_now = json.loads(io.open(export, encoding="utf-8").read())
    arc_rel = doc_now["results_archive"]["path"]
    arc_abs = os.path.join(root, arc_rel.replace("/", os.sep))
    arc_bytes = io.open(arc_abs, "rb").read()
    with io.open(arc_abs, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(" ")
    rc_sha = sx.check(export, sx.STATE)
    # Restore the exact bytes, so the next criterion cannot be red for this reason.
    with io.open(arc_abs, "wb") as handle:
        handle.write(arc_bytes)
    record("AC-SXFB4", rc_sha == 2, "tampered archive sha256 rc=%d" % rc_sha)

    # AC-SXFB5 (AC-SXF8b): a pointer to a file that is not there reddens.
    moved = arc_abs + ".moved"
    shutil.move(arc_abs, moved)
    rc_gone = sx.check(export, sx.STATE)
    shutil.move(moved, arc_abs)
    record("AC-SXFB5", rc_gone == 2, "missing archive rc=%d" % rc_gone)

    # AC-SXFB6 (AC-SXF8c): the live file itself must stay under the waterline.
    saved_max = sx.EXPORT_MAX_BYTES
    sx.EXPORT_MAX_BYTES = 8
    rc_big = sx.check(export, sx.STATE)
    sx.EXPORT_MAX_BYTES = saved_max
    record("AC-SXFB6", rc_big == 2, "waterline 8B rc=%d" % rc_big)

    # AC-SXFB7 (AC-SXF9): archiving is lossless and leaves no key drifting.
    archived = json.loads(io.open(arc_abs, encoding="utf-8").read())
    live = json.loads(io.open(export, encoding="utf-8").read())
    kept = archived.get("results") == LEGACY
    counted = live["results_archive"]["count"] == len(LEGACY)
    dropped = "results" not in live
    drifted = [key for key in pre_archive if key != "results" and pre_archive[key] != live.get(key)]
    record("AC-SXFB7", kept and counted and dropped and not drifted,
           "kept=%s count=%s dropped=%s drift=%s"
           % (kept, counted, dropped, drifted or "none"))

    # AC-SXFB8: --check is read-only in the private world.
    before = snapshot(export)
    sx.check(export, sx.STATE)
    record("AC-SXFB8", snapshot(export) == before, "size+mtime unchanged")

    # AC-SXFB9 (AC-SXF5 carry): no narrative round means rc=5 and zero writes.
    write_json(sx.STATE, {"tick": 2, "log": ["a line with no round tag"]})
    before = snapshot(export)
    rc_none = sx.check(export, sx.STATE)
    record("AC-SXFB9", rc_none == 5 and snapshot(export) == before,
           "no-round rc=%d writes=0" % rc_none)

    # AC-SXFB11 (AC-SXF11): the headline wins over a skip marker that merely
    # MENTIONS the phrase. Driven with the exact shape R2822 produced - a fold
    # summary, then the real headline that discusses the fold, then a
    # continuation line - because the old rule demoted the headline to the
    # continuation and the CEO read "how the change was held to its own criteria"
    # as the current line.
    fold_state = {"tick": 3, "log": [
        "2026-11-16 R2821 fold of log items 1..9 (rounds R2820..R2820), moved "
        "verbatim into logs/archive.md; ids carried forward",
        "R2821 ENGINEERING: the round-aligned fold finally ran and the log items "
        "budget moved",
        "R2821 how the change was held to its own criteria: AC-XYZ1..3",
    ]}
    picked_round, picked = sx.newest_round(fold_state)
    record("AC-SXFB11", picked_round == 2821 and picked == fold_state["log"][1],
           "picked=%r" % ((picked or "")[:56],))

    # AC-SXFB12 (AC-SXF12): a continuation line carries the right round tag and
    # used to read PASS. It must redden, and --apply must repair it.
    write_json(sx.STATE, fold_state)
    frag = json.loads(json.dumps(doc))
    fragment = fold_state["log"][2]
    frag["do"] = fragment
    frag["current"] = fragment
    frag["ceo_face"]["current"] = fragment
    write_json(export, frag)
    # The verdict must red FOR THE FRAGMENT, not merely be non-zero for some
    # other reason on the same document, so the printed code is captured.
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc_frag = sx.check(export, sx.STATE)
    said = buffer.getvalue()
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_frag_fixed = sx.check(export, sx.STATE)
    record("AC-SXFB12", rc_frag == 2 and "E_SXF_FRAGMENT" in said
           and rc_frag_fixed == 0,
           "fragment=%d named=%s applied=%d"
           % (rc_frag, "E_SXF_FRAGMENT" in said, rc_frag_fixed))

    # AC-SXFB13 (AC-SXF13): a meta board page must not be published as the CEO's
    # latest artifact, and the exclusion must be IMPORTED from the one shipped
    # definition rather than repeated as names here or in the tool.
    import export_round as er
    for ext in (".html", ".json"):
        path = os.path.join(root, "preview", "face-sweep" + ext)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("<html>board</html>\n" if ext == ".html" else "{}\n")
        future = time.time() + 120
        os.utime(path, (future, future))
    art = sx.newest_artifact(sx.PREVIEW)
    published = (art or {}).get("line") or ""
    skipped = (art or {}).get("skipped") or []
    source = io.open(os.path.join(REPO, "tools", "status_export_fresh.py"),
                     encoding="utf-8", errors="replace").read()
    repeated = [name for name in er.BOARD_PAGES if '"%s"' % name in source]
    record("AC-SXFB13",
           "face-sweep" not in published and "fixture" in published
           and any("face-sweep" in item for item in skipped) and not repeated,
           "published=%r skipped=%r repeated=%r"
           % (published[:40], len(skipped), repeated or "none"))

    # AC-SXFB14 (AC-SXF14): the milestone row was carried TWICE with different
    # values and neither copy was graded, because the writer only ever wrote the
    # ceo_face copy. Both directions must redden; a strict prefix of the
    # derivation must be named a FRAGMENT rather than merely stale, because that
    # is the same complaint the CEO made about the headline at R2823; and one
    # --apply must make the two copies equal again.
    healthy = json.loads(io.open(export, encoding="utf-8").read())
    derived_ms = sx.next_milestone(sx.BACKLOG)["text"]
    older = "R2821 ENGINEERING: a milestone sentence left behind by an earlier round"
    inner_stale = json.loads(json.dumps(healthy))
    inner_stale["ceo_face"]["next_milestone"] = older
    write_json(export, inner_stale)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc_inner = sx.check(export, sx.STATE)
    said_inner = buffer.getvalue()
    top_stale = json.loads(json.dumps(healthy))
    top_stale["next_milestone"] = older
    write_json(export, top_stale)
    rc_top = sx.check(export, sx.STATE)
    cut = json.loads(json.dumps(healthy))
    cut["next_milestone"] = derived_ms[:40]
    write_json(export, cut)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc_cut = sx.check(export, sx.STATE)
    said_cut = buffer.getvalue()
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_ms_fixed = sx.check(export, sx.STATE)
    landed = json.loads(io.open(export, encoding="utf-8").read())
    record("AC-SXFB14",
           rc_inner == 2 and "E_SXF_MILESTONE_STALE" in said_inner
           and rc_top == 2 and rc_cut == 2
           and "E_SXF_MILESTONE_FRAGMENT" in said_cut
           and rc_ms_fixed == 0
           and landed.get("next_milestone") == landed["ceo_face"].get("next_milestone")
           == derived_ms,
           "inner=%d top=%d cut=%d fixed=%d fragment_named=%s"
           % (rc_inner, rc_top, rc_cut, rc_ms_fixed,
              "E_SXF_MILESTONE_FRAGMENT" in said_cut))

    # AC-SXFB15 (AC-SXF15): the same disease on the artifact row - and here the
    # measured shape was real: the top-level copy still named a qa log while the
    # ceo_face copy already named the membership page.
    healthy = json.loads(io.open(export, encoding="utf-8").read())
    derived_art = sx.newest_artifact(sx.PREVIEW)["line"]
    stale_art = "qa/ugc-gate-suite-R2814.log (835B, sha256 676bd87df8c9250c)"
    art_top = json.loads(json.dumps(healthy))
    art_top["latest_artifact"] = stale_art
    write_json(export, art_top)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc_art_top = sx.check(export, sx.STATE)
    said_art = buffer.getvalue()
    art_inner = json.loads(json.dumps(healthy))
    art_inner["ceo_face"]["latest_artifact"] = stale_art
    write_json(export, art_inner)
    rc_art_inner = sx.check(export, sx.STATE)
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_art_fixed = sx.check(export, sx.STATE)
    landed = json.loads(io.open(export, encoding="utf-8").read())
    record("AC-SXFB15",
           rc_art_top == 2 and "E_SXF_ARTIFACT_STALE" in said_art
           and rc_art_inner == 2 and rc_art_fixed == 0
           and landed.get("latest_artifact") == landed["ceo_face"].get("latest_artifact")
           == derived_art,
           "top=%d inner=%d fixed=%d" % (rc_art_top, rc_art_inner, rc_art_fixed))

    # AC-SXF21 (R3107): the due row was answered TWICE and the two answers were
    # 12.7 hours apart on a tree every gate called healthy (measured on the live
    # document: export_ts=23:24:44 -> ceo_face due +48.0h, top-level due
    # +35.34h). Both directions must redden, AND two copies carrying the SAME
    # wrong hour must still redden, because equality alone would let two
    # agreeing falsehoods read green. One --apply must land export_ts + the
    # row's own hour claim on both copies.
    export, doc = build_world(root)
    healthy = json.loads(io.open(export, encoding="utf-8").read())
    hours = sx.next_milestone(sx.BACKLOG)["hours"]
    stamp = dt.datetime.fromisoformat(healthy["export_ts"])
    wrong = sx.iso(stamp + dt.timedelta(hours=hours + 35))
    top_old = json.loads(json.dumps(healthy))
    top_old["next_milestone_due"] = "2026-11-16T00:00:00+08:00"
    write_json(export, top_old)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc_due_top = sx.check(export, sx.STATE)
    said_due_top = buffer.getvalue()
    inner_old = json.loads(json.dumps(healthy))
    inner_old["ceo_face"]["next_milestone_due"] = "2026-11-16T00:00:00+08:00"
    write_json(export, inner_old)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc_due_inner = sx.check(export, sx.STATE)
    said_due_inner = buffer.getvalue()
    both_wrong = json.loads(json.dumps(healthy))
    both_wrong["next_milestone_due"] = wrong
    both_wrong["ceo_face"]["next_milestone_due"] = wrong
    write_json(export, both_wrong)
    rc_due_agree = sx.check(export, sx.STATE)
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_due_fixed = sx.check(export, sx.STATE)
    landed_due = json.loads(io.open(export, encoding="utf-8").read())
    derived_due = sx.iso(dt.datetime.fromisoformat(landed_due["export_ts"])
                         + dt.timedelta(hours=hours))
    record("AC-SXF21",
           rc_due_top == 2 and "E_SXF_DUE_STALE" in said_due_top
           and rc_due_inner == 2 and "E_SXF_DUE_STALE" in said_due_inner
           and rc_due_agree == 2 and rc_due_fixed == 0
           and landed_due.get("next_milestone_due")
           == landed_due["ceo_face"].get("next_milestone_due") == derived_due,
           "top=%d inner=%d same_wrong=%d fixed=%d derived=%s"
           % (rc_due_top, rc_due_inner, rc_due_agree, rc_due_fixed, derived_due))

    # AC-SXFB16 (AC-SXF16): the milestone used to be cut at 400 chars mid-word, so
    # the CEO read half a sentence. A short row must land WHOLE (no marker), a long
    # row must be cut at a clause boundary with an explicit marker, and the writer
    # and the grader must be the SAME function - proved by publishing a long row
    # through apply() and requiring --check to stay green on the result, which it
    # cannot if either side invents its own truncation.
    short_row = "- [ ] [R2821] next window (<=12h): a short row that fits whole"
    long_row = ("- [ ] [R2821] next window (<=12h): "
                + "; ".join("clause %02d carries one fact" % i for i in range(200)))
    short_text = sx.milestone_text(short_row)
    with io.open(sx.BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(long_row + "\n")
    # The reader hands milestone_text() the row WITHOUT its "- [ ] " marker, so the
    # expectation is derived through the same two functions the writer uses rather
    # than from the raw line (that difference is a defect in this criterion's
    # first draft, found by running it, not a reason to loosen the assertion).
    read_row = sx.next_milestone(sx.BACKLOG)["row"]
    long_text = sx.milestone_text(read_row)
    body = long_text[:-len(sx.MILESTONE_MARK)] if long_text.endswith(sx.MILESTONE_MARK) else long_text
    clause_cut = (read_row.startswith(body) and read_row[len(body):].startswith("; ")
                  and len(long_text) <= sx.MILESTONE_MAX + len(sx.MILESTONE_MARK))
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_long = sx.check(export, sx.STATE)
    published = json.loads(io.open(export, encoding="utf-8").read())
    same_definition = (published.get("next_milestone") == long_text
                       and published.get("next_milestone") == published["ceo_face"]["next_milestone"])
    with io.open(sx.BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(short_row + "\n")
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_restored = sx.check(export, sx.STATE)
    record("AC-SXFB16",
           short_text == short_row and clause_cut and rc_long == 0
           and same_definition and rc_restored == 0,
           "short_whole=%s clause_cut=%s long_rc=%d shared_def=%s restored=%d"
           % (short_text == short_row, clause_cut, rc_long, same_definition, rc_restored))

    # AC-SXF17 (R2835): the expected round is the round the newest HEADLINE
    # labels, never the largest number a sentence happens to contain. Measured
    # on the real tree: a round narrative that named a private-world fixture
    # round (R9101) rewrote the expected round for every copy of the face, so a
    # healthy closeout read E_SXF_STALE three times over. The criterion carries
    # weight because the OLD rule reddens this world: it would pick 9101, find no
    # headline for it, fall back to the mentioning line, and compare the CEO's
    # `do` against a sub-line instead of the headline.
    # A pristine world for this criterion: earlier records tamper with the same
    # export on purpose, and a criterion must be judged on its own tamper only.
    export, doc = build_world(root)
    original_state = json.loads(io.open(sx.STATE, encoding="utf-8").read())
    noisy = json.loads(json.dumps(original_state))
    noisy["log"] = list(noisy["log"]) + [
        "R2821 landed: the same round also names R9101 inside a sentence"]
    write_json(sx.STATE, noisy)
    # A tampered fixture must stay a HEALTHY document apart from the one thing
    # under test, so the graded size follows the state this criterion wrote.
    noisy_doc = json.loads(json.dumps(doc))
    noisy_doc["state_bytes"] = os.path.getsize(sx.STATE)
    write_json(export, noisy_doc)
    rc_noisy = sx.check(export, sx.STATE)
    derived_round, derived_line = sx.newest_round(noisy)
    write_json(sx.STATE, original_state)
    write_json(export, doc)
    record("AC-SXF17", rc_noisy == 0 and derived_round == 2821
           and derived_line == NARRATIVE,
           "rc=%d round=%r headline=%s" % (rc_noisy, derived_round,
                                           derived_line == NARRATIVE))

    # AC-SXF18 (R2835): the mention fallback is preserved for a window that
    # wrote no headline at all - the fix narrows WHICH lines may name the
    # window, it does not delete the only anchor such a window has.
    fallback_round, fallback_line = sx.newest_round(
        {"log": ["a note that mentions R2814 in passing",
                 "another note that mentions R2812 in passing"]})
    record("AC-SXF18", fallback_round == 2814
           and "R2814" in str(fallback_line or ""),
           "round=%r line=%r" % (fallback_round, str(fallback_line or "")[:40]))

    # AC-SXF19 (R2969): a line that merely MENTIONS the newest round is not its
    # narrative. Measured on the real tree before this fix: a R2968 closeout row
    # ended with "the new R2969 board row", round_of() read 2969 for it, and the
    # old rule returned that earlier line - so --apply published the previous
    # round's sentence and --check then called the same file stale. The world
    # below is the same shape in miniature: the first row is a headline of 2901
    # that mentions 2902, the second row IS the 2902 headline.
    earlier = ("2026-11-19 R2901 CLOSEOUT: the next_milestone came from the "
               "new R2902 board row")
    newer = "2026-11-19 R2902 PRODUCT: the row that actually belongs to 2902"
    picked_round, picked_line = sx.newest_round({"log": [earlier, newer]})
    record("AC-SXF19",
           picked_round == 2902 and picked_line == newer,
           "round=%r picked_newer=%s" % (picked_round, picked_line == newer))

    # AC-SXF20 (R2969): the live document obeys the same invariant - when the
    # published sentence IS a headline, its own label is the round it is
    # published for. A fallback row (no headline at all) is exempt by design.
    live_round, live_line = sx.newest_round(
        json.loads(io.open(sx.STATE, encoding="utf-8").read()))
    live_match = sx.HEADLINE_RE.match(live_line or "")
    live_ok = (live_round is not None and
               (live_match is None or int(live_match.group(1)) == live_round))
    record("AC-SXF20", live_ok,
           "round=%r label=%r" % (live_round,
                                  live_match.group(1) if live_match else None))

    # AC-SXFB10 (AC-SXF10): the registry row exists AND declares this many
    # criteria, so adding a criterion without moving the count is red instead of
    # silently uncounted.
    registry = io.open(os.path.join(REPO, "src", "sandbox", "reconcile_all.py"),
                       encoding="utf-8", errors="replace").read()
    found = re.search(r'test_status_export_fresh\.py"\)\s*,\s*(\d+)', registry)
    declared = int(found.group(1)) if found else -1
    row = None
    if os.path.isfile(MATRIX):
        text = io.open(MATRIX, encoding="utf-8", errors="replace").read()
        for line in text.splitlines():
            if "test_status_export_fresh.py" in line:
                row = line
                break
    record("AC-SXFB10", row is not None and declared == 21,
           "matrix_row=%s declared=%d" % (bool(row), declared))


def main():
    real_before = (snapshot(REAL_EXPORT), snapshot(REAL_STATE))
    root = tempfile.mkdtemp(prefix="sxf-R2821-")
    saved = rebind(root)
    try:
        run(root)
    finally:
        restore(saved)
        shutil.rmtree(root, ignore_errors=True)
    real_after = (snapshot(REAL_EXPORT), snapshot(REAL_STATE))
    record("ISOLATION", real_before == real_after, "real export+state untouched")
    bad = [name for name, ok, _ in results if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not bad else "FAIL",
                              len(results) - len(bad), len(results)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
