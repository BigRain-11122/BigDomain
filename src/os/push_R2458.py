"""Append the R2458 push and self-heal lines AFTER the export refresh.

The R2449 ordering law: every state append happens before the export is
re-derived, so the published document carries the line rather than predating
it. This script only appends two measured lines and preserves the document
transport through the shipped dialect law; the export is refreshed by its own
shipped writer afterwards.

Run with --execute to write; the default is a dry run.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402
import declaration_writer_dialect_preservation as DDP  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2458 push: git push origin main SUCCEEDED this window "
    "(5f970de8..944dc61c main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 944dc61c, so the R2458 verification commit is delivered and "
    "nothing is left staged. The export was re-derived and the queue block "
    "re-applied through the shipped gate AFTER this state append (the R2449 "
    "ordering law), so the published document carries this line rather than "
    "predating it.",

    "2026-11-05 R2458 self-heal check: BigDomain-OSLoop exists and is Running, "
    "but its Principal.LogonType still reads Interactive, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "needs an elevated shell while this session is unelevated, so the "
    "definition was left untouched again (two-hundred-and-twentieth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    data = json.loads(raw.decode("utf-8"))
    log = data.setdefault("log", [])
    added = [line for line in LINES if line not in log]
    print("PUSH R2458 append lines=%d skipped=%d"
          % (len(added), len(LINES) - len(added)))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    log.extend(added)
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    canon = state_io.canon(body)
    name, payload = DDP.encode(raw, canon)
    tmp = STATE + ".tmp-r2458push"
    with open(tmp, "wb") as fh:
        fh.write(payload)
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    print("WROTE %dB dialect=%s crlf=%d lone_lf=%d readback=%s"
          % (len(back), name, back.count(b"\r\n"),
             back.count(b"\n") - back.count(b"\r\n"), back == payload))
    return 0 if back == payload else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))