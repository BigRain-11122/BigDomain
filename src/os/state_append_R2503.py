"""R2503 closeout: tick advance, this round's log lines, decision baseline.

Writes once through the same in-place law the earlier appenders use: the file
is CRLF with the log array at sixteen spaces, so the new lines are inserted as
JSON-escaped rows before the closing bracket and the tick plus the decision row
count are moved with anchored substitutions that must each hit exactly once.
"""

import io
import json
import re
import sys

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2503 PRODUCT window on the tech head the register named (state/queue/tech.md:540 prefix AC-PLRC1 patterns_label_readability_render_consumer, criteria AC-PLRC1..AC-PLRC6 pinned in that row at R2502 BEFORE any code). Five-silence scan at open was clean at HEAD a265bfab (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the 85-token baseline at a measured 174 rows, group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read OPEN-NONE (open=1, first=0, the carried loop-s4u-reconcile row) and queue_head named tech line 540 prefix AC-PLRC1 with claimable=10, so this window shipped a product byte rather than another battery.",
    "2026-11-07 R2503 CLAIM AND SHIP: R2502 shipped a readability gate but it protected only callers that CHOSE patterns_label_readability.publish(), while src/sandbox/suite_matrix.py::load_patterns read the patterns file with json.load and render() interpolated every label straight into docs/sandbox-suite-matrix.md - so the shipped operator command still published an unreadable label into the CEO-visible artifact. SHIPPED src/os/patterns_label_readability_render_consumer.py plus its suite, and suite_matrix.render() now asks that seam as its FIRST statement. The consumer holds no classifier of its own: guard() asks patterns_label_readability.gate at CALL time and carries its verdict and its own code verbatim, so no second opinion about a readable label can grow on the render path.",
    "2026-11-07 R2503 PROOF measured, not quoted: AC-PLRC1..AC-PLRC6 SUITE PASS 6/6 TWICE with an identical digest plus three adjacent suites green (qa/patterns-render-consumer-R2503.log, 5855B, utf-8 LF, legs=2 identical=True fails=0 adjacent=3). The call-time ask is proved by patching PLR.gate and watching the REAL SM.render refuse with the gate own code and the refused label key. A suspect patterns file refuses the shipped tool at exit 4 with 'FAIL readability: E_PLR_SUSPECT label=title', the target keeps every byte it had, no .tmp/.part/.parity-stage residue is left, and --check reports the same refusal as readability rather than as the drift exit 2 - while a clean file keeps --check on its today reading of exit 0 and renders byte-identically to the committed doc at 55846 bytes. TWO OF MY OWN ASSERTIONS FAILED FIRST and were fixed as TEST defects rather than loosened: the wired-row string had to match the registry's real two-line shape, and the label check had to compare the shipped labels against their own earlier reading instead of assuming every value is a string.",
    "2026-11-07 R2503 REGISTRY, MATRIX AND ONE MEASURED GAP: one runner row os-patterns-label-readability-render-consumer(6), so the registry reads 581 suites / 4462 criteria, recounted by importing reconcile_all.SUITES. The row moved the artifact, so docs/sandbox-suite-matrix.md was regenerated stamp-aligned from qa/reconcile-all-R2502.log to 55846B at 581 suites / 4462 criteria with --check byte-identical and its green line honestly reading 580/581. The claimed row 540 was closed through a per-round writer with its DISCHARGED note (predicted and measured 1651475B, readback ok) and ONE row was seeded from this window own live measurement: patterns_label_readability.gate is asked with patterns[labels] ONLY while render() interpolates header_note, response_text and every caption, so a doctored header_note carrying U+FFFD read publishable=True while the composed document really carried the broken codepoint (qa/patterns-render-consumer-live-R2503.log, 405B) - seeded as AC-PNLT1..AC-PNLT6, and queue_floor then read FLOOR-MET 5/5 10/10 10/10 with the new head at line 542.",
    "R2503 tokens: local=~24k api=0 api_reason=product window - one pre-registered face shipped with its six criteria, one render path wired to the shipped gate at call time, one suite proved twice with three adjacent suites green, two of my own assertions repaired as test defects, one registry row recounted by import, one matrix stamp-aligned regeneration checked byte-identical, one live reading plus one measured limit seeded, one queue row closed and one battery row opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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