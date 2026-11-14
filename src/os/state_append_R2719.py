"""R2719 verification closeout: adopted leg, verdict, board, debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2719 VERIFICATION ADOPTION window that closed "
    "reconcile-battery-R2718 at its pre-registered 670 suites / 4996 criteria: the leg "
    "was launched at R2719 own launch window as pid 28044 on the committed tree "
    "e2b50b2b and was ADOPTED by its evidence path qa/reconcile-all-R2719.log, never "
    "relaunched. Five readings at open: git status EMPTY at HEAD 02a9e94f equal to "
    "origin/main with no index.lock; ZERO @BigDomain rows new in the group ledger; the "
    "content-addressed decisions face read no new token; the group orders tail is the "
    "2026-11-14 01:3x BigStream seat row already carried as knowledge-only; "
    "benchmarks_refreshed 2026-11-14 inside the seven-day gate.",
    "R2719 THE LEG LOOKED STALLED TWICE AND BOTH TIMES THE PROCESS TABLE SETTLED IT "
    "rather than a guess: at 331 suites the stream sat still for seven minutes, and "
    "rather than call that a hang a kernel liveness probe read pid 28044 ALIVE "
    "(WaitForSingleObject returned the timeout state), the child reconcile_all.py was "
    "named as pid 55692 under that parent, and the stream was found to have grown from "
    "18201B to 584910B while the counter lagged - the suite in flight was writing child "
    "output between PASS rows. A WMI process scan had returned NOTHING for the same "
    "pid, which is a measurement artefact on this host and is named here so the next "
    "window does not read an empty CommandLine list as a dead leg.",
    "R2719 THE GREEN WAS MEASURED ON BYTES: qa/reconcile-all-R2719.log reads 1206663B, "
    "utf-8, bom=False, crlf=0, lone_cr=0, nul=0, 9874 lines, 670 rows beginning PASS "
    "suite carrying 670 UNIQUE names with ZERO duplicates, ZERO rows beginning FAIL "
    "suite, ZERO rows whose exit is non-zero and ZERO rows without a criteria field, and "
    "an INDEPENDENT recount over their declared criteria summing to EXACTLY 4996, byte "
    "for byte the pre-registered target; the stream closes on RUNNER PASS (670/670 "
    "suites green, reconcile controls 7/7, 3851.9s) and BATTERY rc=0 3852.1s.",
    "R2719 DESIGNED ORDER EXECUTED AND THE FIRST MEASUREMENT WAS THE DESIGNED FAIL: "
    "battery_followup --dry-run read SECTION matrix FAIL on-disk 70872B against "
    "regenerated 70866B with NO byte written, because the document still stamped the "
    "R2717 leg. suite_matrix_reconcile was then stamped from THIS window own green leg "
    "(--write --evidence qa/reconcile-all-R2719.log) to 70866 bytes at 670 rows and "
    "--check read DOC-CURRENT, after which the four pinned sections read matrix PASS "
    "byte-identical 70866B, fingerprint CLEAN domains=5, profile byte-identical PASS and "
    "census DRIFT-CLEAN for VERDICT reconcile-battery-R2718 PASS failing=none "
    "(APPENDED 1987B, eol_ok=True).",
    "R2719 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: reconcile-battery-R2718 was "
    "closed at its predicted and measured 229131B -> 229134B (line 426, open 48->47, "
    "done 360->361, readback ok) and one product row was appended first=yes at 229134B "
    "-> 229691B naming queue head state/queue/tech.md line 693 prefix AC-ECMP1 with "
    "claimable 13 and criteria AC-ECMP1..AC-ECMP6 pinned there at R2718 BEFORE any code; "
    "debt_gate --check now reads CLAIM-FIRST item=product-face-R2719 first=1. NO "
    "successor battery is owed because this window moved no product src byte, no "
    "registry row and no code: the registry is unmoved at 670 suites / 4996 criteria and "
    "the only bytes it added are the restamped matrix, the QA evidence and this file.",
    "R2719 honest disclosures: (a) ZERO product points - a green 670-suite battery, a "
    "restamped matrix and a closed debt row are evidence, not something a CEO can newly "
    "open, and every P-47 business face still waits on CEO physical pieces (merchant id, "
    "mini-program appid/secret); (b) this round ran about 70 minutes past its 25 minute "
    "budget on purpose: the leg measures 3852 seconds here and adopting it by "
    "measurement, restamping, appending a verdict and closing debt is the whole face; "
    "(c) the empty WMI CommandLine list at 331 suites was a measurement artefact, not a "
    "dead leg, and the kernel probe plus the child pid are what settled it; (d) tasks.md "
    "was not touched, it is the P-47 canonical board; (e) Docker is absent on this host; "
    "(f) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for "
    "its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2719 tokens: local=~6k api=0 api_reason=verification adoption window - one "
    "five-silence scan with the debt gate and the queue face, one kernel liveness probe "
    "plus one child-pid read in place of calling a slow leg a hang, about ten bounded "
    "progress readings across a 3852-second leg, one byte measurement with an "
    "independent criteria recount of 4996, one designed matrix FAIL then one "
    "stamp-aligned regeneration checked DOC-CURRENT, one four-section verdict append, "
    "one debt close and one debt append with readback, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + LINES
    expected["tick"] = tick + 1

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    bumped = []
    old_tick = '"tick": %d' % tick
    new_tick = '"tick": %d' % (tick + 1)
    seen = 0
    for row in doc_lines:
        if row.strip().rstrip(",") == old_tick and not seen:
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2719v_")
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
