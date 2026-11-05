"""push_R2462 - append the delivery receipt to src/os/state.json.

One line only: this window pushed 58237471..3bd91edd and HEAD reads equal to
origin/main. Same atomic-replace + read-back shape as the closeout writer; the
caller runs state_io --fix afterwards because json.dumps re-indents the log.
"""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2462 push: git push origin main SUCCEEDED this window "
    "(58237471..3bd91edd main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 3bd91edd, so the R2462 entry-page commit is delivered and "
    "nothing is left staged. The export and the queue block were re-derived "
    "and re-applied AFTER this state append (the R2449 ordering law).",
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