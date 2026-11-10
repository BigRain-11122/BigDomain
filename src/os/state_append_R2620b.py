"""R2620 follow-up: push receipt, adopt-after-commit re-run, fold receipt."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "R2620 push and adopt-after-commit re-run: git push origin main SUCCEEDED (242848c7..267602fd main -> main) and git rev-parse read HEAD equal to origin/main at 267602fd with an EMPTY git status after the commit, so the whole window is delivered. The R2614 lesson was then discharged at its STRONGEST reading rather than its weakest: the identical ten write-sensitive suites were re-run a THIRD time ON THE FINAL COMMITTED TREE, after the push, and read RERUN PASS green=10 red=0 with the authority src/sandbox/suite_matrix.py --check reading 'PASS check: byte-identical (65476 bytes, 641 suites, 4822 criteria)' at rc=0, so the green battery verdict and the document it regenerated hold on the tree a reader can clone rather than only on the tree they were authored on.",
    "R2620 FOLD receipt: state.json read 81274B against the 78500B gate after the seven appended lines, so fold 680 ran at a TRUE ROUND-BLOCK BOUNDARY (items 87..94, the complete R2619 verification-round block ending on its push line) only after a dry run whose prediction agreed exactly, 81274B -> 74698B with margin 3802 and 94 live lines, archive VERIFIED, layout AGREE, 4 tokens preserved verbatim, state_fold --check then read FOLD-CLEAR and ledger_lines --check read CLEAN with rounds_without_ledger=none ledger_without_round=none ledger=9 round=50 other=35 baseline missing=0 orphan=0. MY OWN FIRST FOLD ATTEMPT WAS REFUSED by the shipped predicate for token-missing because I had listed three of the four tokens in the fold summary; the predicate named the gap and the retry named D-TOP, which is the fail-closed face working rather than a defect.",
    "R2620 one further tool fact is named because it bit me: a call of the form 'python src/sandbox/reconcile_all.py --help' does not print usage - the runner treats argv[1] as the EVIDENCE PATH and writes a file literally named '--help' (13859B of a real suite leg on this tree). The stray file was DELETED before the commit rather than staged, and the observation is carried as a candidate limit: the battery runner has no unknown-flag refusal on its positional argument. This is my own misuse, disclosed instead of tidied away.",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    item_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith('"') and not stripped.startswith('"log"'):
            item_indent = len(line) - len(stripped)
            break
    if item_indent is None:
        print("REFUSED no item line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * item_indent +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    out = out.replace('"tick": %d' % data["tick"],
                      '"tick": %d' % expected["tick"], 1)
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2620b_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    print("APPENDED lines=%d bytes=%d tick=%d"
          % (len(LINES), len(payload), expected["tick"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
