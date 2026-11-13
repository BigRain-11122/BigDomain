"""R2695 push receipt: one measured log line, no tick advance."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    lines = [
        "R2695 push and export: git push origin main read 85dc4e6b..53e70a21 "
        "main -> main and git rev-parse read HEAD equal to origin/main at "
        "53e70a21 with an EMPTY git status, so the adopted red leg, its "
        "measured bytes, the successor launch and the state/export closeout are "
        "delivered; this receipt line lands in the follow-up commit it "
        "describes. The export was refreshed AFTER the state append and after "
        "the tick advance (the R2449/R2433 ordering law) through the shipped "
        "driver src/os/export_R2635.py to 406279B at tick 2687 with "
        "queue=CURRENT and queue_drifted=(none), and check_export_consistency "
        "read pass=21 fail=0 VERDICT PASS with the three CEO-visible lines "
        "derived rather than typed; it is re-derived again AFTER this line so "
        "the window own log count agrees with the document it is counted in. "
        "state_fold --check read FOLD-CLEAR at 76454B against the 78500B gate "
        "with margin 2046 and 70 live log lines, and ledger_lines --check read "
        "VERDICT CLEAN with new_missing none and new_orphan none. THE SUCCESSOR "
        "LEG WAS LIVE AT THIS CLOSEOUT AND THAT IS THE HONEST STATE OF THE "
        "ROUND: pid 113432 with its reconcile_all child 47944 alive by command "
        "line, logs/battery-R2695.stream carrying 44 PASS suite rows and ZERO "
        "FAIL suite rows, so reconcile-battery-R2692 STAYS OPEN at its "
        "registered 661 suites / 4942 criteria and the next window ADOPTS this "
        "leg by its evidence path qa/reconcile-all-R2695.log rather than "
        "relaunching, then owes the R2614 write-sensitive re-run on the FINAL "
        "committed tree before any verdict.",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + lines
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = " " * state_io.ITEM_INDENT + json.dumps(lines[0], ensure_ascii=False)
    out = state_io.EOL.join(doc_lines[:end] + [inserted] + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2695p_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("RECEIPT ok bytes=%d log_len=%d" % (after["bytes"], after["log_len"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
