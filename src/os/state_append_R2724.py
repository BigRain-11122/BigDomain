"""R2724 adoption closeout: the R2723 leg, its verdict, debt, one tick."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-14 R2724 VERIFICATION ADOPTION window that closed "
    "reconcile-battery-R2723 at its pre-registered 672 suites / 5008 criteria: "
    "the leg was launched at R2723 own launch window as pid 63108 on the "
    "committed tree c58ff81e and was ADOPTED by its evidence path "
    "qa/reconcile-all-R2723.log, never relaunched. Five readings at open, "
    "disclosed rather than smoothed: git status carried ONE modified file (the "
    "R2723 window own uncommitted board line in src/os/backlog.md) at HEAD "
    "100efb37 equal to origin/main with no index.lock; ZERO @BigDomain rows in "
    "the group ledger; the content-addressed decisions face read rows=120 "
    "tokens=66 new=0; the group orders tail is the 2026-11-14 01:3x BigStream "
    "seat row already carried as knowledge-only; benchmarks_refreshed "
    "2026-11-14 inside the seven-day gate. debt_gate read CLAIM-FIRST "
    "item=reconcile-battery-R2723, queue_head read tech line=695 prefix "
    "AC-EPDU1 claimable=13, queue_floor read FLOOR-MET 5/5 13/10 10/10.",
    "R2724 THE LEG WAS STILL RUNNING AT OPEN AND WAS WAITED ON RATHER THAN "
    "RE-FIRED: pid 63108 read ALIVE through a SYNCHRONIZE kernel probe "
    "(WaitForSingleObject returned the timeout state, a WMI child scan was "
    "unavailable on this host and was NOT read as a dead leg), the stream moved "
    "659 -> 662 PASS rows across six bounded polls with ZERO FAIL rows, then "
    "closed on BATTERY rc=0 and the evidence file appeared. THE GREEN WAS "
    "MEASURED ON BYTES: qa/reconcile-all-R2723.log reads 1218994B, utf-8, "
    "bom=False, crlf=0, lone_cr=0, nul=0, 10032 lines, 672 registered suite rows "
    "beginning PASS suite carrying 672 UNIQUE names with ZERO duplicates, ZERO "
    "rows beginning FAIL suite, every row exit=0, and an INDEPENDENT recount "
    "over their declared criteria summing to EXACTLY 5008, byte for byte the "
    "pre-registered target; the summary row reads PASS suites 672/672 green, "
    "overrides=1, and the leg closes on RUNNER PASS (672/672 suites green, "
    "reconcile controls 7/7, 6319.1s) with TMP RECLAIM removed=697 reclaimed "
    "241.16 MiB. A bare 'PASS suite' prefix match counts 673 lines because it "
    "also matches that summary row - named here so the next window does not "
    "read it as a 673rd suite.",
    "R2724 DESIGNED ORDER EXECUTED AND THE FIRST MEASUREMENT WAS THE DESIGNED "
    "FAIL: battery_followup --dry-run read SECTION matrix FAIL on-disk 71107B "
    "against regenerated 71127B with NO byte written, because the document "
    "still stamped the R2719 leg. suite_matrix_reconcile was then stamped from "
    "THIS window own green leg (--write --evidence qa/reconcile-all-R2723.log) "
    "to 71127 bytes at 672 rows and --check read DOC-CURRENT, after which the "
    "four pinned sections read matrix PASS byte-identical 71127B, fingerprint "
    "CLEAN domains=5, profile byte-identical PASS and census DRIFT-CLEAN for "
    "VERDICT reconcile-battery-R2723 PASS failing=none (APPENDED 1987B, "
    "eol_ok=True).",
    "R2724 DEBT AND BOARD THROUGH THE SHIPPED WRITERS: the pre-registered 672 "
    "suites / 5008 criteria was closed at its predicted and measured 232420B -> "
    "232423B (line 432, open 50->49, done 364->365, readback ok) and ONE "
    "product row was appended first=yes at 232423B -> 233595B as "
    "product-face-R2724 naming queue head state/queue/tech.md:695 prefix "
    "AC-EPDU1 with claimable 13 and criteria AC-EPDU1..AC-EPDU6 pinned there at "
    "R2723 BEFORE any code; debt_gate --check now reads CLAIM-FIRST "
    "item=product-face-R2724 first=1 and the queue faces are unchanged "
    "(line=695 claimable=13, FLOOR-MET 5/5 13/10 10/10). NO successor battery "
    "is owed because this window moved no product src byte, no registry row and "
    "no code: the registry is unmoved at 672 suites / 5008 criteria and the "
    "only bytes it added are the restamped matrix, the QA evidence, the board "
    "lines and this file.",
    "R2724 honest disclosures: (a) ZERO product points - a green 672-suite "
    "battery, a restamped matrix and a closed debt row are evidence, not "
    "something a CEO can newly open, and every P-47 business face still waits "
    "on CEO physical pieces (merchant id, mini-program appid/secret); (b) this "
    "round ran past its 25 minute budget because the leg needed about six "
    "minutes of bounded waiting plus the R2614 receipt; (c) the working tree "
    "was NOT clean at open - the R2723 launch window left its board line "
    "uncommitted and this window committed it rather than reporting an empty "
    "status; (d) tasks.md was not touched, it is the P-47 canonical board; (e) "
    "Docker is absent on this host; (f) BigDomain-OSLoop still reads "
    "InteractiveToken and needs an ELEVATED shell for its S4U re-registration "
    "(carried ceo-pending physical item loop-s4u-reconcile).",
    "R2724 tokens: local=~8k api=0 api_reason=verification adoption window - "
    "one five-silence scan with the debt gate, the queue head and queue floor, "
    "one kernel liveness probe plus six bounded progress reads on a live leg, "
    "one byte-level measurement with an independent criteria recount of 5008, "
    "one designed matrix FAIL then one stamp-aligned regeneration checked "
    "DOC-CURRENT, one four-section verdict append, one debt close and one debt "
    "append with readback, one board repair for a lagged line, one "
    "write-sensitive receipt over fifteen suites, and the state/export/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2724p_")
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
