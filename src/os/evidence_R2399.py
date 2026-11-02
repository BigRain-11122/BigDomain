"""R2399 live capture for owner_table_usage_wire.

Writes ONE utf-8 LF evidence file (never a shell redirection) recording the
real tree readings this window measured: the three data-constant false
positives the new notion removes, the two true readings it must keep, the
shipped law's own line before and after, a bad-flag refusal and a missing-path
refusal, plus the module digest before and after to prove nothing moved.

Stdlib only, ASCII source, no clock in the module under test (the capture's
own snapshot is a sha16 of the module bytes).
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
MODULE = os.path.join(BASE, "owner_table_usage_wire.py")
LAW = os.path.join(BASE, "owner_table_parity.py")
OUT = os.path.join(REPO, "qa", "owner-table-usage-wire-live-R2399.log")

FILES = ("evidence_R2372.py", "r2140_fold.py", "retry_naming.py",
         "runner_arg_guard.py", "battery_followup.py")


def run(module, args, cwd=BASE):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, module] + args, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace").strip(), \
        err.decode("utf-8", "replace").strip()


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16], \
            os.path.getsize(path)


def main():
    lines = []
    lines.append("R2399 OWNER TABLE USAGE WIRE live capture (real tree)")
    lines.append("module=%s" % os.path.relpath(MODULE, REPO).replace("\\", "/"))
    before = digest(MODULE)
    lines.append("module_before sha16=%s bytes=%d" % before)
    lines.append("")
    lines.append("-- false positives the new notion removes --")
    for name in FILES[:3]:
        rc, out, _ = run(MODULE, [os.path.join("src", "os", name)], REPO)
        lines.append("rc=%d %s" % (rc, out))
    lines.append("")
    lines.append("-- true readings that must not move --")
    for name in FILES[3:]:
        rc, out, _ = run(MODULE, [os.path.join("src", "os", name)], REPO)
        lines.append("rc=%d %s" % (rc, out))
    lines.append("")
    lines.append("-- the shipped law keeps its own face --")
    rc, out, _ = run(LAW, [os.path.join("src", "os", "runner_arg_guard.py")],
                     REPO)
    lines.append("law rc=%d %s" % (rc, out))
    lines.append("")
    lines.append("-- refusals --")
    rc, out, _ = run(MODULE, ["--nope"], REPO)
    lines.append("bad_flag rc=%d %s" % (rc, out))
    rc, out, _ = run(MODULE, ["src/os/no-such-tool.py"], REPO)
    lines.append("missing rc=%d %s" % (rc, out))
    rc, out, _ = run(MODULE, ["--json", "src/os/battery_followup.py"], REPO)
    lines.append("json rc=%d %s" % (rc, out))
    lines.append("")
    after = digest(MODULE)
    lines.append("module_after sha16=%s bytes=%d" % after)
    lines.append("module_unchanged=%s" % ("yes" if before == after else "no"))
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(OUT, "rb") as handle:
        back = handle.read()
    print("LIVE %s bytes=%d crlf=%d unchanged=%s"
          % (os.path.relpath(OUT, REPO).replace("\\", "/"), len(back),
             back.count(b"\r\n"), "yes" if before == after else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())