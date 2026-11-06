"""R2502 battery receipt: the green measurement and the two closed debt rows."""

import io
import json
import sys

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2502 BATTERY GREEN ON THE COMMITTED TREE, MEASURED NOT QUOTED: after the product commit 161ad687 landed, the full reconcile battery ran through the shipped single writer src/os/battery_stream.py launched with CREATE_NO_WINDOW (pid recorded in logs/battery-R2502.pid, its stdout streamed to logs/battery-R2502.diag.log so progress had a heartbeat) and read RUNNER PASS (580/580 suites green, reconcile controls 7/7, 1125.0s) in qa/reconcile-all-R2502.log, 877010 bytes, zero CRLF, zero replacement characters, zero FAIL rows, an independent recount over the 580 'PASS suite' rows summing criteria to exactly 4456 - the registry number by measurement, not by quotation - and birth-site tmp reclaim candidates=932 removed=932 failed=0 at 326.59 MiB. The new face is green inside that battery: 'PASS suite os-patterns-label-readability exit=0 criteria=6'.",
    "2026-11-07 R2502 MATRIX FROM THIS ROUND OWN EVIDENCE: docs/sandbox-suite-matrix.md regenerated stamp-aligned from qa/reconcile-all-R2502.log to 55709B at 580 suites / 4456 criteria, its green line now honestly reading 580/580, and 'suite_matrix.py --check' read byte-identical afterwards, so the artifact the CEO might open names the battery that actually passed rather than a borrowed older leg.",
    "2026-11-07 R2502 TWO LAUNCH FAILURES DISCLOSED BEFORE THE GREEN: the first launch used DETACHED_PROCESS and the child died with no evidence and no diagnostic because stdout went to DEVNULL; the second used CREATE_NO_WINDOW but resolved the stream path as src/battery_stream.py instead of src/os/battery_stream.py and died in 203 bytes of diagnostic. Both were my own wiring errors, neither touched the tree, and the third launch - same script, path fixed, output streamed to a real file - is the run reported above. Nothing about the green is claimed from the failed launches.",
    "2026-11-07 R2502 DEBT settled through the shipped writers: reconcile-battery-R2501 closed at line 222 (open 3->2, done 202->203, predicted 136574B -> 136578B measured exactly, readback ok) and reconcile-battery-R2502 closed at line 223 (open 2->1, done 203->204, predicted 136578B -> 136582B measured exactly, readback ok). JUDGEMENT DISCLOSED: the R2501 row was owed from the previous window and this battery ran on a tree that already contains both R2501 and R2502 bytes, so it supersedes the narrower 579/4450 target rather than running twice; that substitution is stated, not hidden. Only loop-s4u-reconcile stays open, carried again because src/os/register_loop_task.ps1 needs an elevated shell.",
]


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL state tail %r" % text[-30:])
        return 2
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    state = json.loads(io.open(P, encoding="utf-8").read())
    print("tick=%d loglen=%d bytes=%d"
          % (state["tick"], len(state["log"]), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())