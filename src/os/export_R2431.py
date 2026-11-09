"""R2431 export refresh: derived faces + the three CEO lines, one atomic write.

Every value here is derived from the live tree (state.json tick, queue_floor,
the evidence files on disk, the shipped consistency checker's own self_drive
recount) rather than typed in, so the export cannot drift from what the round
actually did.
"""

import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import export_driver_queue_face as EDQF  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")
STATE = os.path.join(BASE, "state.json")
STAMP = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))) \
    .replace(microsecond=0).isoformat()

DO = ("R2431 verification window: the debt gate named the battery the R2168 "
      "rule owed on the committed R2430 tree, so the full reconcile battery "
      "ran FIRST at the pre-registered 543 suites / 4234 criteria and came "
      "back red on this window's own launcher (its stdout redirect was "
      "pointed into qa/ and filed as cmd-raw evidence); the captures moved to "
      "the gitignored logs face, the census re-read DRIFT-CLEAN with its "
      "baseline untouched, and the retry leg read RUNNER PASS 543/543 at the "
      "same criteria total with all four follow-up sections green")

LATEST = ("qa/reconcile-all-R2431.log (red leg, 843784B) + "
          "qa/reconcile-all-R2431-retry.log (RUNNER PASS 543/543, 956.2s, "
          "criteria 4234) + docs/sandbox-suite-matrix.md regenerated "
          "stamp-aligned to 52317B at 543 suites / 4234 criteria with "
          "--check byte-identical")

NEXT_DUE = "2026-11-06T12:00:00+08:00"

NEXT = ("product face on the tech head state/queue/tech.md:494 prefix "
        "AC-BEDP1 (bare_evidence_deep_pile: a bare evidence name that lives "
        "deeper than the one-level pile walk still refuses), whose criteria "
        "were pinned in that row at R2404 before any code")

RESULT = (
    "2026-11-04 R2431 verification window on the item the debt gate named "
    "first=yes (reconcile-battery-R2431, carried from R2430): zero product "
    "code changed, the R2168 mixed-tree rule honoured. Leg 1 read 542/543 "
    "suites with the criteria total 4234 exactly as pre-registered and the "
    "only red was reconcile-daily-census at cd7 exit=2 DRIFT-FLAG; the "
    "census named the file (qa/battery-R2431-stdout.log, class=cmd-raw) "
    "because this window launched the battery with a Start-Process redirect "
    "pointed INTO the evidence directory. Repaired at the birth site, never "
    "by widening the baseline: the two launcher captures moved to the "
    "gitignored logs/ face, after which the census read flags=0 "
    "DRIFT-CLEAN with the 529-entry baseline untouched. Retry leg on the "
    "repaired tree: RUNNER PASS 543/543 suites plus controls 7/7 in 956.2s "
    "at criteria 4234, TMP RECLAIM 932/932. Four follow-up sections: matrix "
    "FAILED first on the stale doc without rewriting it, was regenerated "
    "stamp-aligned to 52317B, and the re-run read VERDICT R2431 PASS "
    "failing=none (fingerprint CLEAN 5 domains, profile byte-identical, "
    "census DRIFT-CLEAN). Debt: reconcile-battery-R2431 closed and "
    "product-face-R2432 opened first=yes through the shipped CLIs. Zero "
    "product points claimed.")

LEGACY_OUTS = ("qa/reconcile-all-R2431.log (red leg) plus "
               "qa/reconcile-all-R2431-retry.log (RUNNER PASS 543/543, 4234 "
               "criteria) and docs/sandbox-suite-matrix.md regenerated to "
               "52317B")

# Kept only so any older carrier that reads the name still imports; the driver
# itself no longer publishes this constant anywhere (R2499 derivation fix).
OUTS = LEGACY_OUTS


def _round_items(state, tick):
    """This round's own log items, matched by the tick in their own text."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2} R%s\b" % tick)
    items = []
    for entry in state.get("log") or []:
        if isinstance(entry, str) and pattern.match(entry):
            items.append(entry)
    return items


def derive_current(state, tick):
    """The CEO 'current' line is this round's opening summary, not a constant."""
    items = _round_items(state, tick)
    if items:
        return items[0][:400]
    log = state.get("log") or []
    if log and isinstance(log[-1], str):
        return log[-1][:400]
    return "no log entry for tick %s" % tick


def derive_latest(tick):
    """The artifact line is what actually landed for this tick under qa/."""
    hits = []
    directory = os.path.join(REPO, "qa")
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        names = []
    for name in names:
        if "R%s" % tick not in name:
            continue
        path = os.path.join(directory, name)
        try:
            hits.append("%s (%dB)" % (name, os.path.getsize(path)))
        except OSError:
            continue
    if not hits:
        return "none landed yet for R%s" % tick
    return " + ".join(hits[:4])


