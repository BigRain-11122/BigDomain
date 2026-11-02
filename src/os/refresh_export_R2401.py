# refresh_export_R2401.py - surgical in-place digit updates on the three
# stored self-drive counters the checker recomputed, plus export_ts.
import io
import json
import os
import re
import sys
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(REPO, "docs", "status-export.json")
CHECKER = os.path.join(BASE, "check_export_consistency.py")


def recompute():
    out = subprocess.run([sys.executable, CHECKER], capture_output=True,
                         text=True)
    values = {}
    for line in out.stdout.splitlines():
        match = re.search(r"FAIL (\S+) stored='?([^']*)'? recomputed='?([^']*)'?",
                          line)
        if match:
            values[match.group(1)] = (match.group(2), match.group(3))
    return values


def main():
    text = io.open(EXPORT, "r", encoding="utf-8", newline="").read()
    before = len(text.encode("utf-8"))
    values = recompute()
    print("recomputed", values)
    changed = []
    for key, (stored, new) in values.items():
        field = key.rsplit(".", 1)[-1]
        pattern = r'("%s"\s*:\s*)(?:"%s"|%s)' % (re.escape(field),
                                                 re.escape(stored),
                                                 re.escape(stored))
        match = re.search(pattern, text)
        if match is None:
            print("SKIP %s (no anchor)" % field)
            continue
        text = text[:match.start()] + match.group(1) + new + text[match.end():]
        changed.append((field, stored, new))
    stamp = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-Date -Format yyyy-MM-ddTHH:mm:sszzz"],
                           capture_output=True, text=True).stdout.strip()
    if stamp:
        text = re.sub(r'("export_ts"\s*:\s*)"[^"]*"',
                      lambda m: m.group(1) + json.dumps(stamp), text, count=1)
    io.open(EXPORT, "w", encoding="utf-8", newline="").write(text)
    after = len(text.encode("utf-8"))
    print("EXPORT bytes %d -> %d changed=%r export_ts=%s"
          % (before, after, changed, stamp))
    out = subprocess.run([sys.executable, CHECKER], capture_output=True,
                         text=True)
    print(out.stdout.strip().splitlines()[-2:])
    return 0


if __name__ == "__main__":
    sys.exit(main())