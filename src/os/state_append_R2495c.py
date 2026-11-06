"""R2495 third append (one-off): the export driver due-date birth-site fix."""

import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINE = (
    "2026-11-06 R2495 birth-site fix, disclosed not dressed up: the export base "
    "src/os/export_R2431.py hardcoded the CEO-visible next_milestone_due to "
    "\"2026-11-06T12:00:00+08:00\" at line 137, so every re-derivation this "
    "window published a milestone due eight hours in the past while its own "
    "next_milestone text named 2026-11-07 - exactly the F3 written-dead-value "
    "fault. Repaired at the birth site: the base now publishes a module-level "
    "NEXT_DUE (defaulting to the old literal, so every existing driver keeps "
    "its bytes) and export_R2495.py sets 2026-11-07T23:00:00+08:00. VERIFIED: "
    "the export re-derived, the published due now reads 2026-11-07T23:00, the "
    "queue block landed CURRENT and check_export_consistency reads 21/21 PASS; "
    "the five suites that touch the export face were run alone and all read "
    "SUITE PASS 6/6 (os-export-freshness, export-closeout-gate-parity, "
    "queue-export-freshness-gate, queue-floor-export-face, "
    "queue-export-gate-wire); both changed files are pure ASCII. Because a "
    "shipped module moved after the battery ran, reconcile-battery-R2496 is "
    "opened first=no at the unmoved 576 suites / 4432 criteria so the next "
    "window's tree is proved rather than assumed."
)


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINE:
        print("already appended")
        return
    state["log"].append(LINE)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d bytes=%d" % (len(back["log"]),
                                          os.path.getsize(PATH)))


if __name__ == "__main__":
    main()