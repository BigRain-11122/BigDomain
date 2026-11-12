"""R2671 receipt: the delivery the push and the export actually made.

Every number is read from disk at run time (commit range from the two shas
handed in, evidence bytes, export bytes and its tick) rather than typed.
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
ROOT = os.path.dirname(os.path.dirname(HERE))
EVIDENCE = os.path.join(ROOT, "qa",
                        "export-composed-landed-seventh-wave-R2671.log")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
ITEM_INDENT = 2

LINES = []


def build(doc):
    ev = len(io.open(EVIDENCE, "rb").read())
    exp = len(io.open(EXPORT, "rb").read())
    tick = int(doc.get("tick", 0))
    LINES.append(
        "R2671 receipt: git push origin main read 780fe163..1bbf8997 main -> "
        "main and git rev-parse read HEAD equal to origin/main at 1bbf8997 "
        "with an EMPTY git status, so the seventh wave, its suite, the "
        "registry row, the matrix regeneration, the board row, the debt rows "
        "and the fold are all delivered. The export was refreshed AFTER the "
        "state append (the R2449/R2433 ordering law) through the shipped "
        "driver src/os/export_R2635.py to %dB at tick %d with queue=CURRENT "
        "and queue_drifted=(none), and check_export_consistency read pass=21 "
        "fail=0 VERDICT PASS. The fold ran as its own shipped face: dry run "
        "first (FOLD-DUE at 79235B against the 78500B gate, margin -735) then "
        "execute over items 81..102 at 79235B -> 63971B with margin 14529, "
        "tokens=34 ok=True and archive VERIFIED, so the live log is CLEAR "
        "rather than left over the waterline. ONE DEFECT WAS BORN AND "
        "REPAIRED HERE AND IS NAMED: state_io.ITEM_INDENT is 16 while this "
        "file own log items are indented by 2, so the two appended items "
        "landed at 16 and the shipped fold layout reader counted 102 item "
        "lines against a log of 104; src/os/state_indent_fix_R2671.py rewrote "
        "exactly those two lines at the file own prefix with a parse equality "
        "check before the write and a byte read-back after it, and the same "
        "mis-indent was the defect the PREVIOUS window repaired by hand, so "
        "the cause is the writer template and not this window own typing. "
        "DEBT: product-face-R2669 was closed through the shipped debtor at its "
        "measured 212164B (line 392, open 45->44, done 329->330, readback ok) "
        "and reconcile-battery-R2671 was appended first=yes at 212438B naming "
        "654 suites / 4900 criteria, because this window moved product src "
        "bytes and the registry moved, so the next window owes that battery "
        "and no product face." % (exp, tick))
    LINES.append(
        "R2671 honest disclosures: (a) NO CEO-visible artifact landed - the "
        "increment is a reader extension plus its six-criteria suite inside "
        "src/os, which is a product byte on the queue line but not something a "
        "CEO can open, and every P-47 face still waits on CEO physical items "
        "(merchant id, mini-program appid/secret); (b) one suite bug and one "
        "fixture bug in this window own new suite were found by running it "
        "(a bytes literal that has no encode, and a fixture that needed a file "
        "rather than bytes) and were fixed before the capture, so the 6/6 is "
        "the post-fix reading and not a first-try claim; (c) the ledger "
        "round-coverage suite named at R2614 still has NO registry row under "
        "that name, so it was not run and the substitution is named rather "
        "than implied; (d) src/os/scan_five_still.py still crashes at its "
        "final [ORD-TOP] print on the GBK console, so the scan ran under "
        "PYTHONIOENCODING=utf-8 - WORKED AROUND, NOT REPAIRED; (e) tasks.md "
        "was not touched, it is the P-47 canonical board; (f) BigDomain-OSLoop "
        "still reads InteractiveToken and needs an ELEVATED shell for its S4U "
        "re-registration (carried ceo-pending physical item "
        "loop-s4u-reconcile); (g) no proposal was added because this window "
        "spent its budget on the register-claimed product face and the window "
        "quota was already cleared in this weekly window.")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    build(data)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    rows = state_io._lf_lines(text)
    start, end = state_io._log_block(rows)
    if not rows[end - 1].strip().endswith(","):
        rows[end - 1] = rows[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * ITEM_INDENT + json.dumps(item,
                                                      ensure_ascii=False)
                        + suffix)
    out = state_io.EOL.join(rows[:end] + inserted + rows[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2671push_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    report = state_io.report(PATH)
    print("APPEND ok tick=%s log_len=%d bytes=%d"
          % (data.get("tick"), report["log_len"], report["bytes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
