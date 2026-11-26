"""AC-BFL1 (R3525): landing a board page and re-deriving the CEO face are ONE write.

R3524 closed this birth-site gap for one producer (tools/battery_shard_report.py).
The census this round measured the same shape on the other writers of
export_round.BOARD_PAGES. A board page can never become `latest_artifact`, so
landing one changes nothing visible on the CEO face unless the writer re-derives
it: the skipped audit silently ages, and the three suites that grade it redden on
the next window that looks. R3523 paid exactly that.

This module is the one definition those writers share. It takes the root
explicitly, so a writer running against a private world derives that world's face
and never the real repo's, and the shipped writer src/os/export_round.py runs in
THIS process rather than in a scheduled child.

Refusals are named, never raised: the page pair is already on disk when this
runs, so the caller's exit code stays its own.
"""

import datetime
import os
import sys


def refresh_export_face(root, stamp=None):
    """Re-derive docs/status-export.json for `root`. Returns (ok, note, proof).

    `stamp` is accepted for tests and pinned replays; the default is a second
    precision local ISO-8601 stamp, the same shape export_round publishes.
    """
    src_os = os.path.join(root, "src", "os")
    if src_os not in sys.path:
        sys.path.insert(0, src_os)
    try:
        import export_round as ER
    except Exception as exc:  # a private world may carry no OS writer at all
        return (False, "E_BFL_WRITER_MISSING %s: %s"
                % (type(exc).__name__, exc), {})
    if stamp is None:
        stamp = datetime.datetime.now().astimezone().replace(
            microsecond=0).isoformat()
    try:
        ok, derived, proof = ER.write(root, stamp)
    except Exception as exc:
        return (False, "E_BFL_FACE_REFUSED %s: %s"
                % (type(exc).__name__, exc), {})
    gate = (proof or {}).get("gate")
    if not ok or gate != "CURRENT":
        return (False, "E_BFL_FACE_UNPROVEN ok=%s queue=%s" % (ok, gate),
                proof or {})
    return True, "", {"stamp": stamp,
                      "bytes": (proof or {}).get("bytes"),
                      "latest": (derived or {}).get("latest")}
