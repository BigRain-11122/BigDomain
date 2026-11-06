"""R2504 closeout: tick advance and this round's log lines.

Writes once through the same in-place law the earlier appenders use: the file
is CRLF with the log array at sixteen spaces, so the new lines are inserted as
JSON-escaped rows before the closing bracket and the tick is moved with an
anchored substitution that must hit exactly once.
"""

import io
import json
import re
import sys

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2504 VERIFICATION window on the battery the register owed (reconcile-battery-R2503, opened by the R2503 product window as first=no). Five-silence scan at open was clean at HEAD 6831036c (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over an 85-token baseline at a measured 174 rows, group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read OPEN-NONE (open=2, first=0), but the open row own note names the R2168 mixed-tree rule, so the battery was claimed BEFORE any product byte; queue_head still names tech line 542 prefix AC-PNLT1 claimable=10 and that face is carried to the next window rather than started here.",
    "2026-11-07 R2504 TARGET RE-MEASURED BY IMPORT before the run: reconcile_all.SUITES reads 581 suites and 4462 criteria, byte for byte the number the register pinned at R2503. BATTERY GREEN ON THE FIRST LEG, MEASURED NOT QUOTED: qa/reconcile-all-R2504.log written by the shipped single writer src/os/battery_stream.py launched CREATE_NO_WINDOW detached (pid 50276 in logs/battery-R2504.pid, progress streamed to logs/battery-R2504.diag.log) reads 881783B after the follow-up append, utf-8, bom=False, crlf=0, lone_cr=0, closing line 'RUNNER PASS (581/581 suites green, reconcile controls 7/7, 1105.7s)', zero FAIL suite rows, and an independent recount over the 581 PASS suite rows sums criteria to exactly 4462. Birth-site tmp reclaim read candidates=932 removed=932 busy=0 failed=0 at 326.59 MiB. No red leg exists for this round because none was produced, stated rather than implied.",
    "2026-11-07 R2504 FOUR FOLLOW-UP SECTIONS through the shipped src/os/battery_followup.py, all PASS in the designed order: matrix byte-identical 55841B (docs/sandbox-suite-matrix.md regenerated stamp-aligned from THIS round own evidence, green=581/581, --check byte-identical at 581 suites / 4462 criteria), fingerprint CLEAN over 5 domains, profile byte-identical, census DRIFT-CLEAN. write_sections appended 1950B through the single writer and read eol_ok=True with the closing line 'VERDICT R2504: PASS eol crlf=0 bare_cr=0 bom=False', so the matrix the CEO might open names the battery that actually passed rather than a borrowed older leg.",
    "2026-11-07 R2504 DEBT settled through the shipped writers: reconcile-battery-R2503 closed at line 224 (open 2->1, done 204->205, predicted 137073B -> 137077B and measured exactly, readback ok) and product-face-R2504 appended first=yes through debt_append (predicted 137077B -> 137947B, measured exactly, readback ok) naming the next window a PRODUCT face on the tech head state/queue/tech.md:542 prefix AC-PNLT1 patterns_non_label_text_readability, whose criteria AC-PNLT1..AC-PNLT6 were pinned there at R2503 BEFORE any code. No successor battery is registered: this window changed only qa/, docs/ and state/, no registry module and no suite, so the registry stands unmoved at 581 suites / 4462 criteria.",
    "2026-11-07 R2504 BIRTH-SITE REPAIR DISCLOSED: state.json carried two lone-LF lines (the token-array tail) against 187 CRLF lines, so the shipped fold writer REFUSED with E_DWPP_MIXED rather than choosing a transport for lines it was not asked about - the refusal was obeyed, not loosened. src/os/repair_state_eol_R2504.py rewrote ONLY those two terminators (bytes 78001 -> 78003, crlf 187 -> 189, lf_only 0, every value and position kept) and the fold then ran at a true round-block boundary window 1..87 (the whole R2495..R2502 blocks), 78003B -> 10759B with predicted==actual, 370 tokens carried and none missing, round_split None, and state_fold --check read FOLD-CLEAR at margin 67741B.",
    "2026-11-07 R2504 honest disclosures: (a) this is an INTERNAL verification face - zero points on the Executive Protocol scale and nothing a CEO could open was built; what it buys is that the tree R2503 shipped is proved green end to end rather than assumed. (b) the window overshot its 25-minute budget because the battery alone runs about 1106s plus four follow-up sections, and that is disclosed rather than dressed up. (c) one host shell poll was cancelled by the watchdog while the battery kept running; the pid was re-read and confirmed alive before the green was accepted, so nothing is claimed from an interrupted process. (d) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board.",
    "R2504 tokens: local=~12k api=0 api_reason=verification window - one pre-registered battery re-measured by import before the run, one green first leg at 581/581 with exactly 4462 criteria recounted independently, four follow-up sections PASS with the matrix regenerated stamp-aligned and checked byte-identical, one debt row closed and the successor opened through their shipped writers, one refused fold obeyed and repaired at its birth site, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL state tail %r" % text[-30:])
        return 2
    tick_hits = re.findall(r'^\{\r\n  "tick": (\d+),', text)
    if len(tick_hits) != 1:
        print("FAIL tick anchor hits=%d" % len(tick_hits))
        return 2
    tick = int(tick_hits[0]) + 1
    text = text.replace('{\r\n  "tick": %d,' % int(tick_hits[0]),
                        '{\r\n  "tick": %d,' % tick, 1)
    rows = re.findall(r'\r\n  "last_decision_rows": (\d+),', text)
    if len(rows) != 1:
        print("FAIL last_decision_rows anchor hits=%d" % len(rows))
        return 2
    text = text.replace('"last_decision_rows": %s,' % rows[0],
                        '"last_decision_rows": 174,', 1)
    before = len(json.loads(io.open(P, encoding="utf-8").read())["log"])
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    state = json.loads(io.open(P, encoding="utf-8").read())
    print("tick=%d loglen=%d last_decision_rows=%s bytes=%d"
          % (state["tick"], len(state["log"]), state.get("last_decision_rows"),
             len(text.encode("utf-8"))))
    return 0 if (state["tick"] == tick
                 and len(state["log"]) == before + len(LINES)) else 1


if __name__ == "__main__":
    sys.exit(main())