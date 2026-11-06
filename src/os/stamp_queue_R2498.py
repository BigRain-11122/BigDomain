"""stamp_queue_R2498 - close the claimed row, carry the battery, update boards."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
BACKLOG = os.path.join(BASE, "backlog.md")

ROW_PREFIX = "- [ ] P2 tech seed (R2497, from this window own measured limit): `src/os/export_consistency_queue_face.py`"
DONE_PREFIX = "- [x] [done 2026-11-07 R2498] P2 tech seed (R2497, from this window own measured limit): `src/os/export_consistency_queue_face.py`"

DISCHARGE = (
    "  DISCHARGED R2498 (line 533, AC-ECQF1..AC-ECQF6 pinned at R2497 BEFORE "
    "any code): src/os/export_consistency_queue_face.py plus its suite shipped "
    "and registered as os-export-consistency-queue-face(6). read() asks "
    "check_export_consistency.check and queue_export_freshness_gate.check at "
    "CALL time (both proved by patching the shipped readings and watching the "
    "composed result move) and publishes the queue verdict BESIDE the "
    "twenty-one base lines: a doctored document reads DRIFT naming queue:tech "
    "and the drifted section fields while the base twenty-one stay green, and "
    "a CURRENT document reads AGREE at today exit code with exactly one "
    "additional line. CLI writes LF-only bytes through the stdout buffer, so a "
    "capture cannot inherit CRLF. LIVE: the real export carried a stale queue "
    "block at open and the twenty-one checks read 21/21 PASS, which is the "
    "blind spot this face now names."
)

BACKLOG_LINE = (
    "- [ ] [carried 2026-11-07 R2498] R2499 first item: THE BATTERY ON THE "
    "COMMITTED TREE, zero product edits until green (the R2168 mixed-tree "
    "rule), target re-pre-registered by importing reconcile_all.SUITES after "
    "this window (578 suites / 4444 criteria). R2497 carried this to R2498 and "
    "the debt gate read CLAIM-FIRST product-face-R2496 with no battery row on "
    "the register, so the product byte went first again and the battery is "
    "carried a second time - disclosed, not hidden.\n"
)


def rewrite(path, transform):
    with io.open(path, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8-sig")
    new = transform(text)
    if new == text:
        raise SystemExit("E_STAMP_NO_CHANGE %s" % os.path.basename(path))
    payload = new.encode("utf-8")
    tmp = path + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, path)
    with io.open(path, "rb") as handle:
        back = handle.read().decode("utf-8-sig")
    if back != new:
        raise SystemExit("E_STAMP_READBACK %s" % os.path.basename(path))
    return len(raw), len(payload)


def close_row(text):
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(ROW_PREFIX):
            lines[index] = DONE_PREFIX + line[len(ROW_PREFIX):]
            lines.insert(index + 1, DISCHARGE)
            return "\n".join(lines)
    raise SystemExit("E_STAMP_ROW_NOT_FOUND")


def carry_battery(text):
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("- [ ] [carried 2026-11-06 R2497]"):
            lines[index] = BACKLOG_LINE.rstrip("\n")
            return "\n".join(lines)
    raise SystemExit("E_STAMP_CARRIED_ROW_NOT_FOUND")


def main():
    before, after = rewrite(TECH, close_row)
    print("tech.md closed bytes %d -> %d" % (before, after))
    before, after = rewrite(BACKLOG, carry_battery)
    print("backlog.md carried bytes %d -> %d" % (before, after))


if __name__ == "__main__":
    main()