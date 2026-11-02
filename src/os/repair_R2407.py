"""R2407 repair: move the R2395 line the R2405 fold left behind.

The R2405 fold cut after `R2395 tokens:`, which is where R2395's ledger ended
but NOT where its block ended - R2395 appended its closeout disclosures after
the ledger, so that one item stayed in the live log while the round's ledger
moved into logs/state-log-archive-2026-11.md. The ledger coverage law then
read live R2395 as a round without a ledger, which is what three suites
reported at R2407.

This repair moves that orphan line back beside its round, in the archive,
verbatim, and then removes it from the live log so the live first item is a
true block boundary. Nothing is rewritten: the archive only grows, and the
live log loses exactly one item, proved by parse and by the item count.

Read-only proof before any write: the item is the one named, the archive does
not already carry it, and the live log parses. Dry run by default.

Stdlib only, ASCII source, no network, no clock.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

ROUND = "R2395"
MARKER = "closeout disclosures"
HEADER = ("# --- 2026-11-03 R2407 repair: the R2395 closeout disclosure line "
          "that the R2405 fold left behind (appended verbatim here, then "
          "removed from the live log so the round is not split) ---")


class RepairError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def find_item(log):
    """The one live item that belongs to R2395 by its own header."""
    hits = [index for index, line in enumerate(log)
            if ROUND in line and MARKER in line]
    if len(hits) != 1:
        raise RepairError("E_RP07_NOT_ONE",
                          "expected one %s item, measured %d"
                          % (ROUND, len(hits)))
    return hits[0]


def main(argv):
    execute = "--execute" in argv
    path = SF.state_path(REPO)
    raw, state = SF.read_state(path)
    log = state["log"]
    index = find_item(log)
    line = log[index]
    archive = os.path.join(REPO, "logs", "state-log-archive-2026-11.md")
    with io.open(archive, "r", encoding="utf-8") as handle:
        before_archive = handle.read()
    if line in before_archive:
        raise RepairError("E_RP07_ALREADY_ARCHIVED",
                          "the archive already carries this line")
    text = raw.decode("utf-8")
    layout = SF.split_layout(text, len(log))
    if layout is None:
        raise RepairError("E_RP07_BAD_LAYOUT", "log lines do not match")
    print("item index %d of %d, %d bytes; archive %d bytes"
          % (index, len(log), len(line.encode("utf-8")),
             len(before_archive.encode("utf-8"))), flush=True)
    if not execute:
        print("DRY: nothing written", flush=True)
        return 0
    appended = SF.append_archive(archive, HEADER, [line], allow_create=False)
    drop = layout["item_index"][index]
    kept = layout["lines"][:drop] + layout["lines"][drop + 1:]
    new_text = layout["newline"].join(kept)
    temp = path + ".r2407.tmp"
    with io.open(temp, "wb") as handle:
        handle.write(new_text.encode("utf-8"))
    os.replace(temp, path)
    with io.open(path, "rb") as handle:
        post_raw = handle.read()
    post = json.loads(post_raw.decode("utf-8"))
    if len(post["log"]) != len(log) - 1:
        raise RepairError("E_RP07_LEN", "live log is %d items, expected %d"
                          % (len(post["log"]), len(log) - 1))
    if post["log"][:index] != log[:index] or \
            post["log"][index:] != log[index + 1:]:
        raise RepairError("E_RP07_ORDER", "the live log changed elsewhere")
    print("moved %d bytes to the archive, live log %d -> %d items, "
          "state %d -> %d bytes, appendix %d bytes, sha16 %s"
          % (len(line.encode("utf-8")), len(log), len(post["log"]),
             len(raw), len(post_raw), appended["appendix_bytes"],
             appended["sha16"]), flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except RepairError as exc:
        sys.stderr.write("%s\n" % exc.code)
        sys.exit(2)