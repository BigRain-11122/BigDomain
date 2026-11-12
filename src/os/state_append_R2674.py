"""R2674 verification window closeout: two honest log lines plus one tick.

Every number typed into the face line was measured in this window (the pid
chain, the evidence bytes with an independent criteria recount, the registry
by import, the three write-sensitive suites, the two follow-up passes and the
debt register readbacks) rather than copied from the register.

The indent is hard-coded at two spaces on purpose: state_io.ITEM_INDENT is 16
while this file own log items sit at 2, the template defect R2671 and R2673
both repaired by hand after the fact. This writer does not repeat it.
"""

import io
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
        "2026-11-12 R2674 VERIFICATION window ADOPTED the detached battery leg "
        "R2673 launched and CLOSED reconcile-battery-R2671 GREEN at the "
        "pre-registered 654 suites / 4900 criteria. MEASURED NOT QUOTED: the "
        "stream closed on RUNNER PASS (654/654 suites green, reconcile controls "
        "7/7, 3238.7s) and BATTERY rc=0 3241.0s after TMP RECLAIM 697/697 at "
        "241.16 MiB, and the pid chain (63200, 38276, 72800) was gone by "
        "command line before any byte was read. qa/reconcile-all-R2673.log read "
        "1104914B, utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 8663 lines, 654 "
        "suite rows carrying 654 UNIQUE names, 654 PASS and ZERO FAIL rows, "
        "ZERO non-zero exits, and an INDEPENDENT criteria recount summing to "
        "EXACTLY 4900; the registry was re-measured by import at 654 suites / "
        "654 unique names / 654 unique paths. R2614 DISCIPLINE HONOURED: "
        "because two closeout commits (7c6930d6, 80a0e9d1) landed UNDER the "
        "leg, the three export write-sensitive suites were re-run on the FINAL "
        "committed tree and read SUITE PASS 6/6, SUITE PASS 6/6 and SUMMARY "
        "pass=15 fail=0, with ledger_lines --check reading VERDICT CLEAN. "
        "FOLLOW-UP in the designed order: designed matrix FAIL first (on-disk "
        "67177B vs regenerated 67174B, NO byte written) while fingerprint read "
        "CLEAN domains=5, profile byte-identical and census DRIFT-CLEAN; then a "
        "stamp-aligned regeneration from THIS round own green leg to 67174B at "
        "654 rows reading DOC-CURRENT with --check byte-identical at rc=0, then "
        "four sections PASS for VERDICT R2673 PASS failing=none (APPENDED "
        "1951B, eol_ok=True). DEBT: reconcile-battery-R2671 closed 212438B -> "
        "212441B (line 393, open 45->44, done 330->331, readback ok) and "
        "product-face-R2674 opened first=yes 212441B -> 212772B naming the next "
        "window a PRODUCT face on queue head state/queue/tech.md:676 prefix "
        "AC-PNAG1 while claimable reads 14; NO successor battery is owed "
        "because this window moved no product src byte and the registry is "
        "unmoved at 654/4900. HONEST: zero product points, nothing a CEO could "
        "newly open, every P-47 item still waits on CEO physical pieces, and "
        "this window ran past its twenty-five minute budget because the leg "
        "itself measured 3238.7s.",
        "R2674 tokens: local=~7k api=0 api_reason=verification adoption window "
        "- one five-silence scan with the content-addressed decisions face, the "
        "group orders tail and the ledger face read, one debt gate read, one "
        "queue head read on the tech line, five bounded waits on the live pid "
        "and stream, one evidence byte measurement with an independent criteria "
        "recount, one registry re-measure by import, three write-sensitive "
        "suites re-run on the final committed tree, one ledger_lines --check, "
        "two follow-up passes with one stamp-aligned matrix regeneration and "
        "its --check, one debt close and one debt append with readback, and the "
        "state/export/heartbeat closeout; zero cloud calls and zero external "
        "API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2674_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d" %
          (tick + 1, after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
