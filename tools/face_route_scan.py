#!/usr/bin/env python3
"""Site-wide route law: no face is a silent endpoint, and none is unreachable.

Why this exists: R3283 moved the buyer past the page where money appears, and
R3284 found two more faces with out-degree zero - one of them the landing page
of the live-room funnel. Both rounds patched a named face, so the defect was
found by eye each time. R3285 pre-registers the rule instead of the next patch:
EVERY face carrying a control must link to at least one local html file that is
actually on disk. The face list is walked from preview/, never typed, and each
number on the face comes from the same measure_hop definition AC-BT7 grades.

R3287 measured the other direction: the law only covered operable faces, so 32
read-only faces linked nowhere and still read PASS, and a reader who clicked
into one had no onward route. The probe also measured that every non-index face
IS linked from the entry page (unreachable=0), and that injecting a back-hop
into the 32 pages would red 17 owning tools that grade their own page bytes.
So the law grows in the graded direction instead of the byte direction: every
face must be reachable FROM the entry page, and a face with no downstream must
be declared as an endpoint in ONE closure (state/route-termini.json) that names
both the page and the operable page it sends the reader back to.

Criteria AC-FRS1..AC-FRS5 (pinned in src/os/backlog.md, R3285 PIN line, before
this file existed):
  AC-FRS1 the face list is derived from disk (preview/*.html), so a typed list
          cannot hide a face; the printed count equals a fresh walk.
  AC-FRS2 an operable face (controls > 0) with out-degree zero is REFUSED and
          named. This is the law the two dead ends violated.
  AC-FRS3 every printed bytes / controls / out-degree / link counts equals a
          fresh reading of the disk (landed json and page text both graded).
  AC-FRS4 degenerate reading is refused: the tree must hold at least one
          operable face AND at least one read-only face, so an empty or
          control-free world cannot read PASS.
  AC-FRS5 every hop declared in tools/buyer_route.py must exist on disk; a
          stale closure entry is named rather than silently unlinked. The
          closure is graded against the SHIPPED tree even when --preview points
          at a private world, so a fixture does not redden this arm.

Criteria AC-FRS6..AC-FRS9 (pinned in src/os/backlog.md, R3287 PIN line, before
this code):
  AC-FRS6 reachability: every face except index.html must be linked from the
          entry page by a local href whose file is on disk; an unreachable face
          is named. Reachable is measured, not declared.
  AC-FRS7 endpoint declaration: every face with controls==0 and out-degree 0
          must be named in state/route-termini.json with a non-empty title read
          from the page itself, bytes/controls equal to a fresh reading, and a
          `back` href that is on disk and carries at least one control. A silent
          endpoint, an empty title, a drifted measurement or a back hop that
          lands on a read-only page is refused and named.
  AC-FRS8 no stale declaration: a declared endpoint that today links onward, or
          that is no longer on disk, is refused - the table may not keep graves.
  AC-FRS9 one table: the declared endpoint set and count equal the fresh
          derivation, and every declared back hop is itself an operable face, so
          "back to the page you can click" is never an empty promise.

Usage:
    python tools/face_route_scan.py            # render state/face-route-scan.json
                                               #   and state/route-termini.json
    python tools/face_route_scan.py --check     # read-only verdict
    python tools/face_route_scan.py --preview D # private world (tests)
"""
import argparse
import io
import json
import os
import re
import sys

import buyer_route
import buyer_trial

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")
OUT = os.path.join(ROOT, "state", "face-route-scan.json")
TERMINI = os.path.join(ROOT, "state", "route-termini.json")

LINK = re.compile(r'href\s*=\s*["\']([A-Za-z0-9._\-]+\.html)["\']')
TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)

# The page a read-only endpoint sends the reader back to. One constant, not 32
# opinions: buyer-trial is the only face where a buyer can actually click the
# funnel. AC-FRS9 grades that this target is still operable, so the constant
# cannot quietly become a read-only page.
BACK = "buyer-trial.html"
ENTRY = "index.html"


def measure(path):
    size, controls = buyer_trial.measure_hop(path)
    text = io.open(path, encoding="utf-8").read()
    m = TITLE.search(text)
    title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    links = sorted(set(l for l in LINK.findall(text) if os.path.exists(os.path.join(os.path.dirname(path), l))))
    return {
        "bytes": size,
        "controls": controls,
        "title": title,
        "out": len(links),
        "links": links,
    }


