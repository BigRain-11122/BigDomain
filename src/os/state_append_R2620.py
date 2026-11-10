"""R2620 verification window closeout."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-11 R2620 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2616, pre-registered 641 suites / 4822 criteria). Five readings at open: git status carried ONE untracked file qa/reconcile-all-R2616.log which is the adopted leg own evidence, HEAD 242848c7 equal to origin/main with no index.lock, ZERO @BigDomain rows in cph4/evolution-ledger.md, the content-addressed D-/C-/T- decisions scan read 184 file tokens against the 225-token baseline with new=0 over 427 rows (the two regex hits D-20261015 and D-20261101 are DATE CITATIONS inside prose, measured in context rather than counted as decisions, and last_decision_rows 173 is the auxiliary row count while the token set is the authority), the group orders tail unchanged at its 2026-11-10 03:52 row so last_order stands, and benchmarks_refreshed 2026-11-10 inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2616 open=40 first=1, queue_head named tech line 650 prefix AC-EDMG1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "R2620 THE OWED LEG HAD FINISHED GREEN AND IS ADOPTED AND RE-MEASURED RATHER THAN TRUSTED: ZERO python processes carried reconcile_all or battery_stream in their command line at open (measured by command line, not by pid existence), qa/reconcile-all-R2616.log read 1090582B / 8560 lines / utf-8 bom=False crlf=0 lone_cr=0 nul=0 with 641 'PASS suite' rows against 641 UNIQUE names, 7 'PASS reconcile' control rows, ZERO 'FAIL' rows, an independent criteria recount over those 641 rows summing to EXACTLY 4822, and the closing line 'RUNNER PASS (641/641 suites green, reconcile controls 7/7, 4046.8s)'. ONE DIALECT FACT IS NAMED RATHER THAN ASSERTED AWAY: 26 of those rows carry pass-lines=0 with a non-zero criteria count, the shipped runner dialect for suites that print no AC- lines. TARGET RE-MEASURED BY IMPORT AFTER THE FACT: reconcile_all.SUITES read 641 suites / 4822 criteria / 641 unique names / 641 unique paths, byte for byte the registered number.",
    "R2620 THE R2614 LESSON WAS EXERCISED AND IT CAUGHT A REAL RED ON THE COMMITTED TREE: ten write-sensitive suites were re-run INDIVIDUALLY before any byte of this window was written, through the shipped reconcile_all.run_cmd dialect (PYTHONIOENCODING=utf-8 child pipes, utf-8 decode, cwd=src/sandbox, per-suite cap) via a one-off src/os/verify_writesensitive_R2620.py, and the FIRST pass measured NINE green against ONE RED: os-matrix-stamp-compare read rc=1 pass=5 fail=1 because AC-MSC4 requires the shipped suite_matrix --check to AGREE with matrix_stamp_compare, and the authority read rc=2 since docs/sandbox-suite-matrix.md still recorded evidence leg qa/reconcile-all-R2614.log at 65483B while the registry stood at 641 suites / 4822 criteria — i.e. the document was stale, exactly as R2619 pre-dicted. The red was healed AT ITS BIRTH SITE by the document regeneration below rather than by loosening the assertion, and the identical ten-suite set then read RERUN PASS green=10 red=0 (qa/write-sensitive-rerun-R2620.log, 10386B, utf-8, one RE-RUN PASS line).",
    "R2620 DOCUMENT: docs/sandbox-suite-matrix.md read FAIL BY DESIGN BEFORE any byte was written (suite_matrix_reconcile --check printed EVIDENCE-FACE, recorded-evidence=qa/reconcile-all-R2614.log, registry-rows=641 at 4822 criteria, rc=2), was then regenerated stamp-aligned from THIS round own green leg through the shipped face (suite_matrix_reconcile --write --evidence qa/reconcile-all-R2616.log --stamp-from the existing document) to 65476 bytes at 641 rows / 4822 criteria, the face then read DOC-CURRENT at rc=0 and the underlying authority src/sandbox/suite_matrix.py --check read 'PASS check: byte-identical (65476 bytes, 641 suites, 4822 criteria)' at rc=0.",
    "R2620 DEBT AND GATE through the shipped writers: reconcile-battery-R2616 was closed at its predicted and measured 197826B -> 197829B (line 361, open 40->39, done 304->305, readback ok), and product-face-R2620 was appended first=yes at its predicted 197829B -> 198259B (readback ok) naming the next window a PRODUCT face on the queue head state/queue/tech.md:650 prefix AC-EDMG1, whose AC-EDMG1..AC-EDMG6 were pinned in that row at R2616 BEFORE any code. NO successor battery is owed: the registry is unmoved at 641 suites / 4822 criteria (re-read by import, not trusted), this window added no suite and no product src byte, and the only tree movement is the document it regenerated from the leg it consumed. debt_gate re-read CLAIM-FIRST item=product-face-R2620 opened=R2620 carried=0 stale=no open=40 first=1. No queue row was opened or closed, because a verification window writes no board row.",
    "R2620 honest disclosures: (a) ZERO product points on the Executive Protocol scale - no product byte was written, nothing a CEO could newly open exists, and every P-47 business item still waits on CEO physical pieces (merchant id, mini-program appid/secret); the deliverable is a measured green 641/4822 battery on disk, a matrix document whose evidence column names THIS round own green leg, and one closed debt row with one opened; (b) the leg itself was authored by the PREVIOUS window launcher and is adopted here, re-measured on encoding, row count, name uniqueness, criteria sum, control rows and its own verdict line rather than quoted; (c) the ten-suite write-sensitive set is a BOUNDED selection chosen for the artifacts this window rewrites (matrix/export/closeout/state/ledger/queue-head faces), NOT the whole write surface, and is named as a limit rather than a coverage claim; (d) the one red that set found was genuine and is healed by the regenerated document, which is also the reason the AC-MSC4 agreement predicate is worth keeping strict; (e) 26 suite rows carry pass-lines=0 against a non-zero criteria count, the shipped dialect named above; (f) two tool defects named by earlier windows remain UNREPAIRED and are carried rather than hidden - src/os/scan_five_still.py still dies with UnicodeEncodeError on its [ORD-TOP] print under a gbk console, and src/os/debt_note_append.py still needs its marker inside --text while its usage line does not say so (this window composed its note with the marker inside --text and its suite was not needed for the append to land); (g) Docker is absent on this host so no containerised sandbox bring-up is claimed; (h) tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2620 tokens: local=~12k api=0 api_reason=verification window - one five-silence scan with the content-addressed decisions token diff measured in context, one debt gate plus queue head and floor read, one adopted green leg re-measured on six faces plus one registry target recounted by import on four axes, one ten-suite write-sensitive re-run through the shipped run_cmd dialect that caught one real red, one designed document FAIL then one stamp-aligned regeneration through the shipped reconcile face proved byte-identical by the authority, one debt row closed and one opened through their shipped writers, and the state/export closeout; zero cloud calls and zero external API touches",
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2620_")
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
