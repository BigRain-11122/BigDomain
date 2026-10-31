# stamp_exempt_seed_R2280.py - write the accepted stamp-exemption record
# This is a ONE-OFF window action, not a reader: src/os/queue_done_stamp_exempt.py
# is the reader and it writes nothing. The generator takes the live gate
# reading, derives the stable identity of every closed row the gate reports as
# debt, and writes ONE pinned declaration named at R2280 with a dated reason
# per row. Nothing is invented: every entry comes from a row that exists now,
# and an entry that later matches no live row reads as unmatched (inert)
# rather than exempting anything. A row created AFTER this declaration is not
# covered, which is the whole point of the file.
#
# ASCII source, stdlib only, no clock, deterministic ordering.

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import queue_done_stamp as QDS  # noqa: E402
import queue_done_stamp_exempt as SX  # noqa: E402

ROUND = "R2280"
NOTE = ("Every entry below is a queue row that was already CLOSED when the "
        "window-stamp law landed at R2278. The gate cannot go green on them "
        "without rewriting history or widening itself, so they are accepted "
        "here as a dated record. A closed row created after R2280 is NOT "
        "covered: it must carry a [done YYYY-MM-DD R<n>] stamp.")


def reason_for(status):
    return ("%s: closed before the window-stamp law landed at R2278; no "
            "window can be recovered without rewriting the row" % status)


def build(root):
    gate = QDS.audit_root(root)
    entries = []
    seen = set()
    for bad in gate["violations"]:
        queue = SX.queue_of_path(bad["file"])
        identity = SX.identity_of(bad.get("excerpt", ""))
        if (queue, identity) in seen:
            raise SystemExit("E_SEED_DUP: %s:%s" % (queue, identity))
        seen.add((queue, identity))
        entries.append({"queue": queue, "identity": identity,
                        "declared": ROUND,
                        "reason": reason_for(bad["status"])})
    entries.sort(key=lambda item: (item["queue"], item["identity"]))
    return gate, entries


def render(entries):
    lines = ["{", '  "note": %s,' % json.dumps(NOTE, ensure_ascii=True),
             '  "exemptions": [']
    for index, entry in enumerate(entries):
        body = json.dumps(entry, ensure_ascii=True, sort_keys=False)
        tail = "," if index + 1 < len(entries) else ""
        lines.append("    %s%s" % (body, tail))
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main(argv):
    root = REPO
    if len(argv) == 1:
        root = argv[0]
    gate, entries = build(root)
    body = render(entries)
    if not body.isascii():
        raise SystemExit("E_SEED_ASCII: declaration is not ASCII")
    path = os.path.join(root, SX.DECL_REL)
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        raise SystemExit("E_SEED_DIR: %s missing" % directory)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body:
        raise SystemExit("E_SEED_READBACK: declaration does not read back")
    print("WROTE %s entries=%d bytes=%d gate_violations=%d gate_verdict=%s"
          % (SX.DECL_REL.replace(os.sep, "/"), len(entries), len(body),
             gate["violation_count"], gate["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))