def walk(preview=None, hops_base=None):
    base = preview or PREVIEW
    hops_root = hops_base or PREVIEW
    names = sorted(fn for fn in os.listdir(base) if fn.endswith(".html"))
    faces = []
    for fn in names:
        row = measure(os.path.join(base, fn))
        row["face"] = fn
        faces.append(row)
    actionable = [f for f in faces if f["controls"] > 0]
    readonly = [f for f in faces if f["controls"] == 0]
    dead = [f["face"] for f in actionable if f["out"] == 0]

    by_name = {f["face"]: f for f in faces}
    entry = by_name.get(ENTRY) or {"links": []}
    entry_links = set(entry["links"])
    unreachable = [f["face"] for f in faces if f["face"] != ENTRY and f["face"] not in entry_links]

    back_path = os.path.join(base, BACK)
    back_ok = os.path.exists(back_path) and measure(back_path)["controls"] > 0
    termini = []
    for f in faces:
        if f["controls"] == 0 and f["out"] == 0:
            termini.append(
                {
                    "face": f["face"],
                    "title": f["title"],
                    "bytes": f["bytes"],
                    "controls": f["controls"],
                    "back": BACK,
                    "back_controls": measure(back_path)["controls"] if os.path.exists(back_path) else 0,
                }
            )

    hops = sorted({h for group in buyer_route.ROUTES.values() for h in group})
    missing_hops = [h for h in hops if not os.path.exists(os.path.join(hops_root, h))]
    return {
        "faces": faces,
        "face_count": len(faces),
        "actionable_count": len(actionable),
        "readonly_count": len(readonly),
        "dead_ends": dead,
        "declared_hops": hops,
        "missing_hops": missing_hops,
        "entry": ENTRY,
        "entry_out": len(entry_links),
        "unreachable": unreachable,
        "back_default": BACK,
        "back_operable": back_ok,
        "termini": termini,
        "terminus_count": len(termini),
        "law": (
            "an operable face must link to at least one local html file on disk; "
            "every face must be reachable from the entry page; a face with no "
            "downstream must be declared as an endpoint with an operable back hop"
        ),
    }


