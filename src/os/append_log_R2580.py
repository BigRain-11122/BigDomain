"""R2580 state.json log append (verification window on reconcile-battery-R2579)."""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-09 R2580 VERIFICATION window on the battery the register named"
    " first (reconcile-battery-R2579, pre-registered 619 suites / 4690"
    " criteria). Target RE-MEASURED by import before the launch at 619 / 4690"
    " with 619 unique names. LEG 1 RED AND KEPT (qa/reconcile-all-R2579.log,"
    " 1047876B): RUNNER FAIL 4 assertions in THREE suites (os-ledger-lines"
    " AC-LGR8; os-ledger-archive AC-LGA7+AC-LGA8; os-ledger-baseline"
    " AC-LGB8), all three on the coverage gate of the round ledger lines."
    " BIRTH SITE FOUND BY MEASUREMENT, not guessed: audit(live) reported"
    " rounds_without_ledger=[2568] and the scoped baseline gate read"
    " clean=False new_missing=[2568] because the R2578 fold (log items 4..10)"
    " moved the R2568 block - including its own 'R2568 tokens:' line - into"
    " logs/state-log-archive-2026-11.md while leaving that round FOLD SUMMARY"
    " live at index 0, and NARRATIVE_RE matched 'R2568 fold of log lines ...'"
    " as a round narrative even though the module kind table calls fold lines"
    " other. REPAIRED IN ITS BIRTH SITE ALONE in commit b80cf890 before any"
    " retry: src/os/ledger_lines.py now carries a word-bounded"
    " FOLD_SUMMARY_RE guard, with six criteria AC-FCLS1..AC-FCLS6 pinned in"
    " state/queue/tech.md BEFORE the code and a shipped suite"
    " src/os/test_ledger_fold_kind.py.",
    "2026-11-09 R2580 SECOND RED DISCLOSED RATHER THAN HIDDEN: the first retry"
    " after that repair was ALSO red, at 10 assertions"
    " (qa/reconcile-all-R2579-retry.log, 1048691B), because the registry had"
    " moved 619/4690 -> 620/4696 with the new suite while"
    " docs/sandbox-suite-matrix.md still described 619/4690 and the export"
    " face was stale - six text-coverage suites plus three export faces read"
    " the stale documents, exactly the birth site R2567 hit. Reordered and"
    " healed before the final leg: the matrix was regenerated stamp-aligned"
    " from the last green leg qa/reconcile-all-R2577.log to 61554B at 620/4696"
    " green=618/620 honest with --check byte-identical, the export was"
    " refreshed through src/os/export_R2580.py to 395254B at tick 2579 with"
    " check_export_consistency pass=21 fail=0, and both landed in commit"
    " cc456f89.",
    "2026-11-09 R2580 GREEN LEG on the repaired committed tree:"
    " qa/reconcile-all-R2579-retry2.log 1048514B, RUNNER PASS 620/620 suites,"
    " reconcile controls 7/7, 1530.0s, ZERO FAIL suite rows, 620 unique suite"
    " rows and an independent criteria recount over those rows summing to"
    " EXACTLY 4696. FOLLOW-UP in the designed order through the shipped"
    " callable: the dry run read SECTION matrix FAIL by design (doc 61554B"
    " against the new evidence, no byte written), then a stamp-aligned"
    " regeneration from THIS round own green leg to 61574B at 620/4696"
    " green=620/620, --check byte-identical, then all four sections PASS for"
    " VERDICT R2580 PASS failing=none APPENDED 1951B. DEBT AND BOARD:"
    " reconcile-battery-R2579 closed through the shipped debtor at its"
    " predicted and measured 184418B -> 184421B (line 329, open 33->32, done"
    " 279->280, readback ok), product-face-R2580 opened first=yes at 184421B"
    " -> 184652B naming tech line 626 prefix AC-LKND1; the AC-FCLS row was"
    " closed through src/os/queue_close_R2580.py at 1820642B with one row"
    " seeded from this window own measured limits (a date-prefixed fold"
    " summary and the 'folded' inflection both still read round and re-open"
    " the gap). PROOF of the shipped face:"
    " qa/ledger-fold-kind-R2580.log 1312B utf-8 LF crlf=0 nul=0, legs=2"
    " identical=True, adjacent=3 green, fails=0.",
    "2026-11-09 R2580 honest disclosures: (a) TWO product points on the"
    " Executive Protocol scale - a shipped guard with its own six-criteria"
    " suite and a bounded live reading of the real tree - but NOTHING a CEO"
    " could newly open and no P-47 business surface moved; (b) the real 19.9"
    " debit and the real msgSecCheck still wait on CEO physical items; (c)"
    " BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED"
    " shell (carried ceo-pending physical item loop-s4u-reconcile); (d) this"
    " round ran long (the battery alone is ~25 minutes and it had to run"
    " three times), stated plainly rather than dressed as progress.",
    "R2580 tokens: local=~34k api=0 api_reason=verification window - one"
    " five-silence scan with the decisions row count, the group orders tail"
    " and the ledger face actually read, one debt gate read naming the"
    " battery, one target re-measured by import at 619/4690, one red battery"
    " kept with its three failing suites, one birth site diagnosed by"
    " measurement of the live and archived log faces, six criteria"
    " pre-registered before the code, one repair shipped with its own suite"
    " and three suites re-run green alone, one second red kept and healed in"
    " the designed order, one matrix regenerated twice stamp-aligned with"
    " byte-identical checks, one green battery at 620/4696, four follow-up"
    " sections to VERDICT PASS, the debt and board rows moved through their"
    " shipped writers, and the state/export/heartbeat closeout; zero cloud"
    " calls and zero external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2580 VERIFICATION window" in text:
        raise SystemExit("already present")
    tail = "\n ]\n}"
    if text.count(tail) != 1:
        raise SystemExit("log tail anchor not unique")
    chunk = "".join(",\n  " + json.dumps(line, ensure_ascii=True)
                    for line in LINES)
    text = text.replace(tail, chunk + tail, 1)
    payload = json.loads(text)
    for line in LINES:
        assert line in payload["log"], "line missing after insert"
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("LOG appended=%d log=%d bytes=%d crlf=%d" % (
        len(LINES), len(payload["log"]), len(text.encode("utf-8")),
        text.count("\r")))
    return 0


if __name__ == "__main__":
    sys.exit(main())