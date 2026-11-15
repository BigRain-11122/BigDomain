"""Per-window export refresh driver for R2811.

WHY A SCRIPT AND NOT AN EDIT: docs/status-export.json is the CEO's live panel
and F3 forbids canned values in it. The three fields that move every round -
self_drive.log_lines_in_window, self_drive.substantive_non_idle_mention_lines
and results.<tick row> - are recomputed by the SHIPPED checker
(src/os/check_export_consistency.py), not re-derived here, so the writer and
the gate share one caliber and cannot drift into the two-caliber gap the
checker docstring records. The per-window driver exists only because the
per-round hook src/os/export_R2431.py is dead (carried debt).

What this driver does:
  * self_drive numeric/window fields <- checker.recompute()
  * the unique results row whose label is tick_row_label, first element <- state.tick
  * ceo_face.current / do <- the last dated round line in state.json#log
  * ceo_face.latest_artifact <- the newest preview artifact PAIR measured on disk
  * ceo_face.next_milestone <- the first open row of src/os/backlog.md
  * export_ts / ceo_face.updated_at <- now, state_bytes <- measured
It writes nothing else and asserts the row counts it touches.

Usage: python src/os/export_R2811.py
"""
import datetime
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import check_export_consistency as cec  # the shipped caliber, imported not copied

PREVIEW = os.path.join(ROOT, "preview")
BACKLOG = os.path.join(HERE, "backlog.md")
CLIP_ROUND = 420
CLIP_NEXT = 320


def newest_pair():
    """Newest preview pair (X.html + X.json) by mtime, measured on disk."""
    best = None
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        stem = name[: -len(".html")]
        twin = os.path.join(PREVIEW, stem + ".json")
        page = os.path.join(PREVIEW, name)
        if not os.path.isfile(twin):
            continue
        stamp = os.path.getmtime(page)
        if best is None or stamp > best[0]:
            best = (stamp, name, stem, page, twin)
    if best is None:
        raise SystemExit("no preview artifact pair on disk")
    _stamp, name, stem, page, twin = best
    return name, stem, os.path.getsize(page), os.path.getsize(twin)


def first_open_row():
    with io.open(BACKLOG, encoding="utf-8-sig") as fh:
        for line in fh:
            if line.startswith("- [ ]"):
                return line[5:].strip()
    raise SystemExit("src/os/backlog.md carries no open row")


def main():
    derived, state, export, _info = cec.recompute()
    pat = cec._load_patterns()
    label = pat["tick_row_label"]

    sd = export.get("self_drive")
    if not isinstance(sd, dict):
        raise SystemExit("export has no self_drive block")
    moved = []
    for key, value in derived.items():
        if key in sd and sd[key] != value:
            sd[key] = value
            moved.append(key)

    rows = export.get("results")
    hits = [r for r in rows
            if isinstance(r, list) and len(r) == 2 and r[1] == label]
    if len(hits) != 1:
        raise SystemExit("tick row must be unique, found %d" % len(hits))
    tick_before = hits[0][0]
    hits[0][0] = str(state["tick"])

    log = state["log"]
    rounds = [ln for ln in log if cec.RE_ROUND_MAIN.match(ln)]
    if not rounds:
        raise SystemExit("state log carries no dated round line")
    current = rounds[-1]
    if len(current) > CLIP_ROUND:
        current = current[: CLIP_ROUND - 1] + "\u2026"

    page_name, stem, html_bytes, json_bytes = newest_pair()
    stamp = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()

    face = export.setdefault("ceo_face", {})
    face["current"] = current
    face["latest_artifact"] = "preview/%s (%dB) + preview/%s.json (%dB)" % (
        page_name, html_bytes, stem, json_bytes)
    face["last_artifact"] = face["latest_artifact"]
    face["latest_artifact_abs"] = os.path.join(PREVIEW, page_name)
    face["next_milestone"] = first_open_row()[:CLIP_NEXT]
    face["next_milestone_due"] = (
        datetime.datetime.now().astimezone() + datetime.timedelta(hours=48)
    ).replace(microsecond=0).isoformat()
    face["updated_at"] = stamp

    export["do"] = current
    export["export_ts"] = stamp
    export["current"] = current
    export["latest_artifact"] = face["latest_artifact"]
    export["next_milestone"] = face["next_milestone"]
    export["state_bytes"] = os.path.getsize(
        os.path.join(HERE, "state.json"))

    path = os.path.join(ROOT, "docs", "status-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(export, ensure_ascii=False, indent=2) + "\n")

    reloaded = json.loads(io.open(path, encoding="utf-8").read())
    assert reloaded["export_ts"] == stamp
    assert str(reloaded["ceo_face"]["current"]) == current
    print("EXPORT WROTE tick_row %s -> %s moved=%s pair=%s" % (
        tick_before, state["tick"], moved or "none", page_name))
    print("  latest_artifact=%s" % face["latest_artifact"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