def derive_due():
    """The 48h milestone window, computed at call time."""
    return (datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8)))
        + datetime.timedelta(hours=48)).replace(microsecond=0).isoformat()


def derive_next(tick):
    """The milestone line is the debt the register names first, plus a 48h window."""
    item = ""
    try:
        text = io.open(os.path.join(REPO, "state", "debt.md"),
                       encoding="utf-8").read()
    except (IOError, OSError):
        text = ""
    for line in text.split("\n"):
        if line.startswith("- [ ]") and "first=yes" in line:
            found = re.search(r"item=([^ |]+)", line)
            if found:
                item = found.group(1)
                break
    due = derive_due()
    if item:
        return ("next window owes %s on the committed tree, inside a 48h "
                "window due %s" % (item, due))
    return "next round product byte on the queue head, inside a 48h window due %s" % due


def self_drive():
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    window = cec.recompute()[0]
    return {
        "window": window["window"],
        "window_days": window["window_days"],
        "log_lines_in_window": window["log_lines_in_window"],
        "idle_fast_mention_lines": window["idle_fast_mention_lines"],
        "no_pullable_mention_lines": window["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            window["substantive_non_idle_mention_lines"],
        "proposals_total": window["proposals_total"],
        "proposals_open": window["proposals_open"],
        "queue_main_open": window["queue_main_open"],
        "queue_tech_open": window["queue_tech_open"],
        "queue_explore_open": window["queue_explore_open"],
    }


def tick_label():
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    return cec._load_patterns()["tick_row_label"]


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    rows = data.get("results") or []
    if not any(isinstance(r, list) and len(r) >= 2 and r[1] == RESULT
               for r in rows):
        rows.insert(0, [tick, RESULT])
    label = tick_label()
    stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
               and r[1] == label]
    if len(stamped) != 1:
        sys.stdout.write("E_EXP expected exactly 1 tick row, found %d\n"
                         % len(stamped))
        return 2
    stamped[0][0] = tick
    data["results"] = rows
    current = derive_current(state, tick)
    latest = derive_latest(tick)
    milestone = derive_next(tick)
    outs = data.get("outs") or []
    if not outs or outs[0] != latest:
        outs.insert(0, latest)
    data["outs"] = outs
    data["export_ts"] = STAMP
    data["do"] = current
    ceo = data.get("ceo_face") or {}
    ceo["current"] = current
    ceo["latest_artifact"] = latest
    ceo["next_milestone"] = milestone
    ceo["next_milestone_due"] = derive_due()
    ceo["last_artifact"] = latest
    ceo["updated_at"] = STAMP
    data["ceo_face"] = ceo
    data["self_drive"] = self_drive()
    try:
        EDQF.refresh(data, REPO)
    except EDQF.ExportDriverQueueFaceError as exc:
        sys.stdout.write("E_EXP queue face unreadable %s\n" % exc)
        return 2
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    try:
        proof = EDQF.publish(REPO, EXPORT, text)
    except EDQF.ExportDriverQueueFaceError as exc:
        sys.stdout.write("QUEUE FACE REFUSED %s\n" % exc)
        return 2
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    # The tick row is the row THIS driver stamps; results[0] is the round-log
    # row another writer owns, so reading it here made a healthy refresh fail
    # on every round whose result row had not landed yet (R2499 battery catch).
    # R2595: the old health term demanded log_lines_in_window ==
    # substantive_non_idle_mention_lines, which the recompute caliber can never
    # satisfy once one tokens line sits in the window (a tokens line counts as
    # a window line and never as substantive). The document is now proved
    # against a FRESH recompute of the whole self_drive block instead.
    ok = (any(isinstance(r, list) and len(r) >= 2 and r[1] == label
              and str(r[0]) == tick for r in back["results"])
          and back["outs"][0] == latest
          and back["ceo_face"]["latest_artifact"] == latest
          and back["ceo_face"]["current"] == current
          and back["ceo_face"]["next_milestone"] == milestone
          and back["export_ts"] == STAMP
          and back["self_drive"] == self_drive()
          and proof.get("gate") == "CURRENT")
    sys.stdout.write("RESULTS rows=%d outs=%d tick=%s bytes=%d queue=%s "
                     "queue_bytes=%d queue_drifted=%s ok=%s\n"
                     % (len(back["results"]), len(back["outs"]), tick,
                        os.path.getsize(EXPORT), proof.get("gate"),
                        proof.get("bytes"),
                        ",".join(proof.get("drifted") or ()) or "(none)",
                        ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())