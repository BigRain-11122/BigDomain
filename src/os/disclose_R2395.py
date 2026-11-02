"""Append one disclosure item to the R2395 log (R2395)."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

ITEM = (
    "2026-11-03 R2395 closeout disclosures, measured not guessed: (a) the "
    "fold ran TWICE in this window because the first execute pass then tried "
    "a re-pin with a flag the shipped CLI does not take (--declared-by), and "
    "the whole script was re-run instead of only the re-pin step: window 1..17 "
    "took state to 70952B and the second pass moved a further window 1..9 to "
    "63498B, each through state_fold with its own backup "
    "(logs/state-preop-R2395.bak), its own token coverage check and its own "
    "verified append, so no line was lost and the archive holds both headers; "
    "the honest reading is one fold too many, not a damaged log. (b) The "
    "re-pin CLI signature is --round R<n> --until R<n> --reason TEXT and it "
    "ages every live residue round from ONE reading, so --round R2395 pinned "
    "three moved rounds in one call (entries 238 -> 241, 68335B -> 68838B, "
    "dropped=0) and residue_triage now reads TRIAGED 241/241. (c) The derived "
    "counters moved for a structural reason worth naming: self_drive."
    "log_lines_in_window read 23 before the fold and 20 after, because two of "
    "the moved blocks were dated inside the seven-day window - the fold is "
    "what hides them from that counter, and this is disclosed rather than "
    "papered over by editing the number. (d) The registry reading 521 suites / "
    "4102 criteria is a WIRING count: 521 suites is measured off the SUITES "
    "AST (and the live log prints suites=521), while 4102 is the arithmetic "
    "4096 + 6 - no battery has walked this tree since the wiring.")


def main(argv):
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        payload = json.load(handle)
    if ITEM in payload["log"]:
        print("already present")
        return 0
    payload["log"] = list(payload["log"]) + [ITEM]
    text = SIO.canon(json.dumps(payload, indent=2, ensure_ascii=False))
    if "--execute" not in argv:
        print("DRY: would append %d bytes" % len(ITEM.encode("utf-8")))
        return 0
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    print("appended, json_equal=%s items=%d bytes=%d"
          % (back == json.loads(json.dumps(payload)), len(back["log"]),
             len(io.open(STATE, "r", encoding="utf-8", newline="")
                 .read().encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))