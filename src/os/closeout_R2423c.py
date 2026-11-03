"""R2423 closeout part 2: export face, backlog row, heartbeat (one-off)."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PATTERNS = os.path.join(SRC, "export_consistency_patterns.json")
BACKLOG = os.path.join(SRC, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
STAMP = "2026-11-04T04:10:00+08:00"
ROUND = 2423

EXPORT_DO = (
    "R2423 verification window: the carried battery ran FIRST on the committed "
    "tree and came back RED ON EVIDENCE, NOT CODE - two R2422 evidence logs had "
    "been shell-captured as ps-utf16 and the qa writer census read them as "
    "new-dialect - so the transport was repaired at the birth site with the "
    "payload proved identical, and the retry read RUNNER PASS 539/539 suites at "
    "4210 criteria exactly as pre-registered with all four follow-up sections "
    "PASS"
)
EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2423-retry.log (RUNNER PASS 539/539, 4210 criteria, "
    "907.8s) + qa/reconcile-all-R2423.log (the red leg, 538/539) + "
    "docs/sandbox-suite-matrix.md (539 suites / 4210 criteria, --check "
    "byte-identical) + src/os/repair_R2423.py (birth-site transport repair)"
)
EXPORT_MILESTONE = (
    "product-face-R2424: one product face on the tech head "
    "state/queue/tech.md line 489 prefix AC-PICB1 (plain_import_comma_binding, "
    "AC-PICB1..AC-PICB6 already pinned at R2422), committed before any battery"
)
EXPORT_DUE = "2026-11-05T18:00:00+08:00"

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2423] R2423 verification window: the debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2422 with a pre-registered "
    "target of 539 suites / 4210 criteria, so the battery ran FIRST on the "
    "committed tree with zero product edits. It came back RED ON EVIDENCE, NOT "
    "CODE: RUNNER FAIL 538/539 with criteria total 4210 exactly as "
    "pre-registered, the only red being reconcile-daily-census at exit 2, which "
    "named qa/plain-import-alias-gate-R2422.log and its live companion as "
    "ps-utf16 - both had been captured through a PowerShell redirect inside a "
    "pile the census reads as one utf-8 LF dialect. Repaired at the BIRTH SITE, "
    "never by widening the baseline: src/os/repair_R2423.py decodes utf-16, "
    "asks the shipped run_identity.normalize for the allowed normalisation, "
    "writes utf-8 LF through one atomic replace and proves the line set "
    "identical on both sides (2094B -> 1032B and 274B -> 135B, read-back equal), "
    "after which the census read DRIFT-CLEAN flags=0 at an untouched baseline; "
    "the repair was committed ALONE as f0271477. The retry leg then read RUNNER "
    "PASS (539/539 suites, controls 7/7, 907.8s, evidence "
    "qa/reconcile-all-R2423-retry.log 841118B) with the measured criteria total "
    "4210 - the pre-registered number to the unit. The four follow-up sections "
    "produced the designed first FAIL (matrix 51905B against 51924B, no "
    "rewrite), docs/sandbox-suite-matrix.md was regenerated to 51924B at 539 "
    "suites / 4210 criteria with --check byte-identical, and the re-run read "
    "VERDICT R2423 PASS failing=none. Register: reconcile-battery-R2422 closed "
    "through debt_close at its predicted 102964B -> 102967B and ONE leader row "
    "product-face-R2424 appended first=yes at 102967B -> 103429B naming the "
    "next window's product face; open=2 done=136. Closeout: state folded at a "
    "true round-block boundary (items 2..53, predicted 49479B = measured, 79 "
    "tokens covered, none missing), the fold-created residue for R2409/R2412/"
    "R2415 spliced through the shipped batch CLI (260 -> 263 entries, TRIAGED), "
    "and the four ledger suites plus the stamp-exempt and residue suites re-read "
    "green afterwards. Zero product code shipped, honestly 0 product points. "
    "Disclosed rather than swept: the R2422 note had recorded that log at 1516B "
    "while it was 2094B of utf-16 on disk, so that byte count was itself wrong "
    "and is corrected here.\n"
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
    results = [row for row in export["results"] if str(row[0]) != str(ROUND)]
    results.insert(0, [str(ROUND), EXPORT_DO])
    labelled = [row for row in results if len(row) >= 2 and row[1] == label]
    if not labelled:
        results.insert(0, [str(ROUND), label])
    else:
        for row in labelled:
            row[0] = str(ROUND)
    export["results"] = results
    outs = [item for item in export["outs"]
            if "plain_import_alias_gate" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import check_export_consistency
    derived = check_export_consistency.recompute()[0]
    drive = export["self_drive"]
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
    print("export refreshed %dB queues=%s"
          % (len(text.encode("utf-8")), gauge["verdict"]))


def step_backlog():
    text = _read(BACKLOG)
    if "R2423 verification window: the debt gate" in text:
        print("backlog row already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(BACKLOG, text + BACKLOG_ROW, newline="\n")
    print("backlog appended %dB" % len(BACKLOG_ROW.encode("utf-8")))


def step_heartbeat():
    line = ("2026-11-04T04:10:00+08:00 tick=2423 R2423 verification window - "
            "the battery ran first and went red on two shell-captured evidence "
            "logs, repaired at the birth site with the payload proved, then the "
            "retry read RUNNER PASS 539/539 at 4210 criteria exactly as "
            "pre-registered with all four follow-up sections PASS; debt row "
            "closed, leader registered, state folded at a block boundary with "
            "the fold-created residue spliced to TRIAGED")
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