"""R2609 verification-window closeout append: the owed battery, its red leg and the repair."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-10 R2609 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2608, pre-registered 639 suites / 4810 criteria at R2608 because that window moved product src bytes, one registry row and the matrix document). Five readings at open: git status carried exactly TWO untracked files from an INTERRUPTED ATTEMPT of this same round (qa/reconcile-all-R2608.log and src/os/launch_battery_R2608.py) with no battery, probe or capture process live by command line, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions scan unmoved against the stored baseline, the group orders tail unchanged at the 2026-11-09 00:59 BigStream row, benchmarks 2026-11-03 exactly seven days old and inside the gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2608 first=1 opened=R2608 stale=no open=39, queue_head named tech line 642 prefix AC-EDMF1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "2026-11-10 R2609 THE INTERRUPTED ATTEMPT LEG WAS ADOPTED AND RE-MEASURED, NOT RESTARTED, AND IT WAS RED: qa/reconcile-all-R2608.log measured 1088895 bytes, utf-8 with bom=False, crlf=0, lone_cr=0, nul=0, 8542 lines, 639 suite rows with exactly ONE non-zero exit, closing line 'FAIL suites 638/639 green, expected criteria total=4810, suite cap=600s overrides=1'. The single red suite was os-suite-matrix-reconcile-table-shape exit=1 (R2604 own suite), failing exactly one assertion - 'FAIL report says BOUND-REACHED on a capped pile (CEILING-STARVED)' - and 638 suites were green beside it, so this is one stale assertion rather than a product regression.",
    "2026-11-10 R2609 ROOT CAUSE READ OFF THE SHIPPED WORD, NOT GUESSED: R2608 renamed the starved walk to its own word CEILING-STARVED (src/os/suite_matrix_reconcile.py WORD_CEILING / CODE_CEILING via _walk_miss) and amended the assertion in its own R2606 shape suite only, leaving the pre-registered R2604 criterion_edmc3 still pinning verdict == WORD_RED with a bound_reached key that the shipped report no longer returns - a rename that swept one dependent suite and missed another. REPAIRED AT ITS BIRTH SITE: that one assertion now asks for the shipped word, the shipped code, the ceiling it declares and a bounded walk, and still REFUSES the old answer (verdict != WORD_RED), so the law is unchanged and nothing was loosened; the repaired suite read SUITE PASS 6/6 at rc=0 alone. The red leg and the repair were committed ALONE as 602ff19f before any retry, so the retry runs on a committed tree.",
    "2026-11-10 R2609 THE RETRY IS LIVE AT CLOSEOUT AND IS DISCLOSED RATHER THAN DRESSED UP AS GREEN: a one-off launcher (deleted before the commit, never staged) refused on a moved registry and Popen'ed src/os/battery_stream.py detached with CREATE_NO_WINDOW|DETACHED_PROCESS, its stream and pid in SEPARATE files under logs/ (battery-R2609.stream, battery-R2609.pid) so qa/ is written by the single writer alone, target re-measured by importing reconcile_all.SUITES at 639 suites / 4810 criteria. pid 54896 with its reconcile_all child were confirmed live by command line at open+45s. A full leg has measured 3500-4100s in this repository against this window 25-minute budget, so reconcile-battery-R2608 STAYS OPEN at its registered 639/4810 and the next window adopts this leg and closes the row (the R2601/R2607 precedent) instead of a green claim this window cannot make.",
    "R2609 honest disclosures: (a) ZERO product points on the Executive Protocol scale - no product byte was written, because the debt gate puts the owed battery before any further product work and that leg is still running, and nothing a CEO could newly open was built, so every P-47 item still waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) THE RED LEG WAS BORN IN THE PREVIOUS WINDOW OWN RENAME SWEEP - R2608 renamed a shipped verdict word and swept one dependent assertion instead of all of them, which is named here rather than smoothed; (c) the failing assertion was one of two that R2608 disclosed amending, so the sweep was reported as complete when it was not, and the battery is what caught it, which is the point of owing the battery; (d) the battery is NOT green and is NOT claimed green - the retry file does not exist yet at closeout; (e) TWO one-off launchers were deleted rather than staged (the interrupted attempt own launcher and this window own), because a single-use courier is not product; (f) the fold ran at a true round-block boundary (items 88..95, the complete R2608 block ending on its push line) with 12 tokens preserved verbatim before the append; (g) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed; (h) tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still needs an ELEVATED shell for its S4U re-registration (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2609 tokens: local=~11k api=0 api_reason=verification window - one five-silence scan with the decisions token scan, the group orders tail and the ledger face actually read, one debt gate plus queue head and floor read, one interrupted-attempt leg re-measured on its bytes, encoding, suite rows, failing suite and closing line rather than trusted, one root cause read off the shipped constants, one birth-site assertion repaired and re-run green alone, one red-leg plus repair commit, one detached retry launched on that committed tree with its liveness re-read, one fold at a true block boundary, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    for index in range(start):
        if lines[index].strip().startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            break
    else:
        print("REFUSED no tick line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2609_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
