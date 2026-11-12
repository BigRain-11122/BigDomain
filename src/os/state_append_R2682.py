"""R2682 product window closeout: honest log lines plus one tick.

Every number below was measured in this window (the five-silence scan, the debt
gate, the registry by import on four axes, the limits probe before and after,
the evidence bytes with its two legs, the matrix check, the board and debt
writers, both gates) rather than copied from the register.

The indent is hard-coded at two spaces on purpose: state_io.ITEM_INDENT is 16
while this file own log items sit at 2.
"""

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
        "2026-11-13 R2682 PRODUCT window on the queue head the debt gate named "
        "(product-face-R2681, state/queue/tech.md:679 prefix AC-PNAK1, criteria "
        "AC-PNAK1..AC-PNAK6 pinned there at R2679 BEFORE any code). Five "
        "readings at open, all clean: git status EMPTY at HEAD 4f5ab235 with no "
        "index.lock; ZERO unreplied @BigDomain rows (atbd_lines=0 "
        "unreplied_groups=0); the decisions scan read rows=120 tokens=64 new=0; "
        "the group orders tail still the 2026-11-12 12:45 bm-a ONBOARD row "
        "carried as last_order and judged knowledge-only; benchmarks_refreshed "
        "2026-11-10 three days inside the gate. debt_gate read CLAIM-FIRST "
        "product-face-R2681 first=1 open=45 and the registry was re-measured BY "
        "IMPORT at 657 suites / 4918 criteria / 657 unique names / 657 unique "
        "paths with NO battery owed.",
        "R2682 THE TRUNCATION WAS RE-MEASURED BEFORE ANY BYTE on the R2679 "
        "face: ack_unnameable(['a','ab','ac']) answered {'a': "
        "'strict-prefix-of:ab'} and ['a','ab','ac','ad'] also named only 'ab', "
        "so a caller could not count the bindings that outrank a label. "
        "SHIPPED src/os/probe_seam_name_binding_arm_mixed_residual_alias_"
        "attribute_import_alias_scope_module_alias_attribute_alias_walrus_"
        "relative_branch_elif_with_while_match_while_else_nested_match_"
        "ordinal_unique_prefix_unnameable_siblings_scope.py plus its "
        "six-criteria suite: strict_prefix_siblings carries EVERY distinct "
        "sibling in published order, unnameable_reason joins them with ',' "
        "while duplicate:<n> keeps riding and the single-sibling word is "
        "untouched. MEASURED after the change: ['a','ab','ac'] -> "
        "'strict-prefix-of:ab,ac', ['a','ac','ab'] -> 'strict-prefix-of:ac,ab' "
        "(published order, not sorted), ['a','a','ab','ac'] -> "
        "'strict-prefix-of:ab,ac+duplicate:2', and ['x','xy'] -> "
        "'strict-prefix-of:xy' byte for byte what R2679 published.",
        "R2682 PROOF and registry: AC-PNAK1..AC-PNAK6 SUITE PASS 6/6 twice "
        "byte-identical through the single-writer evidence face "
        "(qa/prefix-unnameable-siblings-R2682.log, 6163B, utf-8, bom=False, "
        "crlf=0, lone_cr=0, nul=0, 68 lines, 62 PASS, legs=2 identical=True "
        "digest=5FF98AFDE5A14B18, adjacent=2 both SUITE PASS 6/6, fails=0) with "
        "one bounded live leg reading 22 loops of one real module unchanged and "
        "read-only. Registry 657/4918 -> 658/4924 by exactly one row recounted "
        "by import (658 unique names, 658 unique paths); "
        "docs/sandbox-suite-matrix.md read FAIL stale BEFORE any byte and was "
        "regenerated stamp-aligned from the R2680 green leg to 69049 bytes at "
        "658 suites / 4924 criteria with its green line honestly reading "
        "657/658, then --check read byte-identical at rc=0.",
        "R2682 BOARD AND DEBT: row 679 closed through src/os/queue_close_R2682.py "
        "at its predicted and measured 1951269B -> 1954971B (lines 697 -> 698, "
        "readback ok) and ONE row seeded from this window own MEASURED limit as "
        "AC-PNAL1..AC-PNAL6 (the sibling list is joined with a bare ',' that is "
        "never escaped, so ack_unnameable(['a','ab,ac']) answers the SAME word "
        "['a','ab','ac'] answers and one sibling named 'ab,ac' cannot be told "
        "from two siblings). product-face-R2681 closed through the shipped "
        "debtor at 215204B -> 215207B (line 400, open 45->44, done 337->338, "
        "readback ok) and reconcile-battery-R2682 appended first=yes at 215207B "
        "-> 215656B naming 658 suites / 4924 criteria, because this window "
        "moved product src bytes and one registry row and the R2168 mixed-tree "
        "rule puts the full battery on the committed tree BEFORE any further "
        "product byte.",
        "R2682 honest disclosures: (a) ONE product point on the Executive "
        "Protocol scale - a runnable face with its own six-criteria suite a "
        "maintainer can rerun - but nothing a CEO could newly open and no P-47 "
        "business surface moved, so every P-47 item still waits on CEO physical "
        "pieces; (b) the first double-leg capture was cancelled by the shell "
        "five-minute silence limit because the capture buffers suite output and "
        "the shell saw none, so it was relaunched DETACHED through a one-off "
        "launcher DELETED before the commit and the cancelled attempt left no "
        "evidence file; (c) state_io.ITEM_INDENT still reads 16 against this "
        "file own 2; (d) Docker is absent on this host; (e) tasks.md was not "
        "touched, it is the P-47 canonical board; (f) BigDomain-OSLoop still "
        "reads InteractiveToken and needs an ELEVATED shell (carried "
        "ceo-pending item loop-s4u-reconcile).",
        "R2682 tokens: local=~12k api=0 api_reason=product window - one "
        "five-silence scan with the content-addressed decisions face, the group "
        "orders tail and the ledger face read, one debt gate read, one queue "
        "head read, one registry target re-measured by import on four axes, one "
        "limits probe measuring six shapes BEFORE any code and re-measuring "
        "them AFTER, one face module plus one six-criteria suite written and "
        "registered as exactly one row, one detached double-leg capture that "
        "read 6/6 twice with one digest plus two adjacent suites, one designed "
        "matrix FAIL then one stamp-aligned regeneration checked "
        "byte-identical, one board row closed and one seeded, two debt rows "
        "moved through their shipped writers, and the state/export/heartbeat "
        "closeout; zero cloud calls and zero external API touches",
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
    print("PREDICTED bytes=%d (gate 78500, margin %d)"
          % (len(payload), 78500 - len(payload)))
    if "--dry" in sys.argv:
        print("DRY run, nothing written")
        return 0
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2682_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d items_off_indent=%d" %
          (tick + 1, after["bytes"], after["log_len"],
           after["items_off_indent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
