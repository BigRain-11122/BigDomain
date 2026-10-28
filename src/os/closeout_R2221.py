# closeout_R2221.py - single-writer closeout for the R2221 battery round.
# Updates state.json (tick + two log lines), then rebuilds the derived
# self_drive block of docs/status-export.json through the canonical
# recompute() in check_export_consistency.py (F3: never hand-written),
# refreshes the CEO face and prepends the round result row.
# Pure stdlib, ASCII source, utf-8 LF writer.
import datetime
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P_STATE = os.path.join(HERE, "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402

LOG_LINE = (
    "2026-10-29 R2221 (five-silence scan clean at open: decisions.md 274 "
    "non-empty rows carrying 180 content-addressed tokens with ZERO new "
    "against the stored 185-token baseline; the group ledger carries the "
    "same three @BigDomain patrol rows already paid off with zero "
    "unreplied; the group orders head is unchanged; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate; tree clean, no index.lock) - "
    "carried verification debt discharged on the committed HEAD 8a904359 "
    "tree, with NO product code touched because a battery walking the tree "
    "would have measured a mixed tree (the R2168 rule). Battery: RUNNER "
    "PASS 410/410 suites green plus reconcile controls 7/7 in 1013.5s "
    "(qa/reconcile-all-R2221.log, body written by src/os/battery_stream.py "
    "as single-writer utf-8 LF and never a shell redirection), with the "
    "birth-site tmp sweep inside the same battery window reclaiming "
    "candidates=908 removed=908 busy=0 failed=0 reclaimed=319.53 MiB. The "
    "four post-battery sections then all passed in the new "
    "src/os/battery_followup_R2221.py and were appended to the same log "
    "(749889 bytes, CRLF=0 lone CR=0): matrix regenerated to 410 suites / "
    "3402 criteria and read back (docs/sandbox-suite-matrix.md, 39952 "
    "bytes, green=410/410), fingerprint chain CLEAN over five domains "
    "(ledger/lobby/member/pay/ugc), runner profile --daily --check PASS "
    "against a byte-identical baseline, and the qa writer census re-frozen "
    "then DRIFT-CLEAN on both legs (files=2115 tee=1587 baselined=528 "
    "disappeared=0 flags=0). Counts moved the right way against R2216: "
    "suites 408->410 with criteria 3386->3402, and the census picked up the "
    "two new evidence writers this family of rounds always adds. Product "
    "score honestly zero - this window bought certainty, not features - and "
    "the next window can claim the explore head behind the "
    "merchant-number-gated payment row (seed R2213, five of six still open) "
    "or the docker-host-gated sandbox boot."
)
TOKENS_LINE = (
    "R2221 tokens: local=~32k api=0 api_reason=battery round on the "
    "committed tree - full reconcile battery via battery_stream plus four "
    "follow-up sections in a new script, plus state/export closeout, zero "
    "cloud calls and no product code changed (the R2168 mixed-tree rule)"
)
RESULT_TEXT = (
    "R2221: five-silence scan clean with an exact decision-token match "
    "(zero new against a 185-token baseline), the carried battery debt "
    "discharged on the committed 8a904359 tree - RUNNER PASS 410/410 suites "
    "plus controls 7/7 in 1013.5s with 908/908 tmp worlds reclaimed, then "
    "matrix regenerated to 410 suites / 3402 criteria, fingerprint chain "
    "CLEAN over five domains, runner profile check PASS and the qa writer "
    "census DRIFT-CLEAN on both legs; no product code changed by design, so "
    "the product score is honestly zero."
)
CEO_CURRENT = (
    "R2221: the whole plant was re-verified against the exact commit the "
    "last product round left behind - every one of the 410 sandbox suites "
    "green, the seven reconcile controls still catching tampering, the "
    "suite matrix in docs/sandbox-suite-matrix.md regenerated to 410 "
    "suites / 3402 criteria, the five migration fingerprints clean, and the "
    "evidence-writer census clean on both legs"
)
CEO_LATEST = (
    "qa/reconcile-all-R2221.log (749889 bytes, single UTF-8 LF writer) + "
    "docs/sandbox-suite-matrix.md regenerated 410/410 (2026-10-29)"
)
CEO_NEXT = (
    "R2222 within 24h: a new apimarket product face from the open explore "
    "seed R2213 (five of six rows still unclaimed) on this freshly verified "
    "tree"
)


def main():
    raw = io.open(P_STATE, encoding="utf-8").read()
    state = json.loads(raw)
    state["tick"] = int(state.get("tick", 0)) + 1
    state.setdefault("log", []).append(LOG_LINE)
    state["log"].append(TOKENS_LINE)
    with io.open(P_STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    derived, state2, export, pat = cec.recompute()
    derived = dict(derived)
    derived["tick"] = state2["tick"]
    derived["round"] = "R2221"
    export["self_drive"] = derived
    export["ceo_face"] = {
        "current": CEO_CURRENT,
        "latest_artifact": CEO_LATEST,
        "next_milestone": CEO_NEXT,
    }
    export["do"] = (
        "R2221 verification round on the silicon-domain co-creation "
        "platform: the whole sandbox plant re-verified on the committed "
        "tree, with zero product code touched by design"
    )
    label = pat["tick_row_label"]
    results = [r for r in export.get("results", [])
               if not (isinstance(r, list) and len(r) >= 2 and r[1] == label)]
    results.insert(0, ["R2221", RESULT_TEXT])
    results.append([state2["tick"], label])
    export["results"] = results
    export["export_ts"] = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))).isoformat(
            timespec="seconds")
    with io.open(P_EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(export, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("CLOSEOUT OK tick=%s results=%d" % (state2["tick"],
                                              len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())