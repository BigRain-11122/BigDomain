# battery_R2009.py - R2009 full RUNNER battery driver: runs
# reconcile_all.py via subprocess, streams progress lines to the
# console (keeps the 5-min zero-output kill away), captures all
# output bytes and writes the qa/ evidence log as UTF-8 LF
# (avoids the PS5.1 redirect UTF-16 dialect pitfall; R2006/R2007
# census new-dialect re-anchor face retired by construction).
# ASCII only (encoding discipline).
import io
import os
import subprocess
import sys
import time

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CMD = [sys.executable,
       os.path.join("src", "sandbox", "reconcile_all.py")]
OUT = os.path.join("qa", "reconcile-all-R2009.log")


def main():
    t0 = time.time()
    proc = subprocess.Popen(
        CMD, cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    buf = []
    n = 0
    for raw in proc.stdout:
        line = raw.decode("utf-8", "replace")
        buf.append(line)
        n += 1
        if n % 30 == 0:
            print("progress lines=%d elapsed=%.0fs"
                  % (n, time.time() - t0), flush=True)
    rc = proc.wait()
    text = "".join(buf)
    with io.open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(text)
    tail = text.splitlines()[-12:]
    print("-- battery tail --")
    for ln in tail:
        print(ln.encode("ascii", "replace").decode("ascii"))
    print("battery rc=%d bytes=%d elapsed=%.1fs"
          % (rc, len(text.encode("utf-8")), time.time() - t0))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
