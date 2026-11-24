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
import claim_census as CC  # noqa: E402
import closeout_gate as CG  # noqa: E402

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


def claims_reading(block):
    """The census reading a block carries, without its own age stamp.

    AC-SXF33 (R3231): the age cannot be re-derived at check time (it is a
    clock), so it is graded separately against export_ts; every reading
    comparison goes through this slicing so no arm accidentally compares a
    dict that carries the stamp.
    """
    return {key: value for key, value in (block or {}).items()
            if key != sx.CLAIMS_TS_KEY}


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
        # AC-SXFB17/18: the chain block is a DERIVED row, so the healthy fixture
        # is built from the same derivation the grader asks rather than typed.
        "chain": sx.chain_face(root),
        # AC-SXFB20 (R3228): same law for the census reading. Built from the
        # derivation, so every hand-copied fixture below inherits a correct block
        # instead of each arm having to remember to type one.
        # AC-SXF33 (R3231): the block now states its own age, and the healthy
        # fixture's age IS the apply moment it claims - the same string it
        # publishes as export_ts.
        "claims": dict(sx.claims_face(root), census_ts="2026-11-16T00:00:00+08:00"),
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

    # AC-SXF23 (R3310): a meta headline is the round's own observation scan, so
    # the expected line is the first NON-meta headline of the newest round (the
    # same line src/os/export_round.py publishes, from one shared pattern). A
    # round carrying only the scan still publishes it - the preference is not a
    # ban - and the pattern is not retyped here.
    scan = ("2026-11-23 R9101 GROUP SCAN (content-addressed, read before any "
            "work): the ledger carried 0 rows")
    prod = "2026-11-23 R9101 PRODUCT+ENGINEERING: the round shipped one thing"
    meta_round, meta_line = sx.newest_round({"log": [scan, prod]})
    only_round, only_line = sx.newest_round({"log": [scan]})
    shared = (sx.META_RE.pattern
              == sx._ledger_lines_module().ROUND_META_RE.pattern)
    record("AC-SXF23",
           meta_round == 9101 and meta_line == prod
           and only_round == 9101 and only_line == scan and shared,
           "round=%r line=%r only=%r shared=%r"
           % (meta_round, meta_line, only_line, shared))

    # AC-SXF24 (R3311): the meta set covers waiting and bookkeeping steps too.
    # The two readers must agree on the same waiting-state world, and the product
    # label must never be classified as meta - otherwise a widened name would
    # hide the artifact this face exists to publish.
    wait = ("2026-11-14 R9102 MONITORED-WAIT window: the leg is STILL LIVE at "
            "closeout")
    wprod = "2026-11-14 R9102 PRODUCT+ENGINEERING: the round shipped one thing"
    w_round, w_line = sx.newest_round({"log": [wait, wprod]})
    w_only_round, w_only_line = sx.newest_round({"log": [wait]})
    not_meta = sx.META_RE.match(wprod) is None
    record("AC-SXF24",
           w_round == 9102 and w_line == wprod
           and w_only_round == 9102 and w_only_line == wait and not_meta,
           "round=%r line=%r only=%r not_meta=%r"
           % (w_round, w_line, w_only_line, not_meta))

    # AC-SXF22 (R3118): "refused" and "did not land" must be the same fact. R3117
    # proved AFTER the bytes were already under the live name (measured on a
    # private world: rc=8 and the live name grew 1173->1149 bytes carrying a
    # naive export_ts), and archive_legacy rewrote the same face by hand with no
    # judgement at all while no production vehicle called it.
    import export_round

    def stage_residue():
        return sorted(name for name in os.listdir(os.path.dirname(export))
                      if name.endswith(sx.STAGE_SUFFIX))

    real_clock = sx.now_local
    try:
        # Arm a: a naive clock must refuse BEFORE anything lands.
        before_bytes = io.open(export, "rb").read()
        sx.now_local = lambda: dt.datetime(2026, 11, 21, 12, 0, 0)
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            rc_naive = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        text_naive = said.getvalue()
        after_bytes = io.open(export, "rb").read()
        arm_a = (rc_naive == 8 and after_bytes == before_bytes
                 and "face=STAGED" in text_naive and not stage_residue())

        # Arm b: a judgeable face lands, and a second run is byte-identical.
        sx.now_local = lambda: dt.datetime(2026, 11, 21, 12, 0, 0,
                                           tzinfo=dt.timezone(dt.timedelta(hours=8)))
        with contextlib.redirect_stdout(io.StringIO()):
            rc_first = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        first_bytes = io.open(export, "rb").read()
        with contextlib.redirect_stdout(io.StringIO()):
            rc_second = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        second_bytes = io.open(export, "rb").read()
        code_landed, _ = export_round.face_judgeable(export)
        arm_b = (rc_first == 0 and rc_second == 0
                 and first_bytes == second_bytes
                 and code_landed is None and not stage_residue())

        # Arm c: the archive rewrite is judged too - a naive face leaves the
        # export byte-identical AND creates no archive file.
        naive_doc = json.loads(io.open(export, encoding="utf-8").read())
        naive_doc["export_ts"] = "2026-11-21T12:00:00"
        naive_doc["results"] = LEGACY
        naive_doc.pop("results_archive", None)
        write_json(export, naive_doc)
        before_c = io.open(export, "rb").read()
        logs = os.path.join(root, "logs")
        logs_before = sorted(os.listdir(logs)) if os.path.isdir(logs) else []
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            rc_arch_naive = sx.archive_legacy(export, confirm=True)
        logs_after = sorted(os.listdir(logs)) if os.path.isdir(logs) else []
        arm_c = (rc_arch_naive == 8
                 and io.open(export, "rb").read() == before_c
                 and logs_after == logs_before
                 and "face=STAGED" in said.getvalue())

        # Arm d: on a healthy face the same path still archives losslessly.
        healthy_doc = json.loads(io.open(export, encoding="utf-8").read())
        healthy_doc["export_ts"] = "2026-11-21T00:00:00+08:00"
        write_json(export, healthy_doc)
        with contextlib.redirect_stdout(io.StringIO()):
            rc_arch_ok = sx.archive_legacy(export, confirm=True)
        live_doc = json.loads(io.open(export, encoding="utf-8").read())
        pointer = live_doc.get("results_archive") or {}
        pointer_abs = os.path.join(root, str(pointer.get("path") or "").replace("/", os.sep))
        archived_doc = (json.loads(io.open(pointer_abs, encoding="utf-8").read())
                        if os.path.isfile(pointer_abs) else {})
        code_after_archive, _ = export_round.face_judgeable(export)
        arm_d = (rc_arch_ok == 0
                 and archived_doc.get("results") == LEGACY
                 and pointer.get("count") == len(LEGACY)
                 and pointer.get("sha256") == hashlib.sha256(
                     io.open(pointer_abs, "rb").read()).hexdigest()
                 and "results" not in live_doc
                 and code_after_archive is None and not stage_residue())

        # Arm e: the zero-caller fact is asserted, so re-wiring a vehicle to this
        # path without judging it is red instead of silent.
        callers = []
        for sub in ("src", "tools"):
            for dirpath, _dirnames, filenames in os.walk(os.path.join(REPO, sub)):
                for filename in filenames:
                    if not filename.endswith(".py") or filename.startswith("test_"):
                        continue
                    if filename == "status_export_fresh.py":
                        continue
                    body = io.open(os.path.join(dirpath, filename), encoding="utf-8",
                                   errors="replace").read()
                    if "archive_legacy" in body or "--archive-legacy" in body:
                        callers.append(filename)
        arm_e = callers == []

        record("AC-SXF22", arm_a and arm_b and arm_c and arm_d and arm_e,
               "a=%s b=%s c=%s d=%s e=%s rc=%d/%d/%d/%d"
               % (arm_a, arm_b, arm_c, arm_d, arm_e,
                  rc_naive, rc_first, rc_arch_naive, rc_arch_ok))
    finally:
        sx.now_local = real_clock

    # AC-SXFB17/18/19 (AC-SXF23..25): the ledger counts finally have the consumer
    # the R3221 row demanded. Driven with a REAL broken chain, so a hardcoded zero
    # cannot pass.
    write_json(sx.STATE, {"tick": 9, "log": [NARRATIVE]})
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    healthy = json.loads(io.open(export, encoding="utf-8").read())
    chain_ok = healthy.get("chain")
    rc_chain_ok = sx.check(export, sx.STATE)
    tampered = json.loads(json.dumps(healthy))
    tampered["chain"]["broken"] = int(tampered["chain"]["broken"]) + 1
    write_json(export, tampered)
    rc_chain_bad = sx.check(export, sx.STATE)
    absent = json.loads(json.dumps(healthy))
    absent.pop("chain")
    write_json(export, absent)
    rc_chain_absent = sx.check(export, sx.STATE)
    write_json(export, healthy)
    record("AC-SXFB17", rc_chain_ok == 0 and rc_chain_bad == 2 and rc_chain_absent == 2
           and isinstance(chain_ok, dict) and chain_ok.get("rows") == 0
           and chain_ok.get("broken") == 0,
           "ok=%d tampered=%d absent=%d chain=%s"
           % (rc_chain_ok, rc_chain_bad, rc_chain_absent,
              json.dumps(chain_ok, sort_keys=True)))

    # AC-SXFB18 (AC-SXF24): a world whose adjacent ledger rows do not link lands
    # broken=1 in the export - derived at write time, not carried forward.
    qa_dir = os.path.join(root, "qa")
    os.makedirs(qa_dir, exist_ok=True)
    evidence = os.path.join(qa_dir, "fixture.log")
    with io.open(evidence, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("fixture evidence\n")
    good = hashlib.sha256(io.open(evidence, "rb").read()).hexdigest()[:16]
    first = {"ts": "2026-11-16T00:00:00Z", "event": "REPLACED",
             "name": "fixture.log", "old_bytes": 1, "old_sha16": "0" * 16,
             "new_bytes": 17, "new_sha16": "a" * 16}
    second = dict(first, old_sha16="b" * 16, new_sha16=good)
    ledger = os.path.join(root, "state", "qa_replacements.jsonl")
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with io.open(ledger, "w", encoding="utf-8", newline="\n") as handle:
        for row in (first, second):
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    broken_doc = json.loads(io.open(export, encoding="utf-8").read())
    rc_broken = sx.check(export, sx.STATE)
    record("AC-SXFB18", broken_doc["chain"]["rows"] == 2
           and broken_doc["chain"]["broken"] == 1 and rc_broken == 0,
           "chain=%s rc=%d" % (json.dumps(broken_doc["chain"], sort_keys=True), rc_broken))

    # AC-SXFB19 (AC-SXF24/25): a second --apply is byte-identical on a pinned
    # clock, and a broken chain still reads PASS - published, never gated.
    real_clock = sx.now_local
    pinned = dt.datetime(2026, 11, 22, 4, 0, 0,
                         tzinfo=dt.timezone(dt.timedelta(hours=8)))
    try:
        sx.now_local = lambda: pinned
        rc_first = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        once = io.open(export, "rb").read()
        rc_second = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        twice = io.open(export, "rb").read()
        rc_gate = sx.check(export, sx.STATE)
    finally:
        sx.now_local = real_clock
    record("AC-SXFB19", rc_first == 0 and rc_second == 0 and once == twice
           and rc_gate == 0
           and json.loads(twice.decode("utf-8"))["chain"]["broken"] == 1,
           "apply=%d/%d identical=%s check=%d"
           % (rc_first, rc_second, once == twice, rc_gate))

    # AC-SXF26 (R3224): "no ledger" and "empty ledger" published the identical
    # block. Measured before the change (qa/probe-R3224.log): the report, the
    # LEDGER row and chain_face were byte-identical for the two worlds, so the
    # face said rows=0 for something it never measured. The reading now carries
    # `present`; the row text is deliberately unchanged (an absent ledger is
    # still OK rows=0), so this arm also proves the two did NOT get conflated
    # in the other direction.
    import closeout_gate as CG
    present_world = os.path.join(root, "present-world")
    os.makedirs(os.path.join(present_world, "state"))
    os.makedirs(os.path.join(present_world, "qa"))
    p_ledger = os.path.join(present_world, "state", "qa_replacements.jsonl")
    face_absent = sx.chain_face(present_world)
    read_absent = {}
    CG.check_ledger(present_world, read_absent)
    row_absent = CG.check_ledger(present_world)[1][0]
    with io.open(p_ledger, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("")
    face_empty = sx.chain_face(present_world)
    read_empty = {}
    CG.check_ledger(present_world, read_empty)
    row_empty = CG.check_ledger(present_world)[1][0]
    with io.open(p_ledger, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(first, sort_keys=True) + "\n")
    face_rows = sx.chain_face(present_world)
    arm_p = (face_absent.get("present") is False
             and face_empty.get("present") is True
             and face_rows.get("present") is True
             and face_absent.get("rows") == face_empty.get("rows") == 0
             and face_rows.get("rows") == 1)
    arm_q = (read_absent.get("present") is False
             and read_empty.get("present") is True
             and row_absent == row_empty)
    arm_r = sorted(face_rows) == ["broken", "path", "present", "rows"]
    write_json(sx.STATE, {"tick": 9, "log": [NARRATIVE]})
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    live_doc = json.loads(io.open(export, encoding="utf-8").read())
    rc_live = sx.check(export, sx.STATE)
    arm_s = (isinstance(live_doc.get("chain", {}).get("present"), bool)
             and live_doc["chain"]["present"] is True and rc_live == 0)
    record("AC-SXF26", arm_p and arm_q and arm_r and arm_s,
           "p=%s q=%s r=%s s=%s absent=%s empty=%s rows=%s rc=%d"
           % (arm_p, arm_q, arm_r, arm_s,
              json.dumps(face_absent, sort_keys=True),
              json.dumps(face_empty, sort_keys=True),
              json.dumps(face_rows, sort_keys=True), rc_live))

    # AC-SXFB20 (AC-SXF27, R3228): the census reading finally reaches the file the
    # CEO downloads. Probed first (qa/probe-R3228.log): publishing the reading as
    # a JSON block moved no counter, so the block cannot feed itself.
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    claims_doc = json.loads(io.open(export, encoding="utf-8").read())
    arm_a = isinstance(claims_doc.get("claims"), dict)
    arm_b = claims_reading(claims_doc.get("claims")) == sx.claims_face(sx.ROOT)
    rc_claims_ok = sx.check(export, sx.STATE)
    tampered_claims = json.loads(json.dumps(claims_doc))
    tampered_claims["claims"]["contradicted"] = int(
        tampered_claims["claims"]["contradicted"]) + 1
    write_json(export, tampered_claims)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_claims_bad = sx.check(export, sx.STATE)
    code_stale = "E_SXF_CLAIMS_STALE" in buffer.getvalue()
    absent_claims = json.loads(json.dumps(claims_doc))
    absent_claims.pop("claims")
    write_json(export, absent_claims)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_claims_absent = sx.check(export, sx.STATE)
    code_missing = "E_SXF_CLAIMS_MISSING" in buffer.getvalue()
    write_json(export, claims_doc)
    record("AC-SXFB20", arm_a and arm_b and rc_claims_ok == 0
           and rc_claims_bad == 2 and rc_claims_absent == 2
           and code_stale and code_missing,
           "block=%s derived_equal=%s rc=%d/%d/%d codes=%s/%s"
           % (arm_a, arm_b, rc_claims_ok, rc_claims_bad, rc_claims_absent,
              code_stale, code_missing))

    # AC-SXFB21 (AC-SXF28): a world that really contradicts itself lands the real
    # number at write time, and publishing it is idempotent on a pinned clock.
    with io.open(sx.BACKLOG, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("- [R9997] probe row live: the ledger holds rows=0 in "
                     "state/qa_replacements.jsonl\n")
    rc_landed = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    landed_claims = json.loads(io.open(export, encoding="utf-8").read())["claims"]
    derived_claims = sx.claims_face(sx.ROOT)
    real_clock = sx.now_local
    pinned_claims = dt.datetime(2026, 11, 22, 5, 0, 0,
                                tzinfo=dt.timezone(dt.timedelta(hours=8)))
    try:
        sx.now_local = lambda: pinned_claims
        rc_once = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        once_claims = io.open(export, "rb").read()
        rc_twice = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        twice_claims = io.open(export, "rb").read()
    finally:
        sx.now_local = real_clock
    record("AC-SXFB21", rc_landed == 0 and landed_claims["contradicted"] >= 1
           and claims_reading(landed_claims) == derived_claims
           and rc_once == 0 and rc_twice == 0 and once_claims == twice_claims,
           "landed=%s derived=%s idempotent=%s rc=%d/%d/%d"
           % (json.dumps(landed_claims, sort_keys=True),
              json.dumps(derived_claims, sort_keys=True),
              once_claims == twice_claims, rc_landed, rc_once, rc_twice))

    # AC-SXFB22 (AC-SXF29): publishing is not gating, and the SHAPE is the proof
    # - the census counts `rows=<n>` tokens, so the published block must carry
    # none of them (a prose mirror measured claimed 2 -> 3 in the probe).
    rc_gate_red = sx.check(export, sx.STATE)
    export_text = io.open(export, encoding="utf-8").read()
    mirror_lines = [line for line in export_text.split("\n")
                    if line.startswith('  "claims": ')]
    arm_tokens = all("rows=" not in line for line in mirror_lines)
    chain_keys = sorted(json.loads(export_text)["chain"])
    do_text = json.loads(export_text)["do"]
    record("AC-SXFB22", rc_gate_red == 0 and len(mirror_lines) == 1 and arm_tokens
           and chain_keys == ["broken", "path", "present", "rows"]
           and do_text == NARRATIVE,
           "gate=%d lines=%d tokens=%s chain=%s do=%s"
           % (rc_gate_red, len(mirror_lines), arm_tokens,
              ",".join(chain_keys), do_text == NARRATIVE))

    # AC-SXFB23 (AC-SXF30, R3229): the CEO face carries the WHOLE census, not the
    # four keys that fit first. Probed (qa/probe-R3229.log): the same census read
    # 1 captured + 1 uncaptured while the export published neither.
    reading = {}
    CG.check_claims(sx.ROOT, reading)
    derived_seven = sx.claims_face(sx.ROOT)
    arm_keys = sorted(derived_seven) == ["captured", "claimed", "contradicted",
                                         "historic", "present", "rows",
                                         "uncaptured"]
    arm_equal = all(derived_seven[key] == reading[key] for key in derived_seven)
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    landed_seven = json.loads(io.open(export, encoding="utf-8").read())["claims"]
    rc_seven = sx.check(export, sx.STATE)
    tampered_seven = json.loads(io.open(export, encoding="utf-8").read())
    tampered_seven["claims"]["uncaptured"] = int(
        tampered_seven["claims"]["uncaptured"]) + 1
    write_json(export, tampered_seven)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_stale_seven = sx.check(export, sx.STATE)
    stale_named = "E_SXF_CLAIMS_STALE" in buffer.getvalue()
    legacy_seven = json.loads(json.dumps(tampered_seven))
    legacy_seven["claims"] = {key: legacy_seven["claims"][key] for key in
                              ("contradicted", "historic", "rows", "present")}
    write_json(export, legacy_seven)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_legacy_seven = sx.check(export, sx.STATE)
    legacy_named = "E_SXF_CLAIMS_STALE" in buffer.getvalue()
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    record("AC-SXFB23", arm_keys and arm_equal
           and claims_reading(landed_seven) == derived_seven
           and rc_seven == 0 and rc_stale_seven == 2 and stale_named
           and rc_legacy_seven == 2 and legacy_named,
           "keys=%s equal=%s landed=%s rc=%d/%d/%d named=%s/%s"
           % (arm_keys, arm_equal,
              claims_reading(landed_seven) == derived_seven, rc_seven,
              rc_stale_seven, rc_legacy_seven, stale_named, legacy_named))

    # AC-SXFB24 (AC-SXF31): publishing the census must not move the census. Two
    # claims are planted (one prose, one citing a landed file that carries the
    # same token), the counters are taken, then the block lands and the counters
    # must be unchanged and still conserve.
    with io.open(sx.BACKLOG, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("- [R9996] prose arm says rows=41 and names nothing\n")
        handle.write("- [R9996] captured arm says rows=42 in qa/census-arm.log\n")
    if not os.path.isdir(os.path.join(sx.ROOT, "qa")):
        os.makedirs(os.path.join(sx.ROOT, "qa"))
    with io.open(os.path.join(sx.ROOT, "qa", "census-arm.log"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("LEDGER OK rows=42\n")
    before_census = {key: value for key, value in CC.census(sx.ROOT).items()
                     if key != "faces"}
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    after_census = {key: value for key, value in CC.census(sx.ROOT).items()
                    if key != "faces"}
    census_still = all(before_census[key] == after_census[key]
                       for key in ("claimed", "captured", "contradicted",
                                   "uncaptured", "historic", "rows"))
    block_line = [line for line in io.open(export, encoding="utf-8").read().split("\n")
                  if line.startswith('  "claims": ')]
    arm_tokens_seven = len(block_line) == 1 and "rows=" not in block_line[0]
    landed_block = json.loads(io.open(export, encoding="utf-8").read())["claims"]
    conserves = (landed_block["captured"] + landed_block["contradicted"]
                 + landed_block["uncaptured"]) == landed_block["claimed"]
    record("AC-SXFB24", census_still and arm_tokens_seven and conserves
           and landed_block["captured"] >= 1 and landed_block["uncaptured"] >= 1,
           "still=%s blocks=%d tokens=%s conserves=%s claimed/captured/uncaptured=%d/%d/%d"
           % (census_still, len(block_line), arm_tokens_seven, conserves,
              landed_block["claimed"], landed_block["captured"],
              landed_block["uncaptured"]))

    # AC-SXFB25 (AC-SXF32): the seven-key block is ADDITIVE - chain keys, the
    # derived narrative and the 48h milestone due are untouched, and a second
    # apply on a pinned clock is byte-identical with the wider block on disk.
    real_clock_seven = sx.now_local
    pinned_seven = dt.datetime(2026, 11, 22, 6, 0, 0,
                               tzinfo=dt.timezone(dt.timedelta(hours=8)))
    hours_seven = sx.next_milestone(sx.BACKLOG)["hours"]
    try:
        sx.now_local = lambda: pinned_seven
        rc_seven_once = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        seven_once = io.open(export, "rb").read()
        rc_seven_twice = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        seven_twice = io.open(export, "rb").read()
    finally:
        sx.now_local = real_clock_seven
    seven_doc = json.loads(seven_twice.decode("utf-8"))
    expected_due = (pinned_seven + dt.timedelta(hours=hours_seven)).strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    record("AC-SXFB25", rc_seven_once == 0 and rc_seven_twice == 0
           and seven_once == seven_twice
           and sorted(seven_doc["chain"]) == ["broken", "path", "present", "rows"]
           and seven_doc["do"] == NARRATIVE
           and seven_doc["next_milestone_due"] == expected_due
           and len(seven_doc["claims"]) == 8,
           "rc=%d/%d idempotent=%s chain=%s do=%s due=%s keys=%d"
           % (rc_seven_once, rc_seven_twice, seven_once == seven_twice,
              ",".join(sorted(seven_doc["chain"])), seven_doc["do"] == NARRATIVE,
              seven_doc["next_milestone_due"], len(seven_doc["claims"])))

    # AC-SXFB33 (AC-SXF33, R3231): the reading states its OWN age, and that age
    # is pinned to the face's own moment. Probed (qa/probe-R3231.log, ARM-B): the
    # census moved uncaptured 0 -> 1 while the stamp stayed behind and check()
    # still answered rc=0 - every criterion compared the block to the census and
    # none compared it to a moment.
    real_clock_age = sx.now_local
    pinned_age = dt.datetime(2026, 11, 22, 7, 0, 0,
                             tzinfo=dt.timezone(dt.timedelta(hours=8)))
    try:
        sx.now_local = lambda: pinned_age
        rc_age_apply = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    finally:
        sx.now_local = real_clock_age
    age_doc = json.loads(io.open(export, encoding="utf-8").read())
    rc_age_ok = sx.check(export, sx.STATE)
    arm_same = (age_doc["claims"][sx.CLAIMS_TS_KEY] == age_doc["export_ts"]
                == "2026-11-22T07:00:00+08:00")
    no_stamp = json.loads(json.dumps(age_doc))
    no_stamp["claims"].pop(sx.CLAIMS_TS_KEY)
    write_json(export, no_stamp)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_age_missing = sx.check(export, sx.STATE)
    age_missing = "E_SXF_CLAIMS_AGE:" in buffer.getvalue()
    bad_stamp = json.loads(json.dumps(age_doc))
    bad_stamp["claims"][sx.CLAIMS_TS_KEY] = "yesterday"
    write_json(export, bad_stamp)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_age_bad = sx.check(export, sx.STATE)
    age_bad = "E_SXF_CLAIMS_AGE:" in buffer.getvalue()
    split_stamp = json.loads(json.dumps(age_doc))
    split_stamp["claims"][sx.CLAIMS_TS_KEY] = "2026-11-22T08:00:00+08:00"
    write_json(export, split_stamp)
    with contextlib.redirect_stdout(io.StringIO()) as buffer:
        rc_age_split = sx.check(export, sx.STATE)
    age_split = "E_SXF_CLAIMS_AGE_SPLIT:" in buffer.getvalue()
    # A split is NOT reported as missing: the two defects stay separate codes.
    split_only = "E_SXF_CLAIMS_AGE:" not in buffer.getvalue()
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    rc_age_fixed = sx.check(export, sx.STATE)
    record("AC-SXFB33", rc_age_apply == 0 and rc_age_ok == 0 and arm_same
           and rc_age_missing == 2 and age_missing
           and rc_age_bad == 2 and age_bad
           and rc_age_split == 2 and age_split and split_only
           and rc_age_fixed == 0,
           "same=%s rc=%d/%d/%d/%d/%d missing=%s bad=%s split=%s split_only=%s"
           % (arm_same, rc_age_apply, rc_age_ok, rc_age_missing, rc_age_bad,
              rc_age_split, age_missing, age_bad, age_split, split_only))

    # AC-SXFB34 (AC-SXF34, R3231): the age is ADDITIVE - the chain block, the
    # derived narrative and the 48h due stay exactly as they were, a second apply
    # on a pinned clock is byte-identical, and publishing the stamp moves no
    # census counter (a JSON key is not a `rows=<n>` token).
    real_clock_add = sx.now_local
    pinned_add = dt.datetime(2026, 11, 22, 8, 0, 0,
                             tzinfo=dt.timezone(dt.timedelta(hours=8)))
    before_census_add = {key: value for key, value in CC.census(sx.ROOT).items()
                         if key != "faces"}
    hours_add = sx.next_milestone(sx.BACKLOG)["hours"]
    try:
        sx.now_local = lambda: pinned_add
        rc_add_once = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        add_once = io.open(export, "rb").read()
        rc_add_twice = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        add_twice = io.open(export, "rb").read()
    finally:
        sx.now_local = real_clock_add
    after_census_add = {key: value for key, value in CC.census(sx.ROOT).items()
                        if key != "faces"}
    add_doc = json.loads(add_twice.decode("utf-8"))
    expected_due_add = (pinned_add + dt.timedelta(hours=hours_add)).strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")
    counters_still = all(before_census_add[key] == after_census_add[key]
                         for key in ("claimed", "captured", "contradicted",
                                     "uncaptured", "historic", "rows"))
    add_lines = [line for line in add_twice.decode("utf-8").split("\n")
                 if line.startswith('  "claims": ')]
    add_tokens = len(add_lines) == 1 and "rows=" not in add_lines[0]
    record("AC-SXFB34", rc_add_once == 0 and rc_add_twice == 0
           and add_once == add_twice
           and sorted(add_doc["chain"]) == ["broken", "path", "present", "rows"]
           and add_doc["do"] == NARRATIVE
           and add_doc["next_milestone_due"] == expected_due_add
           and len(add_doc["claims"]) == 8
           and counters_still and add_tokens,
           "rc=%d/%d idempotent=%s chain=%s due=%s keys=%d counters=%s tokens=%s"
           % (rc_add_once, rc_add_twice, add_once == add_twice,
              ",".join(sorted(add_doc["chain"])),
              add_doc["next_milestone_due"], len(add_doc["claims"]),
              counters_still, add_tokens))

    # AC-SXFB35 (AC-SXF35, R3236): the six readings are graded against
    # THEMSELVES. Probed (qa/probe-R3236.log, Q2): a landed block that EQUALED a
    # census reading of claimed=100 / captured=1 / contradicted=0 /
    # uncaptured=0 answered rc=0 VERDICT PASS, because every criterion compared
    # the block to the census and none graded the census against itself.
    def patched_face(over):
        base = {"claimed": 10, "captured": 4, "contradicted": 2,
                "uncaptured": 4, "historic": 1, "rows": 3, "present": True}
        base.update(over)
        return lambda root: dict(base)

    def verdict_of():
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = sx.check(export, sx.STATE)
        return rc, buffer.getvalue()

    real_face_arith = sx.claims_face
    arith_arms = []
    for label, over in (
            ("sum", {"claimed": 100, "captured": 1, "contradicted": 0,
                     "uncaptured": 0}),
            ("historic", {"historic": 5}),
            ("negative", {"captured": -1}),
            ("type", {"claimed": "10"})):
        sx.claims_face = patched_face(over)
        try:
            rc_arm, text_arm = verdict_of()
        finally:
            sx.claims_face = real_face_arith
        arith_arms.append((label, rc_arm, "E_SXF_CLAIMS_ARITH" in text_arm))
    record("AC-SXFB35", all(rc_arm == 2 and hit
                            for _label, rc_arm, hit in arith_arms),
           "arms=%s" % ",".join("%s rc=%d hit=%s" % arm for arm in arith_arms))

    # AC-SXFB36 (AC-SXF36, R3236): the arithmetic code is NOT redundant with
    # STALE. The decisive arm makes the landed block EQUAL the non-conserving
    # census, so STALE is clean by construction and only the new code can redden.
    bad_reading = {"claimed": 100, "captured": 1, "contradicted": 0,
                   "uncaptured": 0, "historic": 0, "rows": 3, "present": True}
    sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
    landed_mut = json.loads(io.open(export, encoding="utf-8").read())
    landed_mut["claims"].update(bad_reading)
    write_json(export, landed_mut)
    sx.claims_face = lambda root: dict(bad_reading)
    try:
        rc_indep, text_indep = verdict_of()
    finally:
        sx.claims_face = real_face_arith
    indep = (rc_indep == 2 and "E_SXF_CLAIMS_ARITH" in text_indep
             and "E_SXF_CLAIMS_STALE" not in text_indep)
    record("AC-SXFB36", indep,
           "rc=%d arith=%s stale=%s" % (rc_indep,
                                        "E_SXF_CLAIMS_ARITH" in text_indep,
                                        "E_SXF_CLAIMS_STALE" in text_indep))

    # AC-SXFB37 (AC-SXF37, R3236): PURE ADDITION - the block keeps its eight
    # keys, a second apply on a pinned clock is byte-identical, and the real
    # world's own reading conserves, so the new code manufactures no false red.
    real_clock_arith = sx.now_local
    pinned_arith = dt.datetime(2026, 11, 22, 9, 0, 0,
                               tzinfo=dt.timezone(dt.timedelta(hours=8)))
    try:
        sx.now_local = lambda: pinned_arith
        rc_arith_once = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        arith_once = io.open(export, "rb").read()
        rc_arith_twice = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        arith_twice = io.open(export, "rb").read()
    finally:
        sx.now_local = real_clock_arith
    rc_arith_after = sx.check(export, sx.STATE)
    live_clean = sx.claims_arith(sx.claims_face(REPO)) == []
    arith_doc = json.loads(arith_twice.decode("utf-8"))
    record("AC-SXFB37", rc_arith_once == 0 and rc_arith_twice == 0
           and arith_once == arith_twice and rc_arith_after == 0
           and len(arith_doc["claims"]) == 8 and live_clean,
           "rc=%d/%d/%d idempotent=%s keys=%d live_clean=%s"
           % (rc_arith_once, rc_arith_twice, rc_arith_after,
              arith_once == arith_twice, len(arith_doc["claims"]), live_clean))

    # AC-SXFB10 (AC-SXF10): the registry row exists AND declares this many
    # criteria, so adding a criterion without moving the count is red instead of
    # silently uncounted.
    # AC-SXFB10 (AC-SXF10/R3311): the registry row exists AND declares the same
    # count the matrix carries, so adding a criterion without moving the count is
    # red instead of silently uncounted. The count is READ OUT OF the matrix row
    # rather than pinned as a literal (measured R3311: the old arm compared
    # declared == 37, so a new criterion needed TWO hand edits - the registry and
    # this literal - which is the drift this arm exists to catch).
    registry = io.open(os.path.join(REPO, "src", "sandbox", "reconcile_all.py"),
                       encoding="utf-8", errors="replace").read()
    found = re.search(r'test_status_export_fresh\.py"\)\s*,\s*(\d+)', registry)
    declared = int(found.group(1)) if found else -1
    row = None
    matrix_declared = -1
    if os.path.isfile(MATRIX):
        text = io.open(MATRIX, encoding="utf-8", errors="replace").read()
        for line in text.splitlines():
            if "test_status_export_fresh.py" in line:
                row = line
                cells = line.split("|")
                if len(cells) >= 5:
                    try:
                        matrix_declared = int(cells[4].strip())
                    except ValueError:
                        matrix_declared = -1
                break
    record("AC-SXFB10",
           row is not None and declared > 0 and declared == matrix_declared,
           "matrix_row=%s declared=%d matrix=%d"
           % (bool(row), declared, matrix_declared))


def wire_arms():
    """AC-SXFB38 (AC-SXF36, R3360): the three rows this face could not see.

    Driven with the module globals back on the REAL tree, because the comparison
    keys on the state path (the shipped writer's own boundary): a private world
    must announce itself, the live pair must read green, and the same pair with
    one count moved by one must name the field. The real face is cloned to a temp
    path for the tamper arm and read back afterwards, so nothing lands on it.
    """
    derived = {"log_lines_in_window": 12,
               "substantive_non_idle_mention_lines": 3}
    label = sx._cec_module()._load_patterns()["tick_row_label"]
    tick_rows = [["7", label, "fixture"]]

    def codes(said):
        return [code for code, _ in said]

    arm_base = sx.self_drive_problems(dict(derived), derived, 7, tick_rows, label) == []
    arm_win = codes(sx.self_drive_problems(
        dict(derived, log_lines_in_window=11), derived, 7, tick_rows, label))
    arm_sub = codes(sx.self_drive_problems(
        dict(derived, substantive_non_idle_mention_lines=2), derived, 7,
        tick_rows, label))
    arm_gone = codes(sx.self_drive_problems(
        {"log_lines_in_window": 12}, derived, 7, tick_rows, label))
    arm_none = codes(sx.self_drive_problems(None, derived, 7, tick_rows, label))
    arm_zero = codes(sx.self_drive_problems(
        dict(derived), derived, 7, [], label))
    arm_two = codes(sx.self_drive_problems(
        dict(derived), derived, 7, tick_rows + [["7", label, "dup"]], label))
    arm_tick = codes(sx.self_drive_problems(
        dict(derived), derived, 8, tick_rows, label))
    pure_ok = (arm_base
               and arm_win == ["E_SXF_SELF_DRIVE_STALE"]
               and arm_sub == ["E_SXF_SELF_DRIVE_STALE"]
               and arm_gone == ["E_SXF_SELF_DRIVE_STALE"]
               and arm_none == ["E_SXF_SELF_DRIVE_MISSING"]
               and arm_zero == ["E_SXF_TICK_ROW_SHAPE"]
               and arm_two == ["E_SXF_TICK_ROW_SHAPE"]
               and arm_tick == ["E_SXF_TICK_ROW_STALE"])

    before = snapshot(REAL_EXPORT)
    world = tempfile.mkdtemp(prefix="sxf-wire-R3360-")
    try:
        live_buffer = io.StringIO()
        with contextlib.redirect_stdout(live_buffer):
            rc_live = sx.check(REAL_EXPORT, REAL_STATE)
        clone = json.loads(sx.read_text(REAL_EXPORT))
        block = clone.get("self_drive") or {}
        block["log_lines_in_window"] = int(block.get("log_lines_in_window") or 0) + 1
        clone["self_drive"] = block
        stamp = os.path.join(world, "status-export.json")
        write_json(stamp, clone)
        wire_buffer = io.StringIO()
        with contextlib.redirect_stdout(wire_buffer):
            rc_wire = sx.check(stamp, REAL_STATE)
        wire_said = wire_buffer.getvalue()
        other_state = os.path.join(world, "state.json")
        shutil.copyfile(REAL_STATE, other_state)
        skip_buffer = io.StringIO()
        with contextlib.redirect_stdout(skip_buffer):
            rc_skip = sx.check(REAL_EXPORT, other_state)
        skip_said = skip_buffer.getvalue()
    finally:
        shutil.rmtree(world, ignore_errors=True)
    after = snapshot(REAL_EXPORT)
    touched = before != after
    named = "E_SXF_SELF_DRIVE_STALE" in wire_said
    skipped = "self_drive graded=0 skipped=private-world" in skip_said
    record("AC-SXFB38",
           pure_ok and rc_live == 0 and rc_wire == 2 and named
           and skipped and rc_skip == 0 and not touched,
           "pure=%s live=%d wire=%d named=%s skip_line=%s skip_rc=%d "
           "real_face_untouched=%s"
           % (pure_ok, rc_live, rc_wire, named, skipped, rc_skip,
              not touched))
    return not touched


def fixed_point_arms():
    """AC-SXFB39..AC-SXFB42 (R3383): the census is taken over the document it lands in.

    R3382 measured the shipped writer landing claimed=40 / uncaptured=33 while
    its own verifier derived 41/34 from the same file (`E_SXF_CLAIMS_STALE` on
    every run): the export face carries `rows=` tokens inside its own prose rows
    (`latest_artifact`, `next_milestone`), so a block derived from the document
    as it stood BEFORE that apply's prose edits is stale the moment it lands.

    This world has the exact shape - a milestone row that carries a `rows=`
    token only once the edit is written - so the old writer is red here and the
    fixed one is green. Every arm is private; the real faces are snapshotted and
    must be untouched.
    """
    real_before = (snapshot(REAL_EXPORT), snapshot(REAL_STATE))
    root = tempfile.mkdtemp(prefix="sxf-fixpoint-R3383-")
    saved = rebind(root)
    try:
        export, _doc = build_world(root)
        # The milestone row lands INSIDE the export face and carries a `rows=`
        # token the pre-edit document does not have. Short enough not to be cut
        # by the derive() width, and naming the ledger so it is a real claim.
        with io.open(os.path.join(root, "src", "os", "backlog.md"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write("- [ ] [R2821] next window: fixture milestone, "
                         "rows=1042 of the ledger\n")
        pre_edit_text = io.open(export, encoding="utf-8").read()
        pre_edit = {key: value for key, value in
                    CC.census(root, export_text=pre_edit_text).items()
                    if key != "faces"}

        # AC-SXFB39: the writer lands the census of the document it wrote.
        rc_apply = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
        landed_doc = json.loads(io.open(export, encoding="utf-8").read())
        landed = claims_reading(landed_doc["claims"])
        live = {key: value for key, value in CC.census(root).items()
                if key != "faces"}
        rc_check = sx.check(export, sx.STATE)
        moved = pre_edit["claimed"] != live["claimed"]
        record("AC-SXFB39", rc_apply == 0 and rc_check == 0 and moved
               and landed == live,
               "apply=%d check=%d moved=%s landed=%s live=%s"
               % (rc_apply, rc_check, moved,
                  json.dumps(landed, sort_keys=True),
                  json.dumps(live, sort_keys=True)))

        # AC-SXFB40: the criterion has weight - the R3382 shape (a block taken
        # from the PRE-edit document) reddens by name, and it is not red for
        # some other reason because the settled document reads green.
        stale_doc = json.loads(json.dumps(landed_doc))
        stale_doc["claims"] = dict(pre_edit, census_ts=landed_doc["claims"][sx.CLAIMS_TS_KEY])
        write_json(export, stale_doc)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc_stale = sx.check(export, sx.STATE)
        said = buffer.getvalue()
        write_json(export, landed_doc)
        rc_restored = sx.check(export, sx.STATE)
        record("AC-SXFB40", rc_stale == 2 and "E_SXF_CLAIMS_STALE" in said
               and rc_restored == 0,
               "stale_rc=%d named=%s restored_rc=%d"
               % (rc_stale, "E_SXF_CLAIMS_STALE" in said, rc_restored))

        # AC-SXFB41: --check is read-only and a second apply on a pinned clock is
        # byte-identical. The state and the board are not this writer's to move.
        watched = (snapshot(sx.STATE),
                   os.path.getsize(sx.BACKLOG), os.path.getmtime(sx.BACKLOG))
        before_check = snapshot(export)
        sx.check(export, sx.STATE)
        after_check = snapshot(export)
        real_clock = sx.now_local
        pinned = dt.datetime(2026, 11, 23, 9, 0, 0,
                             tzinfo=dt.timezone(dt.timedelta(hours=8)))
        try:
            sx.now_local = lambda: pinned
            rc_once = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
            bytes_once = io.open(export, "rb").read()
            rc_twice = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
            bytes_twice = io.open(export, "rb").read()
        finally:
            sx.now_local = real_clock
        same_inputs = (watched[0] == snapshot(sx.STATE)
                       and watched[1] == os.path.getsize(sx.BACKLOG)
                       and watched[2] == os.path.getmtime(sx.BACKLOG))
        record("AC-SXFB41", before_check == after_check and rc_once == 0
               and rc_twice == 0 and bytes_once == bytes_twice and same_inputs,
               "check_writes=%s apply=%d/%d idempotent=%s inputs_untouched=%s"
               % (before_check == after_check, rc_once, rc_twice,
                  bytes_once == bytes_twice, same_inputs))

        # AC-SXFB42: a document that will not settle is refused BY NAME and
        # nothing lands. Honest name: this is writer/verifier agreement on one
        # text (a carrier contract), not a product capability.
        real_face = sx.claims_face
        counter = {"n": 0}

        def moving_face(_root, export_text=None):
            counter["n"] += 1
            return {"claimed": counter["n"], "captured": 0, "contradicted": 0,
                    "uncaptured": counter["n"], "historic": 0, "rows": 0,
                    "present": True}

        sx.claims_face = moving_face
        try:
            before_fail = snapshot(export)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                rc_moving = sx.apply(export, sx.STATE, sx.BACKLOG, sx.PREVIEW)
            fail_said = buffer.getvalue()
        finally:
            sx.claims_face = real_face
        after_fail = snapshot(export)
        record("AC-SXFB42", rc_moving == 9
               and "E_SXF_CLAIMS_FIXPOINT" in fail_said
               and before_fail == after_fail,
               "rc=%d named=%s wrote=%s"
               % (rc_moving, "E_SXF_CLAIMS_FIXPOINT" in fail_said,
                  before_fail != after_fail))
    finally:
        restore(saved)
        shutil.rmtree(root, ignore_errors=True)
    real_after = (snapshot(REAL_EXPORT), snapshot(REAL_STATE))
    record("AC-SXFB39-ISO", real_before == real_after,
           "real export+state untouched by the fixed-point arms")


def main():
    real_before = (snapshot(REAL_EXPORT), snapshot(REAL_STATE))
    root = tempfile.mkdtemp(prefix="sxf-R2821-")
    saved = rebind(root)
    try:
        run(root)
    finally:
        restore(saved)
        shutil.rmtree(root, ignore_errors=True)
    wire_arms()
    fixed_point_arms()
    real_after = (snapshot(REAL_EXPORT), snapshot(REAL_STATE))
    record("ISOLATION", real_before == real_after, "real export+state untouched")
    bad = [name for name, ok, _ in results if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not bad else "FAIL",
                              len(results) - len(bad), len(results)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