def write(preview=None, out=None, hops_base=None):
    doc = walk(preview, hops_base)
    path = out or OUT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    tpath = TERMINI
    if out:
        tpath = os.path.join(os.path.dirname(path), "route-termini.json")
    os.makedirs(os.path.dirname(tpath), exist_ok=True)
    table = {
        "law": "a read-only face with no downstream is an endpoint and must name the operable page it sends the reader back to",
        "back_default": doc["back_default"],
        "back_operable": doc["back_operable"],
        "terminus_count": doc["terminus_count"],
        "termini": doc["termini"],
    }
    with io.open(tpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(table, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(
        "FACE-ROUTE SCAN WROTE faces=%d actionable=%d readonly=%d dead_end=%d hops=%d termini=%d unreachable=%d json=%dB table=%dB"
        % (
            doc["face_count"],
            doc["actionable_count"],
            doc["readonly_count"],
            len(doc["dead_ends"]),
            len(doc["declared_hops"]),
            doc["terminus_count"],
            len(doc["unreachable"]),
            os.path.getsize(path),
            os.path.getsize(tpath),
        )
    )
    return 0


def check(preview=None, out=None, hops_base=None):
    fresh = walk(preview, hops_base)
    path = out or OUT
    fails = []
    if not os.path.exists(path):
        print("FACE-ROUTE SCAN CHECK-MISSING artifact not on disk")
        return 2
    landed = json.load(io.open(path, encoding="utf-8"))

    if landed.get("face_count") != fresh["face_count"]:
        fails.append("AC-FRS1 face_count landed=%s fresh=%s" % (landed.get("face_count"), fresh["face_count"]))
    kept = {f["face"]: f for f in landed.get("faces", [])}
    fresh_faces = {f["face"]: f for f in fresh["faces"]}
    if set(kept) != set(fresh_faces):
        fails.append(
            "AC-FRS1 face set drifted missing=%s extra=%s"
            % (sorted(set(fresh_faces) - set(kept)), sorted(set(kept) - set(fresh_faces)))
        )
    for name, now in sorted(fresh_faces.items()):
        was = kept.get(name)
        if not was:
            continue
        for key in ("bytes", "controls", "out"):
            if was.get(key) != now[key]:
                fails.append("AC-FRS3 %s %s landed=%s fresh=%s" % (name, key, was.get(key), now[key]))
    if landed.get("actionable_count") != fresh["actionable_count"]:
        fails.append("AC-FRS3 actionable_count landed=%s fresh=%s" % (landed.get("actionable_count"), fresh["actionable_count"]))
    if landed.get("readonly_count") != fresh["readonly_count"]:
        fails.append("AC-FRS3 readonly_count landed=%s fresh=%s" % (landed.get("readonly_count"), fresh["readonly_count"]))

    for name in fresh["dead_ends"]:
        fails.append("AC-FRS2 operable face links nowhere: %s (controls=%d)" % (name, fresh_faces[name]["controls"]))
    if fresh["dead_ends"] != (landed.get("dead_ends") or []):
        fails.append("AC-FRS2 dead_end list landed=%s fresh=%s" % (landed.get("dead_ends"), fresh["dead_ends"]))

    if fresh["actionable_count"] < 1 or fresh["readonly_count"] < 1:
        fails.append(
            "AC-FRS4 degenerate reading actionable=%d readonly=%d"
            % (fresh["actionable_count"], fresh["readonly_count"])
        )

    for hop in fresh["missing_hops"]:
        fails.append("AC-FRS5 declared hop missing from disk: %s" % hop)
    if fresh["missing_hops"] != (landed.get("missing_hops") or []):
        fails.append("AC-FRS5 missing_hops landed=%s fresh=%s" % (landed.get("missing_hops"), fresh["missing_hops"]))

    # AC-FRS6: reachability from the entry page, measured, not declared.
    for name in fresh["unreachable"]:
        fails.append("AC-FRS6 face not reachable from the entry page: %s" % name)
    if sorted(fresh["unreachable"]) != sorted(landed.get("unreachable") or []):
        fails.append("AC-FRS6 unreachable landed=%s fresh=%s" % (landed.get("unreachable"), fresh["unreachable"]))

    # AC-FRS7/FRS8/FRS9: one endpoint table, no silent endpoint, no grave.
    tpath = TERMINI
    if out:
        tpath = os.path.join(os.path.dirname(path), "route-termini.json")
    if not os.path.exists(tpath):
        fails.append("AC-FRS7 endpoint table missing from disk: %s" % os.path.basename(tpath))
        table_rows = []
    else:
        table = json.load(io.open(tpath, encoding="utf-8"))
        table_rows = table.get("termini") or []
        if table.get("terminus_count") != fresh["terminus_count"]:
            fails.append(
                "AC-FRS9 terminus_count table=%s fresh=%s"
                % (table.get("terminus_count"), fresh["terminus_count"])
            )
    fresh_termini = {t["face"]: t for t in fresh["termini"]}
    declared = {t.get("face"): t for t in table_rows}
    for name in sorted(set(fresh_termini) - set(declared)):
        fails.append("AC-FRS7 silent endpoint (no declaration): %s" % name)
    for name in sorted(set(declared) - set(fresh_termini)):
        now = fresh_faces.get(name)
        if now is None:
            fails.append("AC-FRS8 declared endpoint no longer on disk: %s" % name)
        else:
            fails.append(
                "AC-FRS8 declared endpoint now links onward: %s (out=%d)" % (name, now["out"])
            )
    for name, now in sorted(fresh_termini.items()):
        was = declared.get(name)
        if not was:
            continue
        if not now["title"]:
            fails.append("AC-FRS7 endpoint has no title on the page: %s" % name)
        if was.get("title") != now["title"]:
            fails.append("AC-FRS7 endpoint title drifted %s table=%r page=%r" % (name, was.get("title"), now["title"]))
        if was.get("bytes") != now["bytes"] or was.get("controls") != now["controls"]:
            fails.append(
                "AC-FRS7 endpoint measure drifted %s table=%s/%s disk=%s/%s"
                % (name, was.get("bytes"), was.get("controls"), now["bytes"], now["controls"])
            )
        back = was.get("back") or ""
        target = fresh_faces.get(back)
        if target is None:
            fails.append("AC-FRS9 back hop not on disk: %s -> %s" % (name, back))
        elif target["controls"] < 1:
            fails.append("AC-FRS9 back hop is not operable: %s -> %s (controls=%d)" % (name, back, target["controls"]))
        if was.get("back") != fresh["back_default"]:
            fails.append("AC-FRS9 back hop is not the one closure constant: %s -> %s" % (name, was.get("back")))
    if not fresh["back_operable"]:
        fails.append("AC-FRS9 back default is not operable: %s" % fresh["back_default"])

    verdict = "PASS" if not fails else "FAIL"
    print(
        "FACE-ROUTE SCAN %s criteria=9 faces=%d actionable=%d readonly=%d dead_end=%d hops=%d termini=%d unreachable=%d fails=%d"
        % (
            verdict,
            fresh["face_count"],
            fresh["actionable_count"],
            fresh["readonly_count"],
            len(fresh["dead_ends"]),
            len(fresh["declared_hops"]),
            fresh["terminus_count"],
            len(fresh["unreachable"]),
            len(fails),
        )
    )
    for f in fails:
        print("  - " + f)
    return 0 if not fails else 2


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--preview")
    ap.add_argument("--out")
    ap.add_argument("--hops-base")
    a = ap.parse_args(argv)
    if a.write:
        return write(a.preview, a.out, a.hops_base)
    return check(a.preview, a.out, a.hops_base)


if __name__ == "__main__":
    sys.exit(main())
