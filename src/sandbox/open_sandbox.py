"""Open the whole sandbox with one call and hand the person the hub URL.

start_all.py already proves nine faces and prints the measured hub URL, but a
person has to run it in a console, read a JSON line, and paste a port. This
module closes the last step for a double-click launcher: it starts start_all.py
as a child, waits for the report file the child writes, and opens the browser
at the URL the child measured - never at a built-in guess.

Honesty law: the browser opens only after the report file says ok=true with a
hub_url. A launcher that opened a guessed port would be the same lie as a page
that paints a dead port green.

Usage:
  python src/sandbox/open_sandbox.py             # serve and open the browser
  python src/sandbox/open_sandbox.py --no-browser
  python src/sandbox/open_sandbox.py --check     # prove, stop, exit 0/2
Exit: 0 = hub came up (and, with --check, the sandbox was torn down cleanly).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOGS = os.path.join(ROOT, "logs")
START_ALL = os.path.join(HERE, "start_all.py")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def read_report(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="start the sandbox and open the measured hub URL")
    parser.add_argument("--check", action="store_true",
                        help="start, wait for the hub, tear down, print a "
                             "verdict and exit 0 on proof / 2 otherwise")
    parser.add_argument("--no-browser", action="store_true",
                        help="do not open a browser (used by --check)")
    parser.add_argument("--timeout", type=float, default=90.0,
                        help="seconds to wait for the hub report")
    args = parser.parse_args(argv)

    os.makedirs(LOGS, exist_ok=True)
    report_path = os.path.join(LOGS, "sandbox-start.json")
    stop_path = os.path.join(LOGS, "sandbox-stop.txt")
    child_log = os.path.join(LOGS, "sandbox-start.log")
    for path in (report_path, stop_path):
        try:
            os.remove(path)
        except OSError:
            pass

    cmd = [sys.executable, START_ALL, "--report-json", report_path,
           "--stop-file", stop_path]
    with open(child_log, "wb") as sink:
        child = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.DEVNULL,
                                 stdout=sink, stderr=subprocess.STDOUT,
                                 creationflags=NO_WINDOW)

    deadline = time.time() + args.timeout
    report = None
    while time.time() < deadline:
        if child.poll() is not None:
            break
        report = read_report(report_path)
        if report and report.get("hub_url") and report.get("ok"):
            break
        time.sleep(0.4)

    ok = bool(report and report.get("hub_url") and report.get("ok"))
    hub_url = (report or {}).get("hub_url") or ""

    if ok:
        faces = report.get("live") or {}
        print("sandbox up: hub=%s faces=%d/8" % (hub_url, sum(1 for v in faces.values() if v)))
        if not args.no_browser and not args.check:
            webbrowser.open(hub_url)
    else:
        errors = (report or {}).get("errors") or []
        print("sandbox did not come up: %s" % ("; ".join(errors) or "no report"))

    try:
        if args.check:
            time.sleep(2.0)
            with open(stop_path, "w", encoding="ascii") as fh:
                fh.write("stop\n")
        else:
            child.wait()
    except KeyboardInterrupt:
        with open(stop_path, "w", encoding="ascii") as fh:
            fh.write("stop\n")
    finally:
        if args.check or child.poll() is not None:
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
