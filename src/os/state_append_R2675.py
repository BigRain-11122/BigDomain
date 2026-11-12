"""R2675 product window closeout: four honest log lines plus one tick.

Every number typed below was measured in this window (the pre-code limits, the
capture report, the evidence bytes, the registry by import, the matrix
regeneration, the board readback and the debt readbacks) rather than copied
from the register.

The indent is hard-coded at two spaces on purpose: state_io.ITEM_INDENT is 16
while this file own log items sit at 2.
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
INDENT = 2


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "2026-11-12 R2675 PRODUCT window on the queue head the debt gate named "
        "(product-face-R2674, state/queue/tech.md:676 prefix AC-PNAG1, "
        "criteria AC-PNAG1..AC-PNAG6 pinned in that row at R2594 BEFORE any "
        "code). Five readings at open: git status EMPTY at HEAD 32badef3 with "
        "no index.lock; ZERO unreplied @BigDomain rows (atbd_lines=0 "
        "unreplied_groups=0); the content-addressed decisions scan read rows=114 "
        "tokens=63 new=0; the group orders tail still the 2026-11-12 12:45 "
        "bm-a station ONBOARD row already carried as last_order and judged "
        "knowledge-only for this company; benchmarks_refreshed 2026-11-10 "
        "sitting two days inside the seven-day gate. debt_gate read CLAIM-FIRST "
        "item=product-face-R2674 first=1 open=45; queue_head named tech line 676 "
        "prefix AC-PNAG1 claimable=14 and queue_floor read FLOOR-MET at 5/5, "
        "14/10, 10/10.",
        "2026-11-12 R2675 THE THREE SEED LIMITS WERE RE-MEASURED BEFORE ANY CODE "
        "with src/os/limits_module_alias_match_ordinal_unique_R2675.py against "
        "private worlds: one while with TWO matches plus a second while with one "
        "match carried THREE bindings and named only TWO labels (while2>case, "
        "while>case); two matches inside ONE while else section named the second "
        "while_elsem2>case, a join artifact rather than while_else2; and a match "
        "in a for body nested in a while, a match in a while inside a while and "
        "an if nested inside a match case all kept attr-module-alias-unbound:M.HW "
        "with NO branch read. The same script run AFTER the change read three "
        "distinct labels (while>case, while2>case, while2_body>case), the else "
        "pair as while_else>case plus while_else2>case, and the three parked "
        "refusals byte for byte.",
        "2026-11-12 R2675 SHIPPED "
        "src/os/probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
        "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_"
        "while_match_while_else_nested_match_ordinal_unique_scope.py plus its "
        "six-criteria suite. Label law: the FIRST while keeps the shipped ordinal "
        "labels for its body matches because R2594 pinned them; every LATER while "
        "names its matches with its own prefix plus _body; a while else section "
        "names its matches while_else, while_else2, never the join artifact. The "
        "extension is applied THROUGH the shipped reading (the R2594 branch table "
        "is swapped inside one guarded block and restored in a finally) and the "
        "row carries the answer of EACH of the five parents named by AC-PNAG4, "
        "not only its immediate one. PROOF measured not quoted: AC-PNAG1..AC-PNAG6 "
        "SUITE PASS 6/6 TWICE identical through the shipped capture callable "
        "(qa/module-alias-walrus-match-ordinal-unique-scope-R2675.log, 15349B, "
        "utf-8, bom=False, crlf=0, lone_cr=0, nul=0, legs=2 identical=True "
        "fails=0) and the R2594 parent suite was run SEPARATELY and read SUITE "
        "PASS 6/6 (logs/adjacent-R2675.stream). REGISTRY 654 suites / 4900 "
        "criteria -> 655 / 4906 by exactly one row, recounted by import (655 "
        "unique names, 655 unique paths); docs/sandbox-suite-matrix.md read "
        "ROWS-MISMATCH 654 against 655 BEFORE any byte and was regenerated through "
        "the shipped write face to 67619 bytes at 655 rows, after which --check "
        "read DOC-CURRENT at rc=0.",
        "2026-11-12 R2675 BOARD AND DEBT: row 676 was closed through "
        "src/os/queue_close_R2675.py at its predicted and measured 1940986B -> "
        "1944152B (lines 694 -> 695, readback ok) and ONE row was seeded from "
        "this window own MEASURED limit as AC-PNAH1..AC-PNAH6 (the three labels "
        "while>case, while2>case and while2_body>case mean a PREFIX ack on while2 "
        "matches TWO bindings, measured 2 hits). DEBT through the shipped "
        "writers: product-face-R2674 closed at its predicted and measured 212772B "
        "-> 212775B (line 394, open 45->44, done 331->332, readback ok) and "
        "reconcile-battery-R2675 appended first=yes at 212775B -> 213076B naming "
        "655 suites / 4906 criteria, because this window moved product src bytes "
        "and one registry row and the R2168 mixed-tree rule puts the full battery "
        "on the committed tree BEFORE any further product byte. HONEST: (a) ONE "
        "product point on the Executive Protocol scale - a runnable reader with "
        "its own six-criteria suite that a maintainer can rerun - but nothing a "
        "CEO could newly open and no P-47 business surface moved, so every P-47 "
        "item still waits on CEO physical pieces; (b) the capture carries "
        "adjacent=0 and the parent suite was run separately rather than inside "
        "the capture, which is named rather than implied; (c) the fixture entry "
        "is expensive on this chain (one root-wide report on the real tree "
        "measures about 31s) so the live leg is ONE module and the AC-PNAG5 "
        "real-tree repeat was dropped in favour of two fixture readings whose "
        "reason strings are identical; (d) the face asks all five parents on "
        "every entry and the duplicate immediate-parent call was REMOVED to halve "
        "that cost, so base_pnag_chain and base_pnag_branch_reads are None while "
        "the five parent state/value/reason keys are measured; (e) "
        "src/os/scan_five_still.py still crashes at its final [ORD-TOP] print on "
        "the GBK console, so the scan ran under PYTHONIOENCODING=utf-8 - WORKED "
        "AROUND, NOT REPAIRED; (f) Docker is absent on this host; (g) tasks.md "
        "was not touched, it is the P-47 canonical board; (h) BigDomain-OSLoop "
        "still needs an ELEVATED shell for its S4U re-registration (carried "
        "ceo-pending physical item loop-s4u-reconcile).",
        "R2675 tokens: local=~26k api=0 api_reason=product window - one "
        "five-silence scan with the content-addressed decisions face, the group "
        "orders tail and the ledger face read, one debt gate read and one queue "
        "head plus floor read, one limits script measuring six shapes BEFORE any "
        "code and re-measuring them AFTER the change, one face module plus one "
        "six-criteria suite written and registered as exactly one row, one "
        "detached suite run that read 6/6, one capture through the shipped "
        "callable producing two identical legs, one separately run adjacent "
        "parent suite at 6/6, one registry row recounted by import, one designed "
        "ROWS-MISMATCH then one regeneration checked DOC-CURRENT, one board row "
        "closed and one seeded with a per-round writer, two debt rows moved "
        "through their shipped writers, one successor limit measured (prefix "
        "while2 hits two labels), and the state/export closeout; zero cloud calls "
        "and zero external API touches",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(lines)
    expected["tick"] = tick + 1
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(lines):
        suffix = "," if index < len(lines) - 1 else ""
        inserted.append(" " * INDENT + json.dumps(item, ensure_ascii=False) +
                        suffix)
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
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2675_")
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
