"""R2421 closeout part 2: export face, backlog row, heartbeat (one-off)."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PATTERNS = os.path.join(SRC, "export_consistency_patterns.json")
BACKLOG = os.path.join(SRC, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
STAMP = "2026-11-04T01:30:00+08:00"
ROUND = 2421

EXPORT_DO = (
    "R2421 verification: the battery came back red on ONE test defect - the "
    "AC-MSC4 live leg pinned qa/reconcile-all-R2418.log instead of asking the "
    "shipped doc which evidence it records - and the repair at the birth site "
    "then read RUNNER PASS 538/538 suites at criteria 4204 exactly as "
    "pre-registered"
)
EXPORT_ARTIFACT = (
    "src/os/test_matrix_stamp_compare.py (AC-MSC4 live leg now asks "
    "suite_matrix.doc_evidence_face) + qa/reconcile-all-R2421-retry.log "
    "(840488B, RUNNER PASS 538/538) + docs/sandbox-suite-matrix.md (51830B, "
    "538 suites / 4204 criteria)"
)
EXPORT_MILESTONE = (
    "reconcile-battery-R2421: one green RUNNER PASS over the 538 suites / "
    "4204 criteria on the committed R2421 tree first, then the four follow-up "
    "sections, then a product face at the tech head AC-PIAG1"
)
EXPORT_DUE = "2026-11-04T23:00:00+08:00"

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2421] R2421 verification window: the debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2420 (pre-registered 538 suites "
    "/ 4204 criteria), so the battery ran FIRST on the committed 08d7f5e4 tree "
    "with zero product edits and came back RED ON ONE TEST BUG, NOT ON CODE - "
    "537/538 suites with the criteria total 4204 exactly as pre-registered "
    "(1101.7s, qa/reconcile-all-R2421.log kept as the red leg), the only red "
    "being os-matrix-stamp-compare AC-MSC4 with measured live=FAIL check=0 "
    "agrees=False. Cause read from the suite source: its live leg hard-pinned "
    "qa/reconcile-all-R2418.log while the shipped doc had been regenerated "
    "from qa/reconcile-all-R2419.log, so the criterion split on the evidence "
    "FACE - the exact shape suite_matrix.doc_evidence_face (R1749) exists to "
    "answer - and the law under test was never at fault. REPAIRED AT THE BIRTH "
    "SITE, no criterion widened: the live leg now asks "
    "suite_matrix.doc_evidence_face for the evidence the SHIPPED doc records "
    "(asked at CALL time, falling back to the pinned file only when the doc "
    "carries no --evidence segment), suite reads SUITE PASS 6/6, repair "
    "committed ALONE as 48eeb76d. RETRY on the committed repair tree: RUNNER "
    "PASS 538/538 suites green plus controls 7/7 in 1011.2s with criteria 4204 "
    "- the pre-registered number to the unit - TMP RECLAIM 932/932, evidence "
    "qa/reconcile-all-R2421-retry.log (840488B, crlf=0). Four follow-up "
    "sections: designed first FAIL on the stale matrix doc (51813B against "
    "51830B, no rewrite), regeneration to 51830B at 538/4204 with --check "
    "byte-identical, re-run VERDICT R2421 PASS (matrix byte-identical, "
    "fingerprint CLEAN 5 domains, profile byte-identical, census "
    "DRIFT-CLEAN). Register: reconcile-battery-R2420 closed through debt_close "
    "at its predicted 101751B -> 101754B (measured, readback=ok) and "
    "reconcile-battery-R2421 registered first=yes at 101754B -> 102384B "
    "because the repair is a real src byte change; open=3 done=134. Zero "
    "product code shipped, honestly 0 product points. Disclosed: AC-MSC4 had "
    "only ever been green because doc and pinned evidence happened to be the "
    "same round, i.e. it was measuring a coincidence.\n"
)


def _read(path, encoding="utf-8", newline=None):
    with io.open(path, "r", encoding=encoding, newline=newline) as handle:
        return handle.read()


def _write(path, text, newline=""):
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def step_export():
    patterns = json.loads(_read(PATTERNS))
    label = patterns["tick_row_label"]
    export = json.loads(_read(EXPORT))
    export["export_ts"] = STAMP
    export["do"] = EXPORT_DO
    face = export["ceo_face"]
    face["current"] = EXPORT_DO
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_MILESTONE
    face["next_milestone_due"] = EXPORT_DUE
    face["updated_at"] = STAMP
    results = [row for row in export["results"]
               if str(row[0]) != str(ROUND)]
    results.insert(0, [str(ROUND), EXPORT_DO])
    labelled = [row for row in results if len(row) >= 2 and row[1] == label]
    if not labelled:
        results.insert(0, [str(ROUND), label])
    else:
        for row in labelled:
            row[0] = str(ROUND)
    export["results"] = results
    outs = [item for item in export["outs"]
            if "test_matrix_stamp_compare" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    import sys
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    drive = export["self_drive"]
    import check_export_consistency
    derived = check_export_consistency.recompute()[0]
    drive["log_lines_in_window"] = derived["log_lines_in_window"]
    drive["substantive_non_idle_mention_lines"] = \
        derived["substantive_non_idle_mention_lines"]
    import queue_floor
    gauge = queue_floor.gauge(ROOT)
    fresh = {row["queue"]: row for row in gauge["queues"]}
    for row in export["queue"]["queues"]:
        live_row = fresh.get(row.get("queue"))
        if not live_row:
            continue
        for key, value in live_row.items():
            row[key] = value
    export["queue"]["floors"] = gauge["floors"]
    export["queue"]["verdict"] = gauge["verdict"]
    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    _write(EXPORT, text, newline="\n")
    print("export refreshed %dB tick_rows=%d"
          % (len(text.encode("utf-8")), len(labelled) or 1))


def step_backlog():
    text = _read(BACKLOG)
    if "R2421 verification window" in text:
        print("backlog row already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(BACKLOG, text + BACKLOG_ROW, newline="\n")
    print("backlog appended %dB" % len(BACKLOG_ROW.encode("utf-8")))


def step_heartbeat():
    line = ("2026-11-04T01:30:00+08:00 tick=2421 R2421 verification - the "
            "battery ran first and found ONE test defect (AC-MSC4 pinned a "
            "round's evidence instead of asking the doc), repaired at the "
            "birth site and committed alone, then RUNNER PASS 538/538 at "
            "criteria 4204 exactly as pre-registered and four follow-up "
            "sections PASS; one debt row closed, one successor registered")
    text = _read(HEARTBEAT)
    if line in text:
        print("heartbeat line already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(HEARTBEAT, text + line + "\n", newline="\n")
    print("heartbeat appended")


if __name__ == "__main__":
    step_export()
    step_backlog()
    step_heartbeat()