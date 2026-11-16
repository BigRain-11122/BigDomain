"""Battery suite for tools/status_export_fresh.py - criteria AC-SXFB1..AC-SXFB13.

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
    doc = {
        "export_ts": "2026-11-16T00:00:00+08:00",
        "do": NARRATIVE,
        "ceo_face": {
            "current": NARRATIVE,
            "latest_artifact": "preview/fixture.html (1B, x)",
            "last_artifact": "preview/fixture.html (1B, x)",
            "latest_artifact_abs": os.path.join(root, "preview", "fixture.html"),
            "next_milestone": "fixture",
            "next_milestone_due": "2026-11-17T00:00:00+08:00",
            "updated_at": "2026-11-16T00:00:00+08:00",
        },
        "current": NARRATIVE,
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
    record("AC-SXFB10", row is not None and declared == 13,
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
