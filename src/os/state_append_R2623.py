"""R2623 state append: five log lines and one tick.

The round adopted the R2622 battery leg, measured it, closed the debt row and
seeded the next product face.  Every line below carries a measured number
rather than a quoted one.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-11 R2623 VERIFICATION window ADOPTING the leg R2622 left running "
    "for the battery the debt gate named first (reconcile-battery-R2621, "
    "pre-registered 642 suites / 4828 criteria). Five readings at open: git "
    "status EMPTY at HEAD a7343636 equal to origin/main with no index.lock, "
    "ZERO @BigDomain rows in cph4/evolution-ledger.md, the content-addressed "
    "decisions scan read tokens=182 with new=0 over 307 rows, the group orders "
    "tail unchanged at its 2026-11-11 03:52 row, benchmarks_refreshed "
    "2026-11-10 inside the seven-day gate. debt_gate read CLAIM-FIRST "
    "item=reconcile-battery-R2621 first=1 open=41. The leg was sampled FOUR "
    "times while it ran (642 suite rows and zero fails by the last sample) and "
    "finished at 05:30:44 with BATTERY rc=0 in 2931.4s.",

    "2026-11-11 R2623 THE GREEN IS MEASURED, NOT QUOTED: "
    "qa/reconcile-all-R2622.log reads 1091366B with bom=False crlf=0 "
    "lone_cr=0 nul=0 over 8568 lines, closing RUNNER PASS (642/642 suites "
    "green, reconcile controls 7/7, 2931.3s), ZERO FAIL suite rows, 642 PASS "
    "suite rows and an INDEPENDENT recount over their own criteria fields "
    "summing to EXACTLY 4828 - the registered target - while the registry was "
    "re-read by import at 642 suites and 642 unique names.",

    "2026-11-11 R2623 FOLLOW-UP IN THE DESIGNED ORDER AND DEBT: the dry run "
    "read matrix FAIL by design at on-disk 65597B against regenerated 65582B "
    "with NO byte written while fingerprint read CLEAN domains=5, profile "
    "byte-identical and census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was "
    "then regenerated stamp-aligned from THIS round own green evidence to "
    "65582B at 642 suites / 4828 criteria with its green line honestly "
    "reading 642/642 and --check byte-identical at rc=0, after which the "
    "write leg read all four PASS for VERDICT R2623 PASS failing=none "
    "(APPENDED 1951B eol_ok=True). reconcile-battery-R2621 was closed through "
    "the shipped debtor at its predicted and measured 198786B -> 198789B "
    "(line 364, open 41->40, done 306->307, readback ok) and "
    "product-face-R2623 was appended first=yes at its predicted 199481B "
    "naming the next window a PRODUCT face on the queue head "
    "state/queue/tech.md:652 prefix AC-EDMH1. NO successor battery is owed: "
    "no product src byte moved and the registry is unmoved at 642 suites / "
    "4828 criteria.",

    "R2623 honest disclosures: (a) ZERO product points on the Executive "
    "Protocol scale - nothing a CEO could newly open was built; the "
    "deliverable is a green 642/4828 battery on disk, a document whose "
    "evidence column names THIS round own leg, one closed debt row and one "
    "opened; (b) the leg was AUTHORED by R2622 and is ADOPTED here - it was "
    "sampled four times while running and measured only after it closed, "
    "never restarted; (c) commits f53fad0a and a7343636 landed UNDER the leg "
    "after its launch on 406ad940, so a green verdict is admissible only "
    "beside an individual re-run of the write-sensitive suites on the FINAL "
    "committed tree, which is owed as this window receipt step; (d) fold 683 "
    "covered items 90..96 including the R2622 receipt line, a true round "
    "block ending on its own receipt rather than a tokens line, and the "
    "split-in-half predicate did not trigger because no line was kept after "
    "it; (e) Docker is absent on this host so no containerised bring-up of "
    "the sandbox faces is claimed; (f) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (g) tasks.md was not touched, it is the P-47 canonical "
    "board; (h) BigDomain-OSLoop still needs an ELEVATED shell for its S4U "
    "re-registration (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2623 tokens: local=~13k api=0 api_reason=verification window - one "
    "five-silence scan with the content-addressed decisions scan, the group "
    "orders tail and the ledger face actually read, one debt gate read naming "
    "the battery, four live progress readings on the adopted leg, one "
    "evidence file measured on bytes, encoding, suite rows and an independent "
    "criteria recount, one designed matrix FAIL with no byte written, one "
    "stamp-aligned regeneration checked byte-identical, one four-section "
    "write leg to a PASS verdict, one debt row closed and one opened through "
    "their shipped writers, one fold at a true round block boundary with the "
    "archive verified, and the state/export/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
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
    # every line but the last carries its own separator, so the block keeps
    # the canonical shape the layout reader expects
    inserted = [" " * item_indent + json.dumps(item, ensure_ascii=False) + ","
                for item in LINES[:-1]]
    inserted.append(" " * item_indent
                    + json.dumps(LINES[-1], ensure_ascii=False))
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    # tick lives outside the log block, so the payload is compared after the
    # tick rewrite below rather than before it.
    out = _retick(out, data["tick"], expected["tick"])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2623_")
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
    """Move the tick field by one, matching the file own formatting."""
    needle = '"tick": %d' % int(old)
    if needle not in text:
        raise SystemExit("REFUSED tick field not found as %r" % needle)
    return text.replace(needle, '"tick": %d' % int(new), 1)


if __name__ == "__main__":
    sys.exit(main())
