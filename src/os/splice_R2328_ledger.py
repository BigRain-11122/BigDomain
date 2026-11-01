"""R2328 ledger-prefix splice: raw-text repair, no reserialisation.

The R2327 closeout emitted its round ledger item as 'tokens: local=1 ...'
without the round prefix, so the pinned '^R<n> tokens:' law cannot see it
and ledger_lines read rounds_without_ledger=2327 VERDICT DIRTY, gating the
whole ledger family red (AC-LGR8, AC-LGA7, AC-LGA8, AC-LGB8, AC-LGN8).

The fix is one insertion of six bytes inside one JSON string, so the rest
of the file stays BYTE-IDENTICAL - no reserialisation, which could reorder
or reformat a 67KB declaration for a one-word defect. Predicted delta is
+6 bytes, one atomic replace, a read-back proof, JSON parsed on both sides.
"""

import io
import json
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "src", "os", "state.json")

OLD = 'tokens: local=1 api=0 api_reason=none'
NEW = 'R2327 ' + OLD


def main():
    raw = io.open(P, encoding="utf-8", newline="").read()
    hits = raw.count(OLD)
    if hits != 1:
        raise SystemExit("E_SPLICE_COUNT %d" % hits)
    after = raw.replace(OLD, NEW, 1)
    before = os.path.getsize(P)
    predicted = len(after.encode("utf-8"))
    if predicted - before != len("R2327 "):
        raise SystemExit("E_SPLICE_DELTA %+d" % (predicted - before))
    old_doc = json.loads(raw)
    new_doc = json.loads(after)
    if len(old_doc["log"]) != len(new_doc["log"]):
        raise SystemExit("E_SPLICE_LOG_LEN")
    changed = [i for i in range(len(old_doc["log"]))
               if old_doc["log"][i] != new_doc["log"][i]]
    if len(changed) != 1:
        raise SystemExit("E_SPLICE_CHANGED %r" % changed)
    print("before=%dB predicted=%dB delta=%+d changed_item=%d"
          % (before, predicted, predicted - before, changed[0] + 1))
    tmp = P + ".tmp-r2328b"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(after)
    written = os.path.getsize(tmp)
    if written != predicted:
        os.remove(tmp)
        raise SystemExit("E_SPLICE_PREDICT %d != %d" % (written, predicted))
    os.replace(tmp, P)
    if os.path.exists(tmp):
        raise SystemExit("E_SPLICE_TEMP")
    back = json.loads(io.open(P, encoding="utf-8", newline="").read())
    if not back["log"][changed[0]].startswith(NEW):
        raise SystemExit("E_SPLICE_READBACK")
    print("readback=%dB log_len=%d tick=%s"
          % (os.path.getsize(P), len(back["log"]), back.get("tick")))


if __name__ == "__main__":
    main()