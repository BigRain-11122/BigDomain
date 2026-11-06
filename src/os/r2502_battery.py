"""R2502 battery: launch the shipped stream detached, then wait with heartbeats.

Detached so this shell call cannot be cancelled for silence, and the wait loop
prints a line a minute so the caller's own watchdog stays fed. Reads the
verdict out of the evidence file instead of quoting anything.
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
REPO = os.path.dirname(SRC)
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2502.log")
PIDFILE = os.path.join(REPO, "logs", "battery-R2502.pid")
STREAM = os.path.join(HERE, "battery_stream.py")
FLAGS = 0x08000000  # CREATE_NO_WINDOW: no console child, and no detach loss
DIAG = os.path.join(REPO, "logs", "battery-R2502.diag.log")


def main():
    if os.path.exists(EVIDENCE):
        os.remove(EVIDENCE)
    diag = open(DIAG, "wb")
    proc = subprocess.Popen([sys.executable, "-u", STREAM, "--evidence",
                             EVIDENCE], cwd=REPO, creationflags=FLAGS,
                            stdin=subprocess.DEVNULL, stdout=diag,
                            stderr=subprocess.STDOUT)
    with open(PIDFILE, "w", encoding="ascii", newline="\n") as handle:
        handle.write("%d\n" % proc.pid)
    print("LAUNCHED pid=%d evidence=%s" % (proc.pid, EVIDENCE), flush=True)
    deadline = time.time() + 2400
    started = time.time()
    while time.time() < deadline:
        time.sleep(60)
        size = os.path.getsize(DIAG) if os.path.exists(DIAG) else 0
        alive = proc.poll() is None
        print("WAIT t+%ds progress=%dB alive=%s"
              % (int(time.time() - started), size, alive), flush=True)
        if not alive:
            break
    if not os.path.exists(EVIDENCE):
        print("VERDICT NO-EVIDENCE")
        return 3
    text = open(EVIDENCE, encoding="utf-8", errors="replace").read()
    tail = [line for line in text.splitlines() if line.startswith("RUNNER ")]
    print("EVIDENCE bytes=%d utf8=%s crlf=%d"
          % (len(text.encode("utf-8")),
             "ok" if "\ufffd" not in text else "replacement-chars",
             open(EVIDENCE, "rb").read().count(b"\r\n")))
    print("VERDICT %s" % (tail[-1] if tail else "NO-RUNNER-LINE"))
    return 0 if tail and tail[-1].startswith("RUNNER PASS") else 1


if __name__ == "__main__":
    sys.exit(main())