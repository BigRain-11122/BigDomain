"""R2382 board: stamp the claimed tech row, seed one REAL measured gap row.

The claimed row is state/queue/tech.md:428 (AC-RNP1..AC-RNP6). Stamping it
drops tech claimable to 9 against the floor of 10, so one real gap row is
seeded from a seam this window MEASURED on a throwaway world before writing
it: a declaration whose bytes carry CRLF line endings reads PLANNED and is
rewritten to LF as PINNED, so a semantically identical declaration is not a
NOOP and the byte comparison silently rewrites a file it should leave alone.

One atomic replace, predicted size proven, read-back, no temp residue.
ASCII source, stdlib only, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

STAMP_OLD = "- [ ] P2 tech seed (R2372, from this window own measured seam):"
STAMP_NEW = ("- [x] [done 2026-11-02 R2382] P2 tech seed (R2372, from this "
             "window own measured seam):")

SEED = (
    "- [ ] P2 tech seed (R2382, from this window own measured seam): "
    "`src/os/repin_noop_eol_dialect.py` - the NOOP is decided by BYTES, which "
    "is right about content and wrong about transport: a declaration whose "
    "text is exactly the composition but whose line endings are CRLF reads "
    "PLANNED and `--execute` rewrites it to LF as PINNED. Measured this window "
    "on a throwaway world (27 CRLF pairs): dry=PLANNED, execute=PINNED, the "
    "file rewritten with crlf 27 -> 0 - so a semantically identical "
    "declaration is written where nothing needed writing, and no reader can "
    "tell that rewrite from a real re-pin. Product: the comparison owns the "
    "EOL dialect explicitly - the composition is compared NORMALISED "
    "(line endings only), and a declaration that differs solely by EOL reads "
    "NOOP with no byte written, while a declaration that differs in CONTENT "
    "still reads PLANNED and still writes. Criteria AC-RNED1..AC-RNED6 "
    "pre-registered HERE BEFORE any code: AC-RNED1 a CRLF declaration whose "
    "content equals the composition reads NOOP with the whole world map "
    "unchanged (no rewrite, no temp); AC-RNED2 an LF declaration keeps "
    "today's readings byte for byte (NOOP, PLANNED and PINNED text "
    "unchanged); AC-RNED3 a declaration that differs in CONTENT still reads "
    "PLANNED and still rewrites, proving the comparison is content-based and "
    "not a blanket CRLF answer; AC-RNED4 the shipped CLI and the wire agree "
    "over the CRLF declaration (parity AGREES) and neither reports a write; "
    "AC-RNED5 the normalisation lives in ONE place and a patched normaliser "
    "moves both faces; AC-RNED6 pure ASCII, stdlib only, zero network, no "
    "clock, plus its own reconcile label. Five anchors zero-occupancy at HEAD "
    "2026-11-02: repin_noop_eol_dialect, AC-RNED, E_RNED, "
    "os-repin-noop-eol-dialect, test_repin_noop_eol_dialect."
)


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if STAMP_NEW in text:
        print("ALREADY-STAMPED")
        return 1
    if text.count(STAMP_OLD) != 1:
        print("STAMP TARGET COUNT %d" % text.count(STAMP_OLD))
        return 1
    stamped = text.replace(STAMP_OLD, STAMP_NEW)
    if not stamped.endswith("\n"):
        stamped += "\n"
    after = stamped + SEED + "\n"
    predicted = len(after.encode("utf-8"))
    tmp = QUEUE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(after)
    os.replace(tmp, QUEUE)
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    measured = len(back.encode("utf-8"))
    residue = os.path.exists(tmp)
    print("before=%dB predicted=%dB measured=%dB match=%s residue=%s"
          % (len(text.encode("utf-8")), predicted, measured,
             back == after, residue))
    return 0 if back == after and not residue else 1


if __name__ == "__main__":
    sys.exit(main())