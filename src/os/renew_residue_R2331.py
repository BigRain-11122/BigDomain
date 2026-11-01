"""R2331 residue renewal: the triage declaration's window closed at R2330.

Measured at open: residue_triage read residue=195 triaged=0 untriaged=195
verdict=RESIDUE, because every entry carried until=R2330 and the R2331 fold
moved whole round blocks into the archive (the fold-creates-residue law). The
declaration is the R2310 pin, and its own expiry law says an expired entry
returns to the debt - so the honest operation is ONE new declaration derived
from ONE live reading, not a hand splice of 195 rows.

The generator shape and the stable text writer are imported from the R2310
pinner (no second wheel); only the declaring round and the window move. The
write is one atomic replace with a predicted byte count, a read-back proof and
a re-read through the reader itself, which must answer TRIAGED.

Pure ASCII, stdlib only, no network, no clock.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import closeout_R2310 as PIN  # noqa: E402
import residue_triage as RT  # noqa: E402
import stamp_residue as SR  # noqa: E402

DECLARED_BY = 2331
UNTIL = 2350
REASON = ("renewed at R2331: the R2310 window closed at R2330, so every round "
          "was read from the live stamp_residue table once more and accepted "
          "at its reported status until R2350")


def build(root):
    """One declaration body, derived from one live reading only."""
    report = SR.read(root)
    entries = []
    for row in report["rounds"]:
        entries.append({"round": int(row["round"]),
                        "status": row["status"],
                        "declared_by": "R%d" % DECLARED_BY,
                        "reason": "reviewed at R%d at its live status"
                                  % DECLARED_BY,
                        "until": UNTIL})
    entries.sort(key=lambda entry: entry["round"])
    return {"declared_by": "R%d" % DECLARED_BY, "reason": REASON,
            "entries": entries}


def main():
    path = os.path.join(ROOT, RT.DECLARATION_PATH)
    before = os.path.getsize(path)
    body = build(ROOT)
    text = PIN.to_text(body)
    predicted = len(text.encode("utf-8"))
    tmp = path + ".tmp-r2331r"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    written = os.path.getsize(tmp)
    if written != predicted:
        os.remove(tmp)
        raise SystemExit("E_RENEW_PREDICT %d != %d" % (written, predicted))
    json.loads(io.open(tmp, encoding="utf-8").read())
    os.replace(tmp, path)
    if os.path.exists(tmp):
        raise SystemExit("E_RENEW_TEMP")
    back = os.path.getsize(path)
    report = RT.read(ROOT, "R%d" % DECLARED_BY)
    print("residue before=%dB after=%dB entries=%d verdict=%s residue=%d "
          "triaged=%d untriaged=%d expired=%d"
          % (before, back, len(body["entries"]), report["verdict"],
             len(report["residue"]), report["triaged"], report["untriaged"],
             report["expired"]))
    if report["verdict"] != "TRIAGED" or report["untriaged"]:
        raise SystemExit("E_RENEW_NOT_TRIAGED")


if __name__ == "__main__":
    main()