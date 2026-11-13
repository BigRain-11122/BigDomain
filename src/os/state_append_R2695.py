"""R2695 verification adoption window closeout: measured log lines, one tick,
and the decisions baseline advanced by the five tokens judged knowledge-only.
Every number typed here was measured in this window rather than copied.
"""

import io  # noqa: F401
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"
NEW_TOKENS = [
    "B-20261028-1810",
    "B-20261105-003656",
    "B-20261107-180106",
    "B-20261108-000400",
    "B-20261108-120628",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    dec_rows = len(io.open(DEC, encoding="utf-8").read().splitlines())
    lines = [
        "2026-11-13 R2695 VERIFICATION window ADOPTING the R2693 leg and "
        "MEASURING ITS RED RATHER THAN DRESSING IT UP. Five readings at open, "
        "all clean: git status EMPTY at HEAD 85dc4e6b with no index.lock; ZERO "
        "@BigDomain rows in the group ledger (atbd_lines=0); the "
        "content-addressed decisions scan read file_tokens=77 against the "
        "stored 258-token union baseline with new=5, every one of them a B- "
        "prefix (B-20261028-1810, B-20261105-003656, B-20261107-180106, "
        "B-20261108-000400, B-20261108-120628) which are ledger round tokens "
        "carried inside prose, so all five are acknowledged by union with NO "
        "execution face for this company; the group orders tail max timestamp "
        "is still 2026-11-12 12:45, the bm-a station ONBOARD row already "
        "carried as last_order and judged knowledge-only; "
        "benchmarks_refreshed 2026-11-10 sitting three days inside the "
        "seven-day gate. debt_gate read CLAIM-FIRST "
        "item=reconcile-battery-R2692 opened=R2692 carried=3 stale=yes "
        "open=45 first=1, state_fold --check read FOLD-CLEAR at 70448B "
        "against the 78500B gate with margin 8052 and 64 live log lines, and "
        "the registry was re-measured BY IMPORT at 661 suites / 4942 criteria "
        "/ 661 unique names / 661 unique paths, byte for byte the "
        "pre-registered number.",

        "R2695 THE LEG WAS WATCHED AND NOT RELAUNCHED: at open pid 113988 "
        "carried child 114884 by command line, stream logs/battery-R2693.stream "
        "read 1107319B with 651 PASS suite rows and 1 FAIL suite row, and FOUR "
        "bounded polls read 652 pass at 1115432B, 653 at 1118588B, 655 at "
        "1125134B and finally the closing band at 1148249B with the BATTERY rc "
        "line, so a full leg measured 3966.4s here, above the 25-minute window "
        "budget exactly as the R2690/R2693 disclosures predicted. THE LEG "
        "FINISHED RED AND IS KEPT AS EVIDENCE: logs/battery-R2693.stream closed "
        "on TMP RECLAIM 697/697 at 241.16 MiB, 'RUNNER FAIL (2 failed "
        "assertions)' and 'BATTERY rc=1 3966.4s', and qa/reconcile-all-R2693.log "
        "was measured on bytes at adoption - 1139482B, bom=False, crlf=0, "
        "lone_cr=0, nul=0, 661 suite rows, 660 PASS and EXACTLY ONE FAIL, 661 "
        "UNIQUE names with no duplicate, and an INDEPENDENT criteria recount "
        "over their declared criteria fields summing to EXACTLY 4942 - so the "
        "walk covered all 661 registered suites and the red is content rather "
        "than a short walk. The runner's own 'FAIL suites 660/661 green, "
        "expected criteria total=4942' line is the second of its two failed "
        "assertions, which is the dialect that makes one red suite read as two "
        "failures; that is named here rather than left to look like a second "
        "defect.",

        "R2695 THE RED IS THE ALREADY-REPAIRED R2692 DEFECT AND NO NEW CAUSE WAS "
        "INVENTED: the single red row is 'FAIL suite os-state-io exit=1 "
        "pass-lines=7 fail-lines=1 criteria=8 1.6s', which is AC-SIO1, the "
        "regression born at R2692 when ITEM_INDENT was set to 2 against a suite "
        "whose drift sample was hardcoded to 2 and whose sample_text skipped "
        "re-indenting at that indent. That defect was repaired at its birth site "
        "in src/os/test_state_io.py and committed ALONE as bcb2c5f0 BEFORE this "
        "window opened, and the same suite re-ran at HEAD in this window reading "
        "'SUITE PASS 8/8 criteria=8' with AC-SIO8 green. The leg simply started "
        "at 08:40:29, before that repair landed, so it measured the pre-repair "
        "tree; no threshold was raised and no assertion was loosened to explain "
        "it away.",

        "R2695 THE SUCCESSOR LEG IS LIVE AT CLOSEOUT AND NO VERDICT IS CLAIMED: "
        "because the R2693 leg ran across a product src byte change, a battery "
        "on the REPAIRED COMMITTED tree is owed (the R2168 mixed-tree rule) and "
        "it was launched rather than promised - a one-off launcher in tmp/ "
        "refused on a moved target (any tuple other than 661/4942/661/661), an "
        "existing evidence file or an existing pid file, then Popen-ed "
        "src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS|"
        "CREATE_NEW_PROCESS_GROUP and put the stream and the pid in SEPARATE "
        "files under logs/ (battery-R2695.stream, battery-R2695.pid, pid 113432 "
        "with child 47944 confirmed live by command line), so "
        "qa/reconcile-all-R2695.log is written by the single utf-8 LF writer and "
        "never by a shell redirection. reconcile-battery-R2692 STAYS OPEN at its "
        "registered 661 suites / 4942 criteria and the next window ADOPTS this "
        "leg by its evidence path (the R2671/R2673/R2674/R2676/R2680/R2683/R2686 "
        "precedent) rather than relaunching, then owes the R2614 write-sensitive "
        "re-run on the FINAL committed tree before any verdict.",

        "R2695 honest disclosures: (a) ZERO product points - a red leg measured "
        "and a successor in flight are evidence, not something a CEO can newly "
        "open, and every P-47 business face still waits on CEO physical pieces "
        "(merchant id, mini-program appid/secret); (b) the red leg is COMMITTED "
        "as evidence rather than deleted, and the repair that closes it was "
        "committed in the PREVIOUS window, so this window claims no repair of "
        "its own; (c) the R2693 leg's 3966.4s runtime again overran the "
        "25-minute budget, disclosed rather than smoothed; (d) the one-off "
        "launcher in tmp/ is DELETED before the commit rather than staged; (e) "
        "Docker is absent on this host; (f) tasks.md was not touched, it is the "
        "P-47 canonical board; (g) BigDomain-OSLoop still reads InteractiveToken "
        "and needs an ELEVATED shell for its S4U re-registration (carried "
        "ceo-pending physical item loop-s4u-reconcile).",

        "R2695 tokens: local=~7k api=0 api_reason=verification adoption window - "
        "one five-silence scan with the content-addressed decisions face, the "
        "group orders tail and the ledger face read, one debt gate read, one "
        "fold gate read, four bounded battery polls with row counts, one "
        "evidence measurement on bytes with an independent criteria recount, "
        "one red cause read off the shipped suite at HEAD, one registry target "
        "re-measured by import on four axes, one successor launcher written "
        "outside the tracked tree and executed once, and the "
        "state/export/heartbeat closeout; zero cloud calls and zero external API "
        "touches",
    ]

    base = list(data.get("last_dec_tokens") or [])
    merged = base + [t for t in NEW_TOKENS if t not in base]

    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + lines
    expected["tick"] = tick + 1
    expected["last_dec_tokens"] = merged
    expected["last_decision_rows"] = dec_rows

    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)

    def set_field(rows, key, values, item_indent=2):
        head = ' "%s": [' % key
        try:
            first = next(i for i, r in enumerate(rows) if r.strip() == head.strip())
        except StopIteration:
            return None
        last = None
        for j in range(first + 1, len(rows)):
            if rows[j].strip() == "],":
                last = j
                break
        if last is None:
            return None
        block = []
        for index, value in enumerate(values):
            suffix = "," if index < len(values) - 1 else ""
            block.append(" " * item_indent + json.dumps(value) + suffix)
        return rows[: first + 1] + block + rows[last:]

    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
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
    rows = set_field(state_io._lf_lines(out), "last_dec_tokens", merged)
    if rows is None:
        print("REFUSED last_dec_tokens block not found")
        return 3
    replaced = 0
    for index, row in enumerate(rows):
        if row.strip().startswith('"last_decision_rows":'):
            rows[index] = ' "last_decision_rows": %d,' % dec_rows
            replaced += 1
    if replaced != 1:
        print("REFUSED last_decision_rows line not found exactly once")
        return 3
    out = state_io.EOL.join(rows)
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2695_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d dec_tokens=%d dec_rows=%d" %
          (tick + 1, after["bytes"], after["log_len"], len(merged), dec_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
