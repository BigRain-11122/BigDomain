"""seed_R2366.py - append this window's measured gap row to the tech queue.

One-off for the round. The row is a single line, so the append is one text
write with a read-back proof.
"""

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

ROW = (
    "- [ ] P2 tech seed (R2366, from this window own measured seam): "
    "`src/os/contract_usage_renderer.py` - ONE usage renderer for a CLI "
    "contract. Measured at R2366: `runner_arg_guard` renders a usage block "
    "from the runner contract (`usage_text(contract)`, shown live by its own "
    "`--guard-help`), and the new `battery_followup_help_wire` renders a "
    "SECOND usage block from the same kind of contract (four derived flag "
    "lines plus a house line), so the tree carries two formatters for one "
    "shape and a third tool would make three. This is the class the R2272 "
    "window collapsed for the battery follow-up (42 per-round copies to 1) "
    "and the class AC-BFH1 exists to stop at the flag-table layer. Product: "
    "the guard exports the renderer, the wire asks it, so a usage block has "
    "ONE owner and both CLIs answer with the same shape. Criteria "
    "AC-CUR1..AC-CUR6 pre-registered HERE BEFORE any code: AC-CUR1 the "
    "renderer is imported from runner_arg_guard (patching it moves BOTH the "
    "guard output and the wire output, and no second format string is "
    "written); AC-CUR2 the guard `--guard-help` text and the wire `--help` "
    "text keep every already-published line byte-identical to what R2366 "
    "shipped, so the collapse adds no new wording; AC-CUR3 a contract with a "
    "missing key refuses with its own code instead of rendering a partial "
    "block; AC-CUR4 a contract whose flag set is empty renders the honest "
    "`(none)` rather than a blank; AC-CUR5 the wire CLI exit codes stay "
    "0/2/5 and both CLIs keep a byte-stable `--json` over pinned keys; "
    "AC-CUR6 pure ASCII, stdlib only, no clock, no network, and the four "
    "follow-up sections still run. Anchors zero-occupancy at HEAD "
    "2026-11-02: contract_usage_renderer, AC-CUR, E_CUR, "
    "os-contract-usage-renderer, test_contract_usage_renderer.\n"
)


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    before = len(text.encode("utf-8"))
    if ROW.split("`")[1] in text:
        print("REFUSE duplicate seed already present")
        return 2
    body = text if text.endswith("\n") else text + "\n"
    body += ROW
    with io.open(QUEUE, "w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    ok = back.endswith(ROW) and back.count("AC-CUR1") == 1
    print("SEED appended before=%dB after=%dB readback=%s"
          % (before, len(body.encode("utf-8")), ok))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())