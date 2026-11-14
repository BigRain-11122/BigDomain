"""Adoption preflight for a battery leg.

Read-only measurement gate for adopting a battery leg by its evidence path.
Twelve windows (R2739..R2748) each re-derived the same eight measurements by
hand before they could write a verdict; this face answers them in one call and
answers NOT-READY loudly while a leg is still running.

It never writes, never shells out, never touches the network and never reads a
clock: every answer comes from the files it is pointed at plus the registry
imported from src/sandbox/reconcile_all.py.

Usage:
    python tools/adoption_preflight.py --stream logs/battery-X.stream \
        --pidfile logs/battery-X.pid --evidence qa/reconcile-all-X.log

Exit codes:
    0  ADOPT-READY      every gate measured true
    2  NOT-READY        at least one gate measured false or unmeasurable
    3  usage error
"""

import argparse
import ctypes
import importlib.util
import json
import os
import re
import sys

PASS_ROW = re.compile(r"^PASS suite (\S+) ")
FAIL_ROW = re.compile(r"^FAIL suite (\S+) ")
CRIT = re.compile(r"criteria=(\d+)")
CLOSING = re.compile(r"BATTERY rc=(-?\d+)")


def kernel_alive(pid):
    """SYNCHRONIZE probe. An empty WMI command line is not evidence of death."""
    if not pid:
        return None
    h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, int(pid))
    if not h:
        return False
    try:
        return ctypes.windll.kernel32.WaitForSingleObject(h, 0) == 258
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def read_pid(pidfile):
    try:
        text = open(pidfile, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    m = re.search(r"\d+", text)
    return int(m.group(0)) if m else None


def registry():
    """Import the registry rather than counting files: names are the contract."""
    path = os.path.join("src", "sandbox", "reconcile_all.py")
    spec = importlib.util.spec_from_file_location("_ra_preflight", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    names, criteria = [], 0
    for row in mod.SUITES:
        names.append(row[0])
        try:
            criteria += int(row[2])
        except (TypeError, ValueError, IndexError):
            pass
    return names, criteria


def measure_evidence(path):
    try:
        raw = open(path, "rb").read()
    except OSError:
        return None
    out = {
        "bytes": len(raw),
        "bom": raw[:3] == b"\xef\xbb\xbf",
        "crlf": raw.count(b"\r\n"),
        "lone_cr": raw.count(b"\r") - raw.count(b"\r\n"),
        "nul": raw.count(b"\x00"),
    }
    try:
        text = raw.decode("utf-8")
        out["utf8"] = True
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        out["utf8"] = False
    out["text"] = text
    return out


def measure_stream(text):
    """A FAIL row is still a suite that RAN, so it counts for coverage.

    Only the unattributed-fail gate may read it as red; excluding it from the
    count and from the criteria recount would double-penalise it and make the
    attribution escape hatch unreachable.
    """
    ran, failed, crit_sum, closing = [], [], 0, None
    for line in text.splitlines():
        m = PASS_ROW.match(line)
        verdict = "PASS"
        if not m:
            m = FAIL_ROW.match(line)
            verdict = "FAIL"
        if m:
            ran.append(m.group(1))
            if verdict == "FAIL":
                failed.append(m.group(1))
            c = CRIT.search(line)
            if c:
                crit_sum += int(c.group(1))
            continue
        m = CLOSING.search(line)
        if m and closing is None:
            closing = int(m.group(1))
    return ran, failed, crit_sum, closing


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--stream", required=True)
    ap.add_argument("--pidfile", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--allow-fail-names", default="",
                    help="comma-separated FAIL row names already attributed to the tree "
                         "moving under the leg; everything else must be absent")
    args = ap.parse_args(argv)
    allowed = {n for n in args.allow_fail_names.split(",") if n}

    checks = []

    def record(code, ok, detail):
        checks.append((code, bool(ok) if ok is not None else False, detail))

    pid = read_pid(args.pidfile)
    alive = kernel_alive(pid)
    record("pid-gone", alive is False,
           "pid=%s kernel=%s" % (pid, "ALIVE" if alive else ("GONE" if alive is False else "UNKNOWN")))

    # The stream is read even when the evidence file is absent, because the
    # closing line lives there and an unfinished leg must say so precisely.
    stream_text = ""
    try:
        stream_text = open(args.stream, encoding="utf-8", errors="replace").read()
    except OSError:
        pass
    s_ran, s_fail, _, s_closing = measure_stream(stream_text)
    record("stream-closing-line", s_closing is not None,
           "closing_rc=%s stream_rows=%d stream_fail=%d" % (s_closing, len(s_ran), len(s_fail)))
    record("closing-rc-zero", s_closing == 0, "closing_rc=%s" % s_closing)

    ev = measure_evidence(args.evidence)
    record("evidence-exists", ev is not None,
           args.evidence if ev is None else "%d bytes" % ev["bytes"])

    names, crit_target = registry()
    record("registry-imported", bool(names), "suites=%d criteria=%d" % (len(names), crit_target))

    if ev is not None:
        record("utf8", ev["utf8"], "bom=%s crlf=%d lone_cr=%d nul=%d"
               % (ev["bom"], ev["crlf"], ev["lone_cr"], ev["nul"]))
        record("no-bom", not ev["bom"], "bom=%s" % ev["bom"])
        record("lf-clean", ev["crlf"] == 0 and ev["lone_cr"] == 0 and ev["nul"] == 0,
               "crlf=%d lone_cr=%d nul=%d" % (ev["crlf"], ev["lone_cr"], ev["nul"]))
        e_ran, e_fail, e_crit, e_closing = measure_stream(ev["text"])
        record("suite-count", len(e_ran) == len(names),
               "ran_rows=%d registry=%d" % (len(e_ran), len(names)))
        record("unique-names", len(set(e_ran)) == len(e_ran),
               "unique=%d rows=%d" % (len(set(e_ran)), len(e_ran)))
        record("name-set-equal", set(e_ran) == set(names),
               "equal=%s" % (set(e_ran) == set(names)))
        unattributed = [n for n in e_fail if n not in allowed]
        record("zero-unattributed-fail-rows", not unattributed,
               "fail_rows=%d unattributed=%d allowed=%d names=%s"
               % (len(e_fail), len(unattributed), len(allowed), ",".join(unattributed[:6])))
        record("criteria-recount", e_crit == crit_target,
               "recount=%d registry=%d" % (e_crit, crit_target))
        record("evidence-closing-line", e_closing is not None, "closing_rc=%s" % e_closing)
    else:
        # Unmeasurable gates are recorded as false rather than skipped, so a
        # reader can never mistake an unmeasured adoption for a passing one.
        for code in ("utf8", "no-bom", "lf-clean", "suite-count", "unique-names",
                     "name-set-equal", "zero-unattributed-fail-rows", "criteria-recount",
                     "evidence-closing-line"):
            record(code, False, "unmeasurable: evidence file absent")

    ready = all(ok for _, ok, _ in checks)
    for code, ok, detail in checks:
        print("%s %-22s %s" % ("PASS" if ok else "FAIL", code, detail))
    print("VERDICT %s gates=%d failed=%d"
          % ("ADOPT-READY" if ready else "NOT-READY",
             len(checks), sum(1 for _, ok, _ in checks if not ok)))
    print(json.dumps({"ready": ready,
                      "failed": [c for c, ok, _ in checks if not ok]}, sort_keys=True))
    return 0 if ready else 2


if __name__ == "__main__":
    sys.exit(main())
