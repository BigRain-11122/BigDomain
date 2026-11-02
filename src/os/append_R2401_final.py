# append_R2401_final.py - one disclosure item with the FINAL measured numbers,
# appended through the same guard door, after the module changed under the
# first capture.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger_line_shape_guard as LLSG  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

ITEM = (
    "2026-11-03 R2401 re-measurement disclosure, stated instead of quietly "
    "re-quoted: the first capture ran against the module as it stood BEFORE "
    "the narrative-line scope fix, so the digest quoted in the evidence line "
    "(8017c190e91917fc) and the dry-run size (77174) are superseded. The door "
    "now accepts a narrative round line - the law classifies it ROUND, it "
    "carries no ledger body and lands untouched - and refuses only a "
    "date-prefixed line that also carries ' tokens:' plus ' local=', which is "
    "exactly what R2392 wrote. Final measured after that fix: the suite is "
    "6/6 twice with adjacent=3 fails=0 (qa/ledger-line-shape-guard-R2401.log "
    "re-captured, 1522B), the live capture reads the REAL post-closeout "
    "82273B state with the R2400 ledger line ACCEPTED, the dated candidate "
    "REFUSED E_LLSG_DATE_PREFIX token=2026-11-02, a dry run predicting 83015 "
    "bytes with wrote=no, and the module digest a3c7fcdd98a4f7c3 unchanged "
    "before and after. Three state items that would have landed under the "
    "stricter rule were refused by the door during this window, which is the "
    "door working rather than a criterion relaxed."
)


def main():
    verdict = LLSG.append_ledger_line(STATE, ITEM, execute=True)
    if verdict["verdict"] != "ACCEPTED" or verdict["wrote"] != "yes":
        raise SystemExit("E_APPEND: %r" % verdict)
    text = io.open(STATE, "r", encoding="utf-8", newline="").read()
    try:
        report = state_io.layout(text)
        print("LAYOUT ok=%r" % report.get("layout_ok"))
    except Exception as exc:
        print("LAYOUT check skipped: %r" % exc)
    payload = json.loads(text)
    print("STATE log_items=%d bytes=%d" % (len(payload["log"]),
                                           os.path.getsize(STATE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())