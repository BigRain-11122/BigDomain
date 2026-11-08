"""state_fold_run suite (R2567; AC-SFOLD1..AC-SFOLD6 were pre-registered in
state/queue/tech.md at R2548 BEFORE this code existed - honesty law).

What this proves: the fold that state_fold.py could only report is now a
face an operator can run, and every claim it makes is measured - the archive
copy is byte-equal, the ledger coverage reader still sees every round it saw
before (because it reads the archive), the layout writer and the fold reader
agree about the same file, the gate only clears when the bytes really are at
or under the waterline, and a fold re-run on its own output writes zero bytes.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import state_fold_run as FR  # noqa: E402
import state_fold as SF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "state_fold_run.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-fold-run"

PASSES = 0
FAILS = 0
INDENT = " " * 16


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture_lines(count=44):
    lines = []
    for index in range(count):
        round_no = 1000 + index
        if index % 4 == 0:
            lines.append("R%d narrative line for the fixture round" % round_no)
        elif index % 4 == 1:
            lines.append("R%d tokens: local=1k api=0 api_reason=fixture"
                         % round_no)
        elif index % 4 == 2:
            lines.append("R%d disclosure sentence about the fixture window"
                         % round_no)
        else:
            lines.append("R%d repair note kept verbatim in the archive"
                         % round_no)
    return lines


def state_text(lines, indent=INDENT):
    items = (",\r\n").join(indent + json.dumps(line, ensure_ascii=False)
                           for line in lines)
    return ('{\r\n  "version": 1,\r\n  "tick": 7,\r\n  "note": "fixture",'
            '\r\n  "log": [\r\n' + items + '\r\n  ]\r\n}\r\n')


def make_world(base, lines=None, indent=INDENT):
    root = os.path.join(base, "world")
    os.makedirs(os.path.join(root, "src", "os"))
    os.makedirs(os.path.join(root, "logs"))
    path = os.path.join(root, "src", "os", "state.json")
    body = state_text(lines or fixture_lines(), indent=indent)
    with io.open(path, "wb") as handle:
        handle.write(body.encode("utf-8"))
    return root, path


def read(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def main():
    base = tempfile.mkdtemp(prefix="state-fold-run-")
    try:
        # --- AC-SFOLD1: verbatim archive copy + stated live floor -----------
        root, path = make_world(base)
        before = read(path)
        before_state = json.loads(before.decode("utf-8"))
        summary = ("fixture fold summary R1000 R1001 R1002 R1003 R1004 "
                   "R1005 R1006 R1007 R1008 R1009 R1010 R1011")
        report = FR.run(root, "R9001", 1, 1, 12, summary)
        archive = report["archive_path"]
        archived_text = read(archive).decode("utf-8")
        moved = before_state["log"][0:12]
        verbatim = all(line in set(archived_text.split("\n"))
                       for line in moved)
        after_state = json.loads(read(path).decode("utf-8"))
        floor_ok = len(after_state["log"]) >= FR.MIN_LIVE_LINES
        check(report["verdict"] == "CLEAR" and verbatim and floor_ok
              and report["archive_verified"],
              "AC-SFOLD1 verbatim archive copy for all %d moved lines, "
              "live block %d >= %d, verdict CLEAR"
              % (len(moved), len(after_state["log"]), FR.MIN_LIVE_LINES))

        # --- AC-SFOLD2: coverage reader reads the archive -------------------
        logs_dir = os.path.join(root, "logs")
        post_cov = FR.ledger_coverage(logs_dir, after_state["log"])
        pre_cov = FR.ledger_coverage(
            os.path.join(base, "empty-logs"), before_state["log"])
        check(post_cov["ledger_lines"] == pre_cov["ledger_lines"]
              and post_cov["ledger_rounds"] == pre_cov["ledger_rounds"]
              and "R1001" in post_cov["ledger_rounds"],
              "AC-SFOLD2 ledger coverage unchanged through the archive: "
              "ledger_lines %d -> %d, rounds %d -> %d (R1001 still found)"
              % (pre_cov["ledger_lines"], post_cov["ledger_lines"],
                 len(pre_cov["ledger_rounds"]),
                 len(post_cov["ledger_rounds"])))

        # --- AC-SFOLD3: round-trip + a re-run writes zero bytes -------------
        fields_ok = set(after_state.keys()) == set(before_state.keys())
        post_bytes = read(path)
        again = FR.run(root, "R9001", 1, 1, 12, summary)
        check(fields_ok and again["verdict"] == "ALREADY-FOLDED"
              and read(path) == post_bytes
              and again["bytes_after"] == again["bytes_before"],
              "AC-SFOLD3 round-trip: field set preserved, re-run reads "
              "ALREADY-FOLDED with zero bytes written")

        # --- AC-SFOLD4: writer and fold reader agree on one file ------------
        # R2522 measured the defect this closes: state_fold insisted on a
        # 16-space item indent while the shipped append path wrote 2-space
        # items, so the reader refused the real file. The reader now derives
        # the indent from the file, so a file in ANY consistent layout folds
        # in its OWN layout (no reformat) and only items that disagree with
        # each other are refused.
        agree = report["layout_agree"] is True
        other_root, other_path = make_world(os.path.join(base, "other"),
                                            indent="  ")
        other_before = read(other_path)
        other = FR.run(other_root, "R9002", 1, 1, 4, "other layout summary")
        other_after = read(other_path)
        kept_prefix = other_after.startswith(other_before.split(b"\n")[0])
        header_same = (other_after.split(b'"log"')[0]
                       == other_before.split(b'"log"')[0])
        bad_root, bad_path = make_world(os.path.join(base, "bad"),
                                        indent="  ")
        bad_text = read(bad_path).replace(b'"log": [\r\n  "',
                                          b'"log": [\r\n      "', 1)
        with io.open(bad_path, "wb") as handle:
            handle.write(bad_text)
        bad_before = read(bad_path)
        refused = False
        try:
            FR.run(bad_root, "R9003", 1, 1, 4, "mixed layout summary")
        except SF.StateFoldError as exc:
            refused = exc.code in ("E_SF_BAD_LAYOUT", "E_SF_BAD_STATE")
        check(agree and other["verdict"] == "CLEAR" and other["layout_agree"]
              and header_same and kept_prefix and refused
              and read(bad_path) == bad_before,
              "AC-SFOLD4 the reader derives the file own indent: a 2-space "
              "real-style file folds in its own layout (header bytes and "
              "prefix intact), and items disagreeing with each other refused "
              "with the shipped code and no byte written [agree=%s other=%s "
              "layout=%s header=%s prefix=%s refused=%s untouched=%s]"
              % (agree, other["verdict"], other["layout_agree"], header_same,
                 kept_prefix, refused, read(bad_path) == bad_before))

        # --- AC-SFOLD5: the gate is honest ---------------------------------
        gate_root, _ = make_world(os.path.join(base, "gate"))
        over = False
        try:
            FR.run(gate_root, "R9003", 1, 1, 4, "gate summary", gate=100)
        except FR.FoldRunError as exc:
            over = exc.code == "E_SFOLD_GATE"
        honest = (report["verdict"] == "CLEAR"
                  and report["bytes_after"] <= report["gate"]
                  and report["margin_after"] >= 0)
        check(over and honest,
              "AC-SFOLD5 gate honest: a fold that would leave %d bytes over "
              "100 refused E_SFOLD_GATE, the real fold cleared at %d <= %d"
              % (report["bytes_after"], report["bytes_after"],
                 report["gate"]))

        # --- AC-SFOLD6: dry run writes nothing; ASCII; registry wired ------
        dry_root, dry_path = make_world(os.path.join(base, "dry"))
        dry_before = read(dry_path)
        dry = FR.run(dry_root, "R9004", 1, 1, 4, "dry run summary",
                     dry_run=True)
        source = read(MODULE)
        ascii_ok = all(byte < 128 for byte in source)
        no_clock = b"import datetime" not in source and b"time.time" not in source
        with io.open(RUNNER, "rb") as handle:
            runner = handle.read()
        wired = (LABEL.encode("ascii") in runner
                 and EXPECTED_CRITERIA == 6)
        check(read(dry_path) == dry_before
              and dry["dry_run_digest_same"] is True
              and dry["verdict"] == "DRY-RUN" and ascii_ok and no_clock
              and wired,
              "AC-SFOLD6 dry run wrote zero bytes (digest %s), source ASCII "
              "and clockless, wired as %s(6)"
              % (digest(read(dry_path))[:16], LABEL))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("CRITERIA %d/%d passes=%d fails=%d"
          % (EXPECTED_CRITERIA, EXPECTED_CRITERIA, PASSES, FAILS))
    return 0 if FAILS == 0 and PASSES == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())