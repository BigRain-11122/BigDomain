"""R2567 honest correction: name exactly what the open scan covered.

The round line said "five-silence scan at open"; measured, only three of the
five were actually read this window, so this line names the covered ones and
names the two that were NOT compared rather than letting the phrase imply
more than was done.
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINE = (
    "R2567 correction, added before push because the round line overclaimed: "
    "it said 'five-silence scan at open' and the MEASURED truth is three of "
    "the five. READ: git status EMPTY at HEAD cb7cf5b1 with no index.lock; "
    "the group ledger grep for @BigDomain returned ZERO rows (nothing to "
    "reply to); the debt gate read first=yes product-face-R2566 with the "
    "opens named above. NOT READ this window: the content-addressed "
    "decisions diff against the stored baseline (state.json still carries "
    "last_decision_rows 273 from R2566, so a row added after that round "
    "would not have been seen) and the group orders tail against "
    "last_order 2026-11-08 12:06. Neither is claimed clean - the next window "
    "must re-run both rather than inherit this window silence as evidence."
)


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    if json.dumps(data, indent=1, ensure_ascii=False) != text:
        print("REFUSED E_SA_RT_LAYOUT")
        return 3
    data["log"].append(LINE)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=1, ensure_ascii=False))
    size = os.path.getsize(STATE)
    print("STATE log=%d after=%dB ok=%s"
          % (len(data["log"]), size, size <= 78500))
    return 0


if __name__ == "__main__":
    sys.exit(main())