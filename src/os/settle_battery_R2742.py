"""Settle the R2742 reconcile battery leg on measured bytes (RED, not adopted).

Why this exists: the leg launched at R2743 from commit 022f916f came back
RED at 4308.6s with five failing assertions. This script MEASURES the
evidence file rather than quoting anybody's summary, then re-runs the red
suites one by one on the CURRENT committed tree, so the claim "the birth
site is already repaired" is a measurement and not an assertion.

What it does NOT do: it never adopts the leg green, never rewrites the
evidence file, never relaunches, and never writes any product byte. The
settlement log is a new artifact beside the evidence.

Stdlib only, pure ASCII source, zero network, no clock read beyond the
evidence file's own mtime which is not consulted.
"""

import io
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
SANDBOX = os.path.join(REPO, "src", "sandbox")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2742.log")
OUT = os.path.join(REPO, "qa", "battery-R2742-settlement.log")

TARGET_SUITES = 676
TARGET_CRITERIA = 5032

# The five suites that read red in the leg, by the runner's own row names.
RED_SUITES = (
    ("os-ledger-lines", "test_ledger_lines.py", 8),
    ("os-ledger-archive", "test_ledger_archive.py", 8),
    ("os-ledger-baseline", "test_ledger_baseline.py", 8),
    ("os-ledger-fold-kind", "test_ledger_fold_kind.py", 6),
    ("os-ledger-fold-kind-dateprefix", "test_ledger_fold_kind_dateprefix.py", 6),
)

SUITE_RE = re.compile(r"^(PASS|FAIL) suite (\S+) exit=(\d+) "
                      r"pass-lines=(\d+) fail-lines=(\d+) criteria=(\d+)")
BATTERY_RE = re.compile(r"^BATTERY rc=(\d+)\s+([0-9.]+)s$")


def measure_evidence(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    out = {
        "bytes": len(raw),
        "bom": raw[:3] == b"\xef\xbb\xbf",
        "crlf": raw.count(b"\r\n"),
        "lone_cr": raw.count(b"\r") - raw.count(b"\r\n"),
        "nul": raw.count(b"\x00"),
        "utf8": True,
        "rows": 0,
        "pass": 0,
        "fail": 0,
        "names": set(),
        "criteria": 0,
        "fail_names": [],
        "battery": None,
        "fail_assertions": None,
    }
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        out["utf8"] = False
        text = raw.decode("utf-8", "replace")
    lines = text.split("\n")
    for line in lines:
        match = SUITE_RE.match(line)
        if match:
            out["rows"] += 1
            out["names"].add(match.group(2))
            out["criteria"] += int(match.group(6))
            if match.group(1) == "PASS":
                out["pass"] += 1
            else:
                out["fail"] += 1
                out["fail_names"].append(match.group(2))
            continue
        match = BATTERY_RE.match(line)
        if match:
            out["battery"] = (int(match.group(1)), float(match.group(2)))
            continue
        if line.startswith("RUNNER FAIL"):
            out["fail_assertions"] = line.strip()
    return out


def registry_by_import():
    sys.path.insert(0, SANDBOX)
    import reconcile_all
    rows = reconcile_all.SUITES
    return (len(rows),
            sum(row[2] for row in rows),
            len({row[0] for row in rows}),
            len({row[1] for row in rows}))


def rerun(name, filename, criteria):
    path = os.path.join(BASE, filename)
    proc = subprocess.run([sys.executable, path], cwd=SANDBOX,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    pass_lines = text.count("PASS AC-")
    fail_lines = text.count("FAIL AC-")
    verdict = ""
    for line in text.split("\n"):
        if line.strip().startswith("SUITE "):
            verdict = line.strip()
    return {
        "name": name,
        "rc": proc.returncode,
        "pass": pass_lines,
        "fail": fail_lines,
        "verdict": verdict,
        "criteria": criteria,
    }


def main():
    if not os.path.isfile(EVIDENCE):
        sys.stdout.write("E_SETTLE_NO_EVIDENCE %s\n" % EVIDENCE)
        return 3
    ev = measure_evidence(EVIDENCE)
    lines = []
    lines.append("SETTLE battery-R2742 leg measured, not quoted")
    lines.append("evidence=%s bytes=%d utf8=%s bom=%s crlf=%d lone_cr=%d nul=%d"
                 % (os.path.relpath(EVIDENCE, REPO).replace("\\", "/"),
                    ev["bytes"], ev["utf8"], ev["bom"], ev["crlf"],
                    ev["lone_cr"], ev["nul"]))
    lines.append("rows=%d pass_rows=%d fail_rows=%d unique_names=%d "
                 "criteria_sum=%d target=%d/%d"
                 % (ev["rows"], ev["pass"], ev["fail"], len(ev["names"]),
                    ev["criteria"], TARGET_SUITES, TARGET_CRITERIA))
    lines.append("fail_names=%s" % (",".join(ev["fail_names"]) or "none"))
    if ev["battery"] is None:
        lines.append("closing_battery=NONE")
    else:
        lines.append("closing_battery=rc%d %.1fs" % ev["battery"])
    lines.append("runner_line=%s" % (ev["fail_assertions"] or "none"))
    lines.append("")
    lines.append("REGISTRY BY IMPORT on the current committed tree")
    suites, criteria, names, paths = registry_by_import()
    lines.append("suites=%d criteria=%d unique_names=%d unique_paths=%d "
                 "matches_leg_target=%s"
                 % (suites, criteria, names, paths,
                    suites == TARGET_SUITES and criteria == TARGET_CRITERIA))
    lines.append("")
    lines.append("RED SUITES RE-RUN ON THE CURRENT TREE (birth site check)")
    healed = 0
    for name, filename, crit in RED_SUITES:
        row = rerun(name, filename, crit)
        green = (row["rc"] == 0 and row["fail"] == 0
                 and "SUITE PASS" in row["verdict"])
        healed += 1 if green else 0
        lines.append("%s rehealed=%s rc=%d pass=%d fail=%d %s"
                     % (name, green, row["rc"], row["pass"], row["fail"],
                        row["verdict"]))
    lines.append("")
    lines.append("VERDICT leg=RED adopted=NO "
                 "red_suites=%d rehealed_on_current_tree=%d/%d "
                 "delta_criteria=%d"
                 % (ev["fail"], healed, len(RED_SUITES),
                    ev["criteria"] - TARGET_CRITERIA))
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
