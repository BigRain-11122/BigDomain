#!/usr/bin/env python3
"""R2020 export flush (closeout): ceo_face + results row + self_drive recompute.

Shares the canonical self_drive caliber with check_export_consistency via
import (single caliber, closes the two-caliber gap per the module docstring).
Byte-safe: json round-trip with indent=2 matching the on-disk layout;
tick row synced to state.tick; check() re-run at the end for the PASS stamp.
"""
import datetime as _dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402

P_EXPORT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "status-export.json")

CURRENT = (
    "R2020: QA charter daily-crawl round + same-day daily-reconcile standing row executed "
    "(the R2019-held crawl flag discharged as this round's first item per the takeover's "
    "honest note). (1) Daily reconcile: RECONCILE-DAILY 20261018 verdict=PASS runner_exit=0 "
    "sentinel=ok profile=ok census=ok, RUNNER PASS 236/236 suites green + reconcile controls "
    "7/7 in 226.1s = qa/reconcile-daily-20261018.log (G0 green, standing row continues). "
    "(2) W27 legal-source harvest: Regulations on Security Assessment for Internet "
    "Information Services with Public-opinion or Social-mobilization Attributes (CAC+MPS, "
    "issued 2018-11-15, effective 2018-11-30, 17 articles) official fulltext A-grade "
    "direct-captured from the gov.cn policy library (1-try search + 1-get, zero negatives), "
    "consumed into benchmarks sections 1/2/3/4 (new regulatory block + execution-standard "
    "row 11 + source row + record row) + intelligence-wall W27 dual rows; art. 2 scope "
    "directly names mini-programs/chatrooms/messaging groups = visitor mini-program + lobby "
    "rooms; art. 3 pre-launch / pre-function-addition assessment gate + art. 5 eight "
    "assessment items (staffing statute source no.7) + art. 7 national-platform submission "
    "before launch or within 30 working days + art. 13 public risk notice for refusal = the "
    "launch-ops security-assessment step statute body (closes the W13 candidate). "
    "benchmarks_refreshed=2026-10-18. (3) Group faces: DEC D-20261018-01 (BigCompute "
    "restoration-watch; the decision note itself states zero BigDomain pending rulings) "
    "acked no-action, baseline rows 356->360 tokens merged; group-orders tail batch 10-18 "
    "01:53..13:5x five lines all MV-lane dispatches acked no-action, last_order baseline "
    "-> 2026-10-18 13:5x. (4) fold R550 honored (tail-3 4885B -> one rolling line, 66 tokens "
    "embedded zero-loss, archive verbatim + preop backup logs/state-preop-R2020.bak, post "
    "76531B under the line). Score 2."
)
ARTIFACT = (
    "qa/reconcile-daily-20261018.log (RUNNER PASS 236/236 + controls 7/7) + "
    "qa/smoke-R2020.log + qa/smoke-R2020.png (rendered from the real log) + "
    "benchmarks W27 4-place entry (docs/global-benchmarks.md) + intelligence-wall "
    "W27 dual rows (2026-10-18)"
)
MILESTONE = (
    "next crawl round 2026-10-19 (charter daily cadence; 7-day benchmark window next due "
    "2026-10-25) + P3 explore queue next open heads (dev_sales_board month-window, "
    "dev_sales_board zero-listing boundary persist, yearbooks_combined multi-year persist) "
    "+ launch-ops security-assessment step drafting candidate (W27 statute body in place, "
    "next spec-revision window); window <=48h (by 2026-10-20)"
)
RESULT_ROW = (
    "R2020: QA charter daily-crawl round + same-day daily reconcile delivered. Daily "
    "reconcile standing row: RECONCILE-DAILY 20261018 verdict=PASS runner_exit=0 "
    "sentinel=ok profile=ok census=ok, RUNNER PASS 236/236 suites green + controls 7/7 "
    "226.1s = qa/reconcile-daily-20261018.log. W27 legal-source harvest: CAC+MPS Security "
    "Assessment Regulations for public-opinion/social-mobilization services (2018-11-30 "
    "effective, 17 articles) fulltext A-grade from gov.cn policy library (1-try search + "
    "1-get, zero negatives), consumed 4-place into benchmarks (new block + row 11 + source "
    "row + record row) + intelligence-wall dual rows; art. 2 names mini-programs/chatrooms/"
    "messaging groups = our visitor mini-program + lobby rooms; art. 3 pre-launch assessment "
    "gate + art. 5 eight items (staffing source no.7) + art. 7 platform submission before "
    "launch / 30 working days + art. 13 refusal = public risk notice = launch-ops "
    "security-assessment step statute body (W13 candidate closed). benchmarks_refreshed="
    "2026-10-18. Group faces: DEC D-20261018-01 acked no-action (rows 356->360, tokens "
    "merged); orders tail batch 10-18 01:53..13:5x all MV-lane acked (last_order -> 10-18 "
    "13:5x). fold R550 honored (tail-3 4885B -> one rolling line, 66 tokens zero-loss, "
    "archive + preop, post 76531B). Score 2."
)


def main():
    with io.open(P_EXPORT, "r", encoding="utf-8") as f:
        export = json.load(f)

    export["export_ts"] = _dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["ceo_face"]["current"] = CURRENT
    export["ceo_face"]["latest_artifact"] = ARTIFACT
    export["ceo_face"]["next_milestone"] = MILESTONE

    if not export["results"] or export["results"][0][0] != "R2020":
        export["results"].insert(0, ["R2020", RESULT_ROW])

    tick_label = None
    with io.open(os.path.join(HERE, "export_consistency_patterns.json"), "r", encoding="utf-8-sig") as f:
        tick_label = json.load(f)["tick_row_label"]
    hit = 0
    for row in export["results"]:
        if len(row) >= 2 and row[1] == tick_label:
            row[0] = "2020"
            hit += 1
    if hit != 1:
        raise SystemExit("FATAL: tick row count=%d (expected 1)" % hit)

    derived, state, _export, _pat = cec.recompute()
    method = export["self_drive"].get("method")
    sd = dict(derived)
    sd["method"] = method
    export["self_drive"] = sd

    with io.open(P_EXPORT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
        f.write("\n")

    report, n_pass, n_fail = cec.check()
    print("\n".join(report[-6:]))
    print("CHECK n_pass=%d n_fail=%d" % (n_pass, n_fail))
    if n_fail:
        raise SystemExit(2)
    print("EXPORT-FLUSH-OK tick=2020 self_drive=%s" % json.dumps(derived, ensure_ascii=False))


if __name__ == "__main__":
    main()
