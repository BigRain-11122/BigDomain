"""push_R2464 - append the delivery receipt to src/os/state.json."""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2464 push: git push origin main SUCCEEDED this window "
    "(8e08a44e..89bccb1f main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 89bccb1f, so the R2464 room-picker commit is delivered and "
    "nothing is left staged. The export and the queue block were re-derived and "
    "re-applied AFTER the state append (the R2449 ordering law) and "
    "check_export_consistency reads pass=21 fail=0 VERDICT PASS. The first "
    "commit attempt was refused by the R1650b message gate at 509B against the "
    "500B limit; the message was trimmed and the same staged tree committed, so "
    "no content changed between the refusal and the push."
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