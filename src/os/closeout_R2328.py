"""R2328 closeout: tick, five log items, canonical atomic write.

The fold ran first (fold 620, commit 16d98ccd) because state.json stood at
78496B against the 78500B gate, and the two rounds the folds exposed as
residue (R2312, R2314) were carried as DELIVERED by name before any battery.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
TICK = 2328

ITEMS = [
    "2026-11-01 R2328 verification window (five-silence scan clean at open: "
    "empty git status --short and no index.lock; the content-addressed diff of "
    "the group decisions.md against the stored baseline read NEW=0 over 59 "
    "live tokens, so no decision row was owed; the evolution ledger carries no "
    "@BigDomain row and the group orders tail is unchanged at the 2026-11-01 "
    "10:4x baseline R2321 already acked by number as non-execution; benchmarks "
    "refreshed 2026-11-01 inside the seven-day gate). FOLD FIRST because "
    "state.json measured 78496B against the 78500B gate (4B margin): fold 620 "
    "moved log lines 2..12 - three older fold markers plus the whole R2314 and "
    "R2315 round blocks - verbatim into logs/state-log-archive-2026-11.md "
    "(182784B -> 194390B, prefix intact, 45 window tokens covered), predicted "
    "67340B equal to measured 67340B, margin 11160B, committed alone as "
    "16d98ccd. The fold exposed R2312 and R2314 as live residue with no triage "
    "entry (the known fold-creates-residue law, first measured at R2311), and "
    "both were spliced into state/residue_triage.json BY NAME as DELIVERED off "
    "the live stamp table (tech.md:374 and tech.md:375 both read closed=yes), "
    "192 -> 194 entries, 34316B -> 35027B with the predicted delta equal to the "
    "write, read-back proof, no temp residue; the declaration now reads "
    "untriaged=0 verdict=TRIAGED. BATTERY on the committed tree: the FIRST RUN "
    "WAS RED, 467/471 suites with 5 failed assertions in the ledger family "
    "(AC-LGR8, AC-LGA7, AC-LGA8, AC-LGB8, AC-LGN8) in 853.5s, kept as the red "
    "leg at qa/reconcile-all-R2328.log (788640B). ROOT CAUSE measured, not "
    "guessed: the R2327 closeout had written its round ledger item as "
    "'tokens: local=1 api=0 ...' without its round prefix, so the pinned "
    "'^R<n> tokens:' law could not see it and ledger_lines read "
    "rounds_without_ledger=2327 VERDICT DIRTY - the exact R2288 class. REPAIR "
    "AT THE BIRTH SITE, committed alone as 2efd5533: src/os/splice_R2328_ledger.py "
    "inserts the six bytes 'R2327 ' as RAW TEXT inside that one JSON string so "
    "every other byte of the 67KB declaration stays identical (no "
    "reserialisation), 67340B -> 67346B, JSON parsed on both sides, one changed "
    "item proved, read-back ok; ledger_lines then read ledger=12 "
    "round=37 other=2 rounds_without_ledger=none ledger_without_round=none "
    "VERDICT CLEAN and all four ledger suites re-ran 8/8 green. GREEN RETRY on "
    "the committed repair tree: RUNNER PASS 471/471 suites plus controls 7/7 in "
    "827.1s with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2328-retry.log, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3802 "
    "- EXACTLY the pre-registered target of +1 suite / +6 criteria against "
    "R2326 (470/3796), so the prediction matched the measurement with no "
    "correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=45098B regenerated=45205B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 471 suites / 3802 criteria (45205B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --daily --check byte-identical, census DRIFT-CLEAN), "
    "closing VERDICT R2328 PASS.",
    "R2328 tokens: local=~20k api=0 api_reason=verification window that "
    "inherited a deferred battery - one waterline fold with its archive append "
    "and read-back proof, one two-round residue splice by name, two full "
    "reconcile batteries (the red leg and the green retry on the committed "
    "repair tree), one birth-site ledger repair as a six-byte raw-text splice, "
    "four ledger suite re-runs, one four-section follow-up twice plus one "
    "matrix regeneration, and the debt/state/export/heartbeat/board closeout; "
    "zero cloud calls and zero external API touches; the product face resumes "
    "at R2329",
    "R2328 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(ninetieth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",
    "R2328 honest disclosures: (a) this window shipped NO product code and "
    "scores 0 product points; the work it did was the battery the R2327 "
    "closeout deferred plus the fold the waterline demanded. (b) The red leg is "
    "kept and named rather than overwritten: 467/471 suites, 5 failed "
    "assertions, all in one family and all from ONE unprefixed word, which is "
    "why the family gates together. (c) The repair script's own read-back "
    "assertion was wrong (it compared the whole log item to the six-byte needle "
    "instead of asserting the prefix) and it raised E_SPLICE_READBACK AFTER a "
    "correct write; the assertion was corrected and the file re-read to prove "
    "the write, so the reported defect is this window's TEST, never the "
    "declaration. (d) The first battery launch was killed by the shell tool's "
    "five-minute silence guard because its output was piped through a buffering "
    "selector (the R2211 trap re-proven); an ownership check proved zero "
    "orphan runners and no evidence file before the unpiped re-launch, so "
    "nothing was lost and nothing is claimed from the dead run. (e) The window "
    "overran its 25-minute budget by the battery cost itself (853.5s red plus "
    "827.1s green), recorded honestly rather than trimmed. (f) tasks.md was "
    "left untouched: it is the P-47 canonical board and carries no row for a "
    "verification window, disclosed rather than silently skipped.",
]


def main():
    raw = io.open(STATE, encoding="utf-8", newline="").read()
    before = os.path.getsize(STATE)
    data = json.loads(raw)
    if data.get("tick") == TICK:
        raise SystemExit("E_R2328_ALREADY_CLOSED")
    data["tick"] = TICK
    data["log"].extend(ITEMS)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    canon = SIO.canon(text)
    predicted = len(canon.encode("utf-8"))
    print("state before=%dB predicted=%dB delta=%+d log_len=%d"
          % (before, predicted, predicted - before, len(data["log"])))
    tmp = STATE + ".tmp-r2328c"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(canon)
    written = os.path.getsize(tmp)
    if written != predicted:
        os.remove(tmp)
        raise SystemExit("E_R2328_PREDICT %d != %d" % (written, predicted))
    os.replace(tmp, STATE)
    if os.path.exists(tmp):
        raise SystemExit("E_R2328_TEMP")
    back = json.loads(io.open(STATE, encoding="utf-8", newline="").read())
    if back["tick"] != TICK or len(back["log"]) != len(data["log"]):
        raise SystemExit("E_R2328_READBACK")
    measured = SIO.layout(io.open(STATE, encoding="utf-8", newline="").read())
    print("readback=%dB tick=%d log_len=%d layout_ok=%r"
          % (os.path.getsize(STATE), back["tick"], len(back["log"]),
             measured.get("layout_ok")))


if __name__ == "__main__":
    main()