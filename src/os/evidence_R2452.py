"""Evidence for the R2452 product window (AC-SEWS1..AC-SEWS6).

Two measured faces, both written through Python as one utf-8 LF body (never a
PowerShell redirect - the R2451 defect), each proved by reading the bytes back:

1. the shipped capture ritual over the scope suite with three adjacent suites,
2. a LIVE capture of the shipped CLI over the real export, so the reading the
   reader opens is the reading this window measured.

Run with --execute to write; the default is a dry run.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import evidence_capture as EVC  # noqa: E402

ROUND = "R2452"
SUITE = os.path.join("src", "os", "test_status_export_writer_transport_scope.py")
ADJACENT = [os.path.join("src", "os", "test_status_export_writer_dialect_wire.py"),
            os.path.join("src", "os", "test_queue_floor_export_face.py"),
            os.path.join("src", "os", "test_queue_export_gate_wire.py")]
MODULE = os.path.join(BASE, "status_export_writer_transport_scope.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
CAPTURE = os.path.join(REPO, "qa", "status-export-writer-transport-scope-R2452.log")
LIVE_LOG = os.path.join(REPO, "qa",
                        "status-export-writer-transport-scope-live-R2452.log")


def write_bytes_atomic(path, data, prefix):
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
    back = io.open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2452_BACK read-back does not match the write")
    return len(back)


def live_body():
    proc = subprocess.run(
        [sys.executable, MODULE, "--check", "--root", REPO,
         "--sample", EXPORT],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=REPO)
    text = proc.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return proc.returncode, text


def main(execute):
    code, body = live_body()
    if not execute:
        print("DRY RUN live_rc=%d live_lines=%d capture=%s"
              % (code, len(body.splitlines()), os.path.basename(CAPTURE)))
        print(body.rstrip())
        return 0
    report = EVC.capture(REPO, ROUND, SUITE, adjacent=ADJACENT,
                         evidence=os.path.relpath(CAPTURE, REPO))
    print(EVC.render(report).rstrip())
    print("CAPTURE bytes=%d" % os.path.getsize(CAPTURE))
    if code not in (0, 2):
        raise SystemExit("E_R2452_LIVE rc=%d" % code)
    size = write_bytes_atomic(LIVE_LOG, body.encode("utf-8"), ".r2452-live-")
    back = io.open(LIVE_LOG, "rb").read()
    print("LIVE bytes=%d crlf=%d lone_lf=%d rc=%d readback=%s"
          % (size, back.count(b"\r\n"),
             back.replace(b"\r\n", b"").count(b"\n"), code,
             "ok" if back == body.encode("utf-8") else "MISMATCH"))
    print(body.rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))