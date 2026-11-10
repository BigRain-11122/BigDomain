"""R2627 state append: four log lines, one tick and the order watermark.

The round owed the battery the debt gate named first and launched it
detached on the committed tree. Every line below carries a measured
number rather than a quoted one.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
NEW_ORDER = "2026-11-11 03:52"

LINES = [
    "2026-11-11 R2627 VERIFICATION window on the battery the debt gate named "
    "first (reconcile-battery-R2624, pre-registered 643 suites / 4834 "
    "criteria at R2624 because that window moved product src bytes and one "
    "registry row). Five readings at open: git status EMPTY at HEAD b771e395 "
    "equal to origin/main with no index.lock, ZERO @BigDomain rows in "
    "cph4/evolution-ledger.md (hits=0), the content-addressed D-/C- decisions "
    "scan read tokens=179 against the stored 225-token baseline with new=0, "
    "the group orders tail max_ts read 2026-11-11 03:52 which is byte-equal "
    "to the recorded watermark (an event-shift row carrying CEO-PROXY and "
    "PT-20261026 text, knowledge-only for this company, so no order moved), "
    "and benchmarks_refreshed 2026-11-10 sits inside the seven-day gate. "
    "debt_gate read CLAIM-FIRST item=reconcile-battery-R2624 opened=R2624 "
    "carried=3 stale=yes open=42 first=1; queue_head named tech line 653 "
    "prefix AC-EDMI1 claimable=15 and queue_floor read FLOOR-MET at 5/5, "
    "15/10, 10/10.",

    "2026-11-11 R2627 TARGET RE-MEASURED BY IMPORT BEFORE THE LAUNCH: "
    "reconcile_all.SUITES read 643 suites / 4834 criteria / 643 unique names "
    "/ 643 unique paths, byte for byte the registered number, so the "
    "pre-registration needed no move. The leg was launched DETACHED through a "
    "one-off refusing launcher src/os/launch_battery_R2627.py that exits 2 "
    "when the registry target has moved from 643/4834 and exits 3 when the "
    "evidence file already exists, Popen'ing src/os/battery_stream.py with "
    "CREATE_NO_WINDOW|DETACHED_PROCESS and putting the stream and the pid in "
    "SEPARATE files under logs/ (battery-R2627.stream, battery-R2627.pid) so "
    "qa/ is written by the single writer inside battery_stream and never by a "
    "shell redirection. pid 82760 with its reconcile_all child 82032 were "
    "confirmed live by command line at open+40s and again at closeout, the "
    "stream measuring 445991B at 6.2 minutes with 219 PASS suite rows and "
    "ZERO FAIL rows, then 331 PASS rows and ZERO FAIL rows at closeout with "
    "the evidence file not yet written because the run is still in its slow "
    "suite region (single rows measured 51.4s and 76.1s).",

    "R2627 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - no product byte was written, because the debt gate puts "
    "the owed battery before any further product work (the R2168 mixed-tree "
    "rule) and that leg is still running; (b) the battery is NOT green and is "
    "NOT claimed green - it is live at closeout with 331/643 suites green, "
    "zero red rows and no evidence file yet, so reconcile-battery-R2624 "
    "STAYS OPEN at its registered 643/4834 and the next window adopts this "
    "leg and closes the row (the R2601/R2607/R2609/R2614 precedent); (c) my "
    "own first launcher draft resolved BASE one directory too low and died on "
    "logs/battery-R2627.stream under src/, which is disclosed rather than "
    "presented as a clean first try - it wrote no evidence and started no "
    "process, and the corrected launcher printed LAUNCHED pid=82760 at its "
    "measured target; (d) the fold ran BEFORE the append at a true round-block "
    "boundary (items 92..97, the complete R2624 block ending on its push and "
    "export receipt) after a dry run that agreed exactly, 77009B -> 69978B "
    "with margin 8522 and the archive VERIFIED, and one of my first summaries "
    "was REFUSED by the predicate for token-missing and was widened to all "
    "nine measured tokens rather than loosened; (e) Docker is absent on this "
    "host so no containerised bring-up of the sandbox faces is claimed; (f) "
    "the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items (merchant id, mini-program appid/secret); (g) tasks.md was not "
    "touched, it is the P-47 canonical board; (h) BigDomain-OSLoop still needs "
    "an ELEVATED shell for its S4U re-registration (carried ceo-pending "
    "physical item loop-s4u-reconcile).",

    "R2627 tokens: local=~11k api=0 api_reason=verification window - one "
    "five-silence scan with the content-addressed decisions scan, the group "
    "orders tail and the ledger face actually read, one debt gate plus queue "
    "head and floor read, one registry target re-measured by import on both "
    "axes, one one-off launcher written, corrected at its birth site and used "
    "to start the leg detached with its stream and pid in separate files, two "
    "liveness reads and two progress reads on the live stream, one fold at a "
    "true round block boundary with the archive verified and ledger CLEAN, and "
    "the state/export/heartbeat closeout; zero cloud calls and zero external "
    "API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
    expected["last_order"] = NEW_ORDER
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = [" " * item_indent + json.dumps(item, ensure_ascii=False) + ","
                for item in LINES[:-1]]
    inserted.append(" " * item_indent
                    + json.dumps(LINES[-1], ensure_ascii=False))
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    out = _retick(out, data["tick"], expected["tick"])
    out = _reorder(out, data["last_order"], NEW_ORDER)
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2627_")
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


def _retick(text, old, new):
    needle = '"tick": %d' % int(old)
    if needle not in text:
        raise SystemExit("REFUSED tick field not found as %r" % needle)
    return text.replace(needle, '"tick": %d' % int(new), 1)


def _reorder(text, old, new):
    needle = '"last_order": %s' % json.dumps(old, ensure_ascii=False)
    if needle not in text:
        raise SystemExit("REFUSED order field not found as %r" % needle)
    return text.replace(needle, '"last_order": %s'
                        % json.dumps(new, ensure_ascii=False), 1)


if __name__ == "__main__":
    sys.exit(main())
