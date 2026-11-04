"""R2453 post-closeout appends: one state log line and one real tech seed.

Both writes are single atomic replaces with a predicted payload and a byte
read-back. The state append must happen BEFORE the export refresh (the R2449
ordering law), so the export is refreshed by its own driver afterwards.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TECH = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                    "state", "queue", "tech.md")

LOG_LINE = (
    "2026-11-05 R2453 post-closeout measurement, appended rather than edited "
    "in: after export_R2453 refreshed the document, "
    "queue_floor_export_face --check read STALE on the live queue section "
    "(claimable=5,10,10), because the round export driver derives "
    "do/latest/next/results but does not apply the queue face - the same gap "
    "R2452 named one window earlier, now measured twice in a row. Landed "
    "through the shipped gate wire (QUEUE EXPORT GATE verdict=WRITTEN "
    "gate=CURRENT bytes=105964 drifted=(none)), after which the face reads "
    "CURRENT and check_export_consistency reads pass=21 fail=0 VERDICT PASS. "
    "The gap is seeded as a tech row this window rather than named a third "
    "time with no owner."
)

SEED_ROW = (
    "- [ ] P2 tech seed (R2453, from this window own measured limit): "
    "`src/os/export_driver_queue_face.py` - the round export driver re-derives "
    "do / latest / next / results but never applies the queue face, so a "
    "freshly re-derived CEO-visible document can still carry a stale queue "
    "block. MEASURED TWICE: R2452 and R2453 both read "
    "queue_floor_export_face --check STALE immediately after their own export "
    "refresh (claimable=5,10,10) and both had to land the block by hand "
    "through queue_export_gate_wire --execute, after which the face read "
    "CURRENT and check_export_consistency read 21/21 PASS. Product: the export "
    "driver asks the shipped queue face for its section at CALL time and "
    "publishes the gate verdict beside the count, so a stale queue block "
    "cannot survive its own refresh and no operator step is required. "
    "Criteria AC-EDQF1..AC-EDQF6 pre-registered HERE BEFORE any code: "
    "AC-EDQF1 the section written by the driver IS the shipped face own "
    "published reading, asked at CALL time, never a second derivation; "
    "AC-EDQF2 a driver run on the real tree leaves the queue block CURRENT "
    "with the face itself re-reading CURRENT and reporting no drift; "
    "AC-EDQF3 a queue that moved between the reading and the write refuses "
    "with the gate own code and leaves the document byte-identical; "
    "AC-EDQF4 every already-published key of the document keeps its value - "
    "the queue section is refreshed in place, not reordered; AC-EDQF5 the "
    "gate verdict and its byte count are printed by the driver so a refused "
    "or drifted run is visible rather than silent; AC-EDQF6 pure ASCII, "
    "stdlib only, no clock beyond the document own stamp, zero network, own "
    "reconcile label and suite. Four anchors to re-check zero-occupancy at "
    "HEAD before any code: export_driver_queue_face, AC-EDQF, E_EDQF, "
    "os-export-driver-queue-face, test_export_driver_queue_face.\n"
)


def write_atomic(path, data, prefix):
    import tempfile
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    if open(path, "rb").read() != data:
        raise SystemExit("E_R2453A_BACK read-back mismatch")
    return len(data)


def main(execute):
    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if any("R2453 post-closeout measurement" in item for item in payload["log"]):
        raise SystemExit("E_R2453A_LOG already present")
    tech = io.open(TECH, encoding="utf-8", newline="").read()
    if "export_driver_queue_face" in tech:
        raise SystemExit("E_R2453A_SEED already present")

    payload["log"].append(LOG_LINE)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2453A_PAYLOAD canon moved the payload")
    before, after = len(raw), len(tech.encode("utf-8"))
    print("DRY RUN state %dB -> %dB (predicted %dB) tech %dB -> %dB"
          % (before, len(canonical.encode("utf-8")),
             len(canonical.encode("utf-8")), after,
             after + len(SEED_ROW.encode("utf-8"))))
    if not execute:
        return 0
    size = write_atomic(STATE, canonical.encode("utf-8"), ".r2453a-state-")
    print("STATE bytes=%d log_len=%d" % (size, len(payload["log"])))
    if not tech.endswith("\n"):
        tech += "\n"
    wrote = write_atomic(TECH, (tech + SEED_ROW).encode("utf-8"),
                         ".r2453a-tech-")
    print("TECH bytes=%d" % wrote)
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))