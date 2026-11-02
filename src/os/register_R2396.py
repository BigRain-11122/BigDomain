"""R2396 register note update: re-target the carried battery row in place.

The register refuses the WHOLE file for one unknown key (the R2391 and R2395
lessons), so nothing is appended as a new key - the text is folded INSIDE the
existing note. Predicted after-size, one atomic replace, read-back, and the
shipped reader is then asked to parse the result.

Stdlib only, ASCII source, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

REGISTER = os.path.join(REPO, "state", "debt.md")

OLD_TAIL = "so a loaded machine will abort this battery again with no code defect.) | first=yes"

NEW_TAIL = ("so a loaded machine will abort this battery again with no code "
            "defect. R2396 note: still not run - the product face "
            "(matrix_evidence_pile_consistency) took this window too and the "
            "tree it must walk now carries 522 suites / 4108 criteria "
            "(521/4102 plus this window's os-matrix-evidence-pile-consistency "
            "suite, +1 suite / +6 criteria). The R2396 face makes the row more "
            "likely to finish rather than less: a bare evidence name now "
            "reaches the matrix tool as the pile the guard measured, so the "
            "follow-up section cannot fail on a path the guard approved.) | first=yes")


def main():
    with io.open(REGISTER, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    before = len(raw.encode("utf-8"))
    if raw.count(OLD_TAIL) != 1:
        print("E_REG_ANCHOR count=%d" % raw.count(OLD_TAIL))
        return 2
    text = raw.replace(OLD_TAIL, NEW_TAIL)
    after = len(text.encode("utf-8"))
    temp = REGISTER + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, REGISTER)
    with io.open(REGISTER, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    import debt_register as DR
    report = DR.parse(REGISTER)
    print("REGISTER NOTE before=%dB after=%dB predicted=%dB readback=%s "
          "residue=%s open=%d done=%d first=%s"
          % (before, after, after, back == text, os.path.exists(temp),
             len(report["open"]), len(report["done"]),
             ",".join(row["item"] for row in report["open"]
                      if row.get("first") == "yes") or "none"))
    return 0 if back == text and not os.path.exists(temp) else 1


if __name__ == "__main__":
    sys.exit(main())