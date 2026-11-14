"""Negative/positive controls for tools/adoption_preflight.py.

Builds private worlds in tmp/preflight-ctrl/ so the gate is proven in both
directions instead of only being read. Dead pid 4 is used so the pid gate reads
GONE without depending on a clock.
"""

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE = os.path.join(ROOT, "tmp", "preflight-ctrl")
TOOL = os.path.join(ROOT, "tools", "adoption_preflight.py")


def registry():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_ra_ctrl", os.path.join(ROOT, "src", "sandbox", "reconcile_all.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [(r[0], int(r[2])) for r in mod.SUITES]


def world(tag, rows, closing, stream_closing=None, pid=4):
    d = os.path.join(BASE, tag)
    os.makedirs(d, exist_ok=True)
    body = "".join(
        "PASS suite %s exit=0 pass-lines=6 fail-lines=0 criteria=%d 0.1s\n" % (n, c)
        for n, c in rows)
    tail = "" if closing is None else "BATTERY rc=%d 1.0s\n" % closing
    ev = os.path.join(d, "evidence.log")
    with open(ev, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body + tail)
    st = os.path.join(d, "stream.log")
    sc = closing if stream_closing is None else stream_closing
    with open(st, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body + ("" if sc is None else "  | BATTERY rc=%d 1.0s\n" % sc))
    pf = os.path.join(d, "battery.pid")
    with open(pf, "w", encoding="utf-8") as fh:
        fh.write(str(pid))
    return st, pf, ev


def run(tag, args, expect_rc):
    r = subprocess.run([sys.executable, TOOL] + args,
                       capture_output=True, text=True, cwd=ROOT)
    verdict = [l for l in r.stdout.splitlines() if l.startswith("VERDICT")]
    line = verdict[0] if verdict else "NO VERDICT LINE"
    ok = r.returncode == expect_rc
    print("%s %-28s rc=%d expect=%d  %s"
          % ("PASS" if ok else "FAIL", tag, r.returncode, expect_rc, line))
    return ok


def main():
    rows = registry()
    total = sum(c for _, c in rows)
    print("registry suites=%d criteria=%d" % (len(rows), total))
    checks = []

    st, pf, ev = world("good", rows, 0)
    checks.append(run("positive-full-green", ["--stream", st, "--pidfile", pf, "--evidence", ev], 0))

    st, pf, ev = world("rc1", rows, 1)
    checks.append(run("negative-closing-rc-1", ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))

    st, pf, ev = world("noev", rows, None)
    os.remove(ev)
    checks.append(run("negative-no-evidence", ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))

    st, pf, ev = world("crlf", rows, 0)
    with open(ev, "ab") as fh:
        fh.write(b"\r\n")
    checks.append(run("negative-crlf-in-evidence", ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))

    st, pf, ev = world("short", rows[:-1], 0)
    checks.append(run("negative-missing-suite", ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))

    st, pf, ev = world("foreign", rows[:-1] + [("os-foreign-name", 6)], 0)
    checks.append(run("negative-foreign-name", ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))

    st, pf, ev = world("alive", rows, 0, pid=os.getpid())
    checks.append(run("negative-pid-alive", ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))

    # Attribution escape hatch: a named fail row is tolerated only when the
    # operator passes --allow-fail-names, and never silently.
    d = os.path.join(BASE, "attrib")
    os.makedirs(d, exist_ok=True)
    rows_text = "".join(
        "PASS suite %s exit=0 pass-lines=6 fail-lines=0 criteria=%d 0.1s\n" % (n, c)
        for n, c in rows[1:])
    rows_text += "FAIL suite %s exit=1 pass-lines=5 fail-lines=1 criteria=%d 0.1s\n" % (rows[0][0], rows[0][1])
    ev = os.path.join(d, "evidence.log")
    open(ev, "w", encoding="utf-8", newline="\n").write(rows_text + "BATTERY rc=0 1.0s\n")
    st = os.path.join(d, "stream.log")
    open(st, "w", encoding="utf-8", newline="\n").write(rows_text + "  | BATTERY rc=0 1.0s\n")
    pf = os.path.join(d, "battery.pid")
    open(pf, "w", encoding="utf-8").write("4")
    checks.append(run("negative-unattributed-fail",
                      ["--stream", st, "--pidfile", pf, "--evidence", ev], 2))
    checks.append(run("positive-attributed-fail",
                      ["--stream", st, "--pidfile", pf, "--evidence", ev,
                       "--allow-fail-names", rows[0][0]], 0))

    print("SUMMARY %s pass=%d/%d"
          % ("PASS" if all(checks) else "FAIL", sum(1 for c in checks if c), len(checks)))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
