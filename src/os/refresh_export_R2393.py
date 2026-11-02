"""Re-derive the one stale counter the R2393 repair invalidated (R2393).

Measured, not guessed: after repair_R2393 dropped the date prefix from the
R2392 ledger item, check_export_consistency recomputed
self_drive.log_lines_in_window = 7 while docs/status-export.json still stored
8, because the counter counts state log items that carry a date prefix inside
the window and one item no longer does. Nothing else in the export disagrees.

The value written here is the checker's own derivation (recompute()), never a
hand number, and the edit is surgical: the stored digit is replaced in place so
the export keeps its LF, its 2-space indent and every other byte.

Stdlib only, ASCII source, no clock, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as C  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")
KEY = "log_lines_in_window"


def main(argv):
    dry_run = "--execute" not in argv
    derived, _state, export, _pat = C.recompute()
    want = derived[KEY]
    stored = export["self_drive"][KEY]
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        before_text = handle.read()
    before_bytes = len(before_text.encode("utf-8"))
    needle = '"%s": %d' % (KEY, stored)
    if before_text.count(needle) != 1:
        raise SystemExit("REFUSED: %r appears %d times"
                         % (needle, before_text.count(needle)))
    after_text = before_text.replace(needle, '"%s": %d' % (KEY, want), 1)
    predicted = len(after_text.encode("utf-8"))
    print("EXPORT key=%s stored=%d recomputed=%d before_bytes=%d "
          "predicted=%d" % (KEY, stored, want, before_bytes, predicted),
          flush=True)
    if dry_run:
        print("EXPORT wrote=no", flush=True)
        return 0
    temp = EXPORT + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(after_text)
    os.replace(temp, EXPORT)
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        written = handle.read()
    measured = len(written.encode("utf-8"))
    payload_ok = json.loads(written)["self_drive"][KEY] == want
    print("EXPORT after_bytes=%d matches_prediction=%s value_now=%d "
          "payload_ok=%s temp_left=%s"
          % (measured, measured == predicted,
             json.loads(written)["self_drive"][KEY], payload_ok,
             os.path.exists(temp)), flush=True)
    if measured != predicted or not payload_ok:
        raise SystemExit("REFUSED: the write missed its prediction")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))