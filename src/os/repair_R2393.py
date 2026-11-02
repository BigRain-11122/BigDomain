"""Repair the two birth-site defects the R2393 battery measured (R2393).

Both reds were real and neither was caused by this window's own edits - the
tree was clean at HEAD 3535cc1a before the run:

  1. state.json carried the R2392 ledger item as
     "2026-11-02 R2392 tokens: local=~38k ..." while ledger_lines.py owns the
     law LEDGER_PREFIX_RE = ^R(\\d{3,5}) tokens:, i.e. a ledger line may not
     carry a date prefix (a NARRATIVE line may). The round therefore read
     rounds_without_ledger=2392 and the four ledger suites went red.
     Repair: drop exactly that one date prefix, 11 bytes, nothing else.

  2. qa/repin-noop-eol-dialect-live-R2388.log was written with the child CLI
     stdout embedded verbatim, so it carried 1 CRLF, 4 LF and 2 bare CR - a
     mixed dialect the census reads as class=other and flags as new-dialect.
     Repair: run_identity.normalize over the whole text (the only allowed
     normalisation) through one atomic replace, payload line set proven equal.

Both repairs predict their byte delta first and prove it by read-back.
Stdlib only, ASCII source, no clock, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import run_identity as RI  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
CENSUS_LOG = os.path.join(REPO, "qa", "repin-noop-eol-dialect-live-R2388.log")
PREFIX = "2026-11-02 "
ANCHOR = "2026-11-02 R2392 tokens:"


def _replace(path, text):
    """One atomic replace from a same-directory temp, then a read-back."""
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def repair_state(dry_run=True):
    """Surgical edit: drop the date prefix on that ONE item, every other
    byte and the canonical CRLF/16-space layout left untouched."""
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        before_text = handle.read()
    before_bytes = len(before_text.encode("utf-8"))
    payload = json.loads(before_text)
    hits = [index for index, item in enumerate(payload["log"])
            if item.startswith(ANCHOR)]
    if len(hits) != 1:
        raise SystemExit("REFUSED: %d items start with %r"
                         % (len(hits), ANCHOR))
    if before_text.count(ANCHOR) != 1:
        raise SystemExit("REFUSED: the anchor text appears %d times"
                         % before_text.count(ANCHOR))
    after_text = before_text.replace(ANCHOR, ANCHOR[len(PREFIX):], 1)
    expected = dict(payload)
    fixed = list(payload["log"])
    fixed[hits[0]] = fixed[hits[0]][len(PREFIX):]
    expected["log"] = fixed
    predicted = before_bytes - len(PREFIX.encode("utf-8"))
    print("STATE before_bytes=%d predicted=%d crlf=%d"
          % (before_bytes, predicted, before_text.count("\r\n")), flush=True)
    if dry_run:
        print("STATE wrote=no payload_equal=%s"
              % (json.loads(after_text) == expected), flush=True)
        return predicted, before_bytes
    written = _replace(STATE, after_text)
    measured = len(written.encode("utf-8"))
    reread = json.loads(written)
    same = reread == expected
    print("STATE after_bytes=%d matches_prediction=%s payload_equal=%s crlf=%d"
          % (measured, measured == predicted, same, written.count("\r\n")),
          flush=True)
    if measured != predicted or not same:
        raise SystemExit("REFUSED: the write missed its prediction")
    return measured, before_bytes


def repair_census_log(dry_run=True):
    with io.open(CENSUS_LOG, "r", encoding="utf-8", newline="") as handle:
        before_text = handle.read()
    before_bytes = len(before_text.encode("utf-8"))
    raw = before_text.encode("utf-8")
    after_text = RI.normalize(before_text)
    predicted = len(after_text.encode("utf-8"))
    print("CENSUS before_bytes=%d predicted=%d crlf=%d bare_cr=%d"
          % (before_bytes, predicted, raw.count(b"\r\n"),
             raw.count(b"\r") - raw.count(b"\r\n")), flush=True)
    before_lines = [line for line in before_text.replace("\r\n", "\n")
                    .replace("\r", "\n").split("\n")]
    after_lines = after_text.split("\n")
    payload_equal = before_lines == after_lines
    if dry_run:
        print("CENSUS wrote=no payload_equal=%s" % payload_equal, flush=True)
        return predicted, before_bytes
    written = _replace(CENSUS_LOG, after_text)
    measured = len(written.encode("utf-8"))
    raw_after = written.encode("utf-8")
    print("CENSUS after_bytes=%d matches_prediction=%s payload_equal=%s "
          "crlf=%d bare_cr=%d"
          % (measured, measured == predicted, payload_equal,
             raw_after.count(b"\r\n"),
             raw_after.count(b"\r") - raw_after.count(b"\r\n")), flush=True)
    if measured != predicted or not payload_equal:
        raise SystemExit("REFUSED: the census log repair missed its prediction")
    return measured, before_bytes


def main(argv):
    dry_run = "--execute" not in argv
    repair_state(dry_run)
    repair_census_log(dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))