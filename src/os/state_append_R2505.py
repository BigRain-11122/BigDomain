"""R2505 closeout: tick advance and this round's log lines.

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
    "2026-11-07 R2505 PRODUCT window on the tech head the register named (product-face-R2504, tech head state/queue/tech.md:542 prefix AC-PNLT1 patterns_non_label_text_readability, criteria AC-PNLT1..AC-PNLT6 pinned in that row at R2503 BEFORE any code). Five-silence scan at open was clean at HEAD 62f68212 (git status empty, no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the 85-token baseline at a measured 174 rows, group orders tail unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the seven-day gate). debt_gate read CLAIM-FIRST on product-face-R2504 and queue_head named tech line 542 prefix AC-PNLT1 with claimable=10, so this window shipped a product byte rather than another battery.",
    "2026-11-07 R2505 CLAIM AND SHIP: the R2502/R2503 gates ask patterns_label_readability.gate with patterns[labels] ONLY, while src/sandbox/suite_matrix.py::render interpolates header_note, labels.response_text, every table caption and every face label straight into docs/sandbox-suite-matrix.md - a doctored header_note carrying U+FFFD read publishable=True while the composed artifact really carried the broken codepoint (measured at R2503, qa/patterns-render-consumer-live-R2503.log). SHIPPED src/os/patterns_non_label_text_readability.py plus its suite, and render() now asks it one statement after the label seam. The coverage is DERIVED, not listed: the shipped render is composed once against a recording mapping that keeps every string it asks for, addressed by the field path that asked for it (header_note, labels.summary_cols[0], domains[0].faces[1].label, and fields read through .get such as labels.stamp_from), and that set goes to the SHIPPED per-codepoint law at CALL time - no second classifier exists here, and a key the render never reads is honestly not claimed as covered.",
    "2026-11-07 R2505 PROOF measured, not quoted: AC-PNLT1..AC-PNLT6 SUITE PASS 6/6 TWICE with an identical digest plus three adjacent readability/matrix suites green (qa/patterns-non-label-text-readability-R2505.log, 7967B, utf-8 LF, legs=2 identical=True fails=0 adjacent=3). The call-time ask is proved by patching PLR.gate and watching this face carry the stub code verbatim, and by feeding a doctored header_note to the REAL render. A suspect file refuses the shipped tool at exit 4 with 'FAIL non-label: E_PLR_SUSPECT field=header_note', the target keeps every byte it had, no residue is left, and --check reports the same refusal instead of the drift exit 2 - while a clean file renders byte-identically to the committed doc at 55964 bytes and --check stays at its today reading of exit 0. TWO OF MY OWN ASSERTIONS FAILED FIRST and were fixed as TEST defects rather than loosened: the call-time proof had to ask this face directly because the label seam refuses first on the same patched gate, and the byte-identity leg had to be measured AFTER the new registry row moved the artifact (55841B -> 55964B) instead of against the pre-move doc.",
    "2026-11-07 R2505 REGISTRY, MATRIX, BOARD AND DEBT: one runner row os-patterns-non-label-text-readability(6), so the registry reads 582 suites / 4468 criteria, recounted by importing reconcile_all.SUITES. docs/sandbox-suite-matrix.md was regenerated stamp-aligned from qa/reconcile-all-R2504.log to 55964B at 582 suites / 4468 criteria with --check byte-identical and its green line honestly reading 581/582. The claimed row 542 was closed through a per-round writer with its DISCHARGED note (predicted and measured 1655665B, readback ok) and ONE row was seeded from this window own live measurement: a registry suite label carrying U+FFFD renders into the artifact while the shipped gate still reads publishable=True, because that text comes from DISK rather than the patterns document (qa/patterns-non-label-live-R2505.log, 435B) - seeded as AC-ADTR1..AC-ADTR6 intent with the head now at line 544 and queue_floor reading claimable=10. product-face-R2504 closed through debt_close (137947B -> 137950B, open 2->1, done 205->206) and reconcile-battery-R2505 appended first=yes through debt_append (137950B -> 138541B), both readback ok.",
    "2026-11-07 R2505 honest disclosures: (a) the product increment is a runnable guard on the CEO-visible artifact rather than a new feature the CEO could open - the artifact it protects is docs/sandbox-suite-matrix.md, and the defect it prevents was carried by that document until today. (b) DISCLOSED LIMIT: deriving the read set means composing the real render once, so the probe patches PLR.gate to an allow-all stub and raises this module own re-entrancy flag for that single compose, restoring both in a finally block; a concurrent in-process caller could observe that window, which the single-process CLI and render path never do. (c) no battery ran this window by design (product face), and the register now owes reconcile-battery-R2505 at 582/4468 BEFORE any further product byte. (d) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed. (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); tasks.md was not touched, it is the P-47 canonical board.",
    "R2505 tokens: local=~22k api=0 api_reason=product window - one pre-registered face shipped with its six criteria, the render path wired to it one statement after the label seam, one suite proved twice with three adjacent suites green, two of my own assertions repaired as test defects, one registry row recounted by import, one matrix stamp-aligned regeneration checked byte-identical, one live reading plus one measured limit seeded, one queue row closed and one battery row opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
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
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    print("tick=%d loglen=%d last_decision_rows=%s bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]),
             state.get("last_decision_rows"), len(raw_after),
             raw_after.count(b"\r\n"),
             raw_after.count(b"\n") - raw_after.count(b"\r\n")))
    return 0 if (state["tick"] == tick
                 and len(state["log"]) == before + len(LINES)) else 1


if __name__ == "__main__":
    sys.exit(main())