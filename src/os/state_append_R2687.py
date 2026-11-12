"""R2687 continuation closeout: honest log lines plus one tick.

Every number below was measured in this window (the five-silence scan, the debt
gate, the queue head and floor, the registry by import on four axes, the red leg
bytes, the birth-site repair at HEAD, the four bounded polls of the retry leg and
the three-suite write-sensitive re-run) rather than copied from the register.

The indent is hard-coded at two spaces on purpose: state_io.ITEM_INDENT is 16
while this file own log items sit at 2.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
INDENT = 2


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "2026-11-13 R2687 VERIFICATION window CONTINUING the R2686 round on the "
        "battery the debt gate names first (reconcile-battery-R2685, "
        "pre-registered 659 suites / 4930 criteria at R2685). Five readings at "
        "open, all clean: git status EMPTY at HEAD fd5857d7 equal to origin/main "
        "with no index.lock; ZERO unreplied @BigDomain rows (atbd_lines=0); the "
        "content-addressed decisions scan read 70 distinct D/C/T/B/F/P/O/XL "
        "tokens against the stored 256-token baseline with new=0; the group "
        "orders head still the 2026-11-12 12:45 row already carried as "
        "last_order and judged knowledge-only for this company; "
        "benchmarks_refreshed 2026-11-10 sitting three days inside the seven-day "
        "gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2685 "
        "opened=R2685 carried=2 open=45 first=1, queue_head read tech line=681 "
        "prefix=AC-PNAO1 claimable=14 and queue_floor read FLOOR-MET 5/5, "
        "14/10, 10/10, and the registry was re-measured BY IMPORT at 659 suites "
        "/ 4930 criteria / 659 unique names / 659 unique paths, byte for byte "
        "the pre-registered number.",
        "R2687 THE R2686 LEG FINISHED RED AND IS KEPT AS EVIDENCE RATHER THAN "
        "DRESSED UP: logs/battery-R2686.stream closed at 1135520B on RUNNER FAIL "
        "(4 failed assertions) with BATTERY rc=1 3037.2s after TMP RECLAIM "
        "697/697 at 241.16 MiB, and qa/reconcile-all-R2686.log was measured on "
        "bytes - 1126905B, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 8885 "
        "lines, 656 PASS suite rows carrying 656 UNIQUE names and no duplicate "
        "names, THREE red suite rows (os-suite-matrix-reconcile-evidence-face "
        "AC-EDMB3, os-matrix-stamp-compare AC-MSC4, os-stamp-text-coverage "
        "AC-STPT4) plus the runner own summary row, and an INDEPENDENT criteria "
        "recount over the 656 PASS plus 3 FAIL suite rows summing to EXACTLY "
        "4930 - so the walk covered all 659 registered suites and the reds are "
        "content rather than a short walk.",
        "R2687 THE CAUSE WAS READ OFF THE SHIPPED FACES AND NOT GUESSED, AND THE "
        "BIRTH-SITE REPAIR HAD ALREADY LANDED AS fd5857d7 BEFORE THIS WINDOW "
        "OPENED: AC-STPT4 compares the doc own stamp and borrow against the "
        "module source, so with the borrow line MISSING from "
        "docs/sandbox-suite-matrix.md the recorded source read None whose str() "
        "is 'None' and 'None' lives all over that module; AC-MSC4 measured "
        "check=0 live='FAIL' agrees=False, i.e. the shipped --check read "
        "DOC-CURRENT while a fresh composition of the same document differed. "
        "The R2685 regeneration had composed WITHOUT --stamp-from and dropped "
        "the borrow line, and fd5857d7 restored it at 69502 -> 69560 bytes. "
        "MEASURED AT HEAD THIS WINDOW: the doc reads 69560B carrying '--stamp-from "
        "docs/sandbox-suite-matrix.md', suite_matrix.py --check reads "
        "byte-identical at 69560 bytes / 659 suites / 4930 criteria, and the "
        "three red suites re-ran individually at rc_failures=0 "
        "(qa/write-sensitive-R2687.log, 496B, utf-8, bom=False, crlf=0) reading "
        "SUITE PASS 6/6, SUITE PASS 6/6 and SUITE PASS exit=0 pass-lines=6 "
        "fail-lines=0 criteria=6.",
        "R2687 THE RETRY LEG IS LIVE AT CLOSEOUT AND NO VERDICT IS CLAIMED: "
        "logs/battery-R2686-retry.pid was written 05:41:15 and pid 75488 "
        "(battery_stream.py) with its reconcile_all child 89156 were confirmed "
        "live by command line, streaming to qa/reconcile-all-R2686-retry.log. "
        "MEASURED at three bounded polls: 05:46 386852B / 191 PASS suite rows / "
        "0 FAIL, 05:47 503162B / 263 PASS / 0 FAIL, and 05:49 561654B / 320 "
        "PASS / 0 FAIL, with NO RUNNER and NO BATTERY closing line at any of "
        "them. A full leg has measured 1600-4100s in this repository against "
        "this window 25-minute budget, so reconcile-battery-R2685 STAYS OPEN at "
        "its registered 659 suites / 4930 criteria and the next window ADOPTS "
        "this leg by its evidence path qa/reconcile-all-R2686-retry.log (the "
        "R2671/R2673/R2674/R2676/R2680/R2683/R2684/R2686 precedent) rather than "
        "a green claim this window cannot make.",
        "R2687 honest disclosures: (a) ZERO product points - no product byte "
        "moved and nothing a CEO could newly open exists, because the R2168 "
        "mixed-tree rule keeps product bytes shut until this battery is green, "
        "and every P-47 business face still waits on CEO physical pieces "
        "(merchant id, mini-program appid/secret); (b) this window CONTINUES "
        "the R2686 round after the birth-site repair commit fd5857d7, so the "
        "retry leg runs on a repaired committed tree rather than a fresh "
        "launch; (c) the three reds were NOT reproducible individually at HEAD "
        "and that is a measurement rather than a dismissal - the red leg keeps "
        "them byte for byte in git; (d) the one-off runner "
        "tmp/write_sensitive_R2687.py is DELETED before the commit rather than "
        "staged; (e) Docker is absent on this host; (f) tasks.md was not "
        "touched, it is the P-47 canonical board, and the backlog board top "
        "line still names the R2685 product face that R2685 already discharged "
        "- carried untouched rather than hand-closed, as R2686 also carried it; "
        "(g) BigDomain-OSLoop still reads InteractiveToken and needs an "
        "ELEVATED shell for its S4U re-registration (carried ceo-pending "
        "physical item loop-s4u-reconcile); (h) this window closeout commits "
        "land UNDER the retry leg, so the adopting window owes the R2614 "
        "write-sensitive re-run on the FINAL committed tree before it lands any "
        "verdict.",
        "R2687 tokens: local=~9k api=0 api_reason=verification continuation "
        "window - one five-silence scan with the content-addressed decisions "
        "face, the group orders head and the ledger face read, one debt gate "
        "read, one queue head plus one queue floor read, one red leg measured "
        "on bytes with an independent criteria recount, one registry target "
        "re-measured by import on four axes, one cause read off the shipped "
        "faces, one three-suite write-sensitive re-run landed as a single "
        "utf-8 LF evidence file, three bounded polls of the live retry leg, and "
        "the state/export/heartbeat closeout; zero cloud calls and zero "
        "external API touches",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    expected["tick"] = tick + 1
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * INDENT + json.dumps(item, ensure_ascii=False) +
                        suffix)
    bumped = []
    old_tick = '"tick": %d,' % tick
    new_tick = '"tick": %d,' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip() == old_tick and not seen:
            bumped.append(row.replace(old_tick, new_tick))
            seen += 1
        else:
            bumped.append(row)
    if seen != 1:
        print("REFUSED tick line not found exactly once")
        return 3
    out = state_io.EOL.join(bumped[:end] + inserted + bumped[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    if "--dry" in sys.argv:
        print("DRY run, nothing written")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2687_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d items_off_indent=%d" %
          (tick + 1, after["bytes"], after["log_len"],
           after["items_off_indent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
