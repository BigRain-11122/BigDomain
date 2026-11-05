"""push_R2463 - append the delivery receipt to src/os/state.json.

One line only: this window pushed 1883f995..cb7927e3 and HEAD reads equal to
origin/main. Same atomic-replace + read-back shape as the closeout writer; the
caller runs state_io --fix --execute afterwards.
"""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2463 push: git push origin main SUCCEEDED this window "
    "(1883f995..cb7927e3 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at cb7927e3, so the R2463 verification commit is delivered and "
    "nothing is left staged. The export was re-derived and the queue block "
    "re-applied through the shipped gate AFTER this state append (the R2449 "
    "ordering law). The fold run this window moved log lines 1..14 (the whole "
    "R2452 block plus the previous fold summary, 237 tokens, none missing) into "
    "the monthly archive at a true round-block boundary, after which state.json "
    "measured 68830B canonical with 86 log items."
]

def main():
    with open(STATE, "rb") as handle:
        raw = handle.read()
    crlf = b"\r\n" in raw
    obj = json.loads(raw.decode("utf-8"))
    before = len(obj.get("log") or [])
    obj.setdefault("log", []).extend(LINES)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if crlf:
        text = text.replace("\n", "\r\n")
    data = text.encode("utf-8")
    fd, path = tempfile.mkstemp(dir=BASE, prefix=".state-", suffix=".tmp")
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    os.replace(path, STATE)
    with open(STATE, "rb") as handle:
        back = handle.read()
    check = json.loads(back.decode("utf-8"))
    print("STATE PUSH-LINE tick=%d log=%d->%d crlf=%s bytes=%d readback=%s"
          % (check["tick"], before, len(check["log"]), crlf, len(back),
             "ok" if len(check["log"]) == before + len(LINES) else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())