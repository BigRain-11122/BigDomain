"""battery_shard - supervised slice runner over the battery registry (R2797).

AC-BSH1..AC-BSH8 were pinned in src/os/backlog.md BEFORE this file existed.

Why this exists: src/sandbox/reconcile_all.py is all-or-nothing. It carries no
label selector and no shard mode, so the only way to learn whether a FAMILY of
suites is green is a 4000-5900s leg that a window must supervise end to end.
Legs launched by windows that could not supervise them died truncated without a
closing row (R2779 pid 77376 gone mid-suite; R2780 refused the adoption by
measurement), which made "full battery owed" a structurally permanent debt.

This tool runs a NAMED SUBSET of the same registry rows with the SAME command
the battery uses, and prints its own closing SHARD row. It is deliberately not
a battery: its output can never be adopted as a full leg by
tools/adoption_preflight.py, which keys on a closing "BATTERY rc=" row.

Usage:
  python tools/battery_shard.py --match os-ledger --match ledger
  python tools/battery_shard.py --match os-lobby --dry
  python tools/battery_shard.py --match os-ledger --evidence battery-shard-R2797.log
  python tools/battery_shard.py --claim full        # refused, rc=2
  python tools/battery_shard.py --check --evidence battery-shard-R2797.log

Source discipline: pure ASCII, stdlib only, no clock literal, no network, no
shell (the only child processes are the selected suite files themselves).
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_REL = os.path.join("src", "sandbox", "reconcile_all.py")
QA_LOG_REL = os.path.join("tools", "qa_log.py")
QA_DIR = os.path.join(ROOT, "qa")
SUITE_LINE = re.compile(r"(?m)^SUITE\s+(PASS|FAIL)\s+(\d+)\s*/\s*(\d+)")


class Refuse(Exception):
    """A named refusal that must reach the caller as rc=2, never as rc=1."""


def load_module(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def registry():
    """AC-BSH1: rows, criteria, base and caps come from the registry itself."""
    mod = load_module(os.path.join(ROOT, REGISTRY_REL), "_bs_registry")
    rows = []
    seen = set()
    for row in mod.SUITES:
        label = row[0]
        rel = row[1]
        try:
            crit = int(row[2])
        except (TypeError, ValueError, IndexError):
            crit = 0
        if label in seen:
            raise Refuse("E_DUP_LABEL %s" % label)
        seen.add(label)
        rows.append((label, rel, crit))
    base = getattr(mod, "BASE", os.path.join(ROOT, "src", "sandbox"))
    cap = int(getattr(mod, "SUITE_TIMEOUT_S", 600))
    overrides = dict(getattr(mod, "SUITE_TIMEOUT_OVERRIDES", None) or {})
    return rows, base, cap, overrides


def select(rows, prefixes, limit):
    """AC-BSH2: a case-sensitive label PREFIX test, in registry order."""
    if prefixes:
        picked = [r for r in rows if any(r[0].startswith(p) for p in prefixes)]
        unmatched = [p for p in prefixes if not any(r[0].startswith(p) for r in rows)]
        if unmatched:
            raise Refuse("E_NO_MATCH %s" % ",".join(unmatched))
    else:
        picked = list(rows)
    if limit and limit > 0:
        picked = picked[:limit]
    return picked


def run_one(base, label, rel, cap, overrides):
    """AC-BSH3: the battery's own invocation, byte for byte in behaviour.

    The cap law is the battery's own suite_timeout(): one declared override per
    suite LABEL, else the named constant. Override keys are labels, measured on
    the registry (one key today: ledger-apimarket-refundregister -> 900).
    """
    path = os.path.join(base, rel)
    duration = int(overrides.get(label, cap))
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    started = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", cwd=os.path.dirname(path), timeout=duration,
            env=env)
        code, out = proc.returncode, proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        out = (out or "").rstrip("\n")
        marker = "TIMEOUT suite exceeded the %ds per-suite cap" % duration
        code = 124
        out = (out + "\n" + marker) if out else marker
    return code, out, time.time() - started


def evidence_name(raw):
    """AC-BSH6: evidence lives under qa/ and nowhere else."""
    name = os.path.basename(str(raw))
    if not name or name != str(raw).replace("\\", "/").split("/")[-1]:
        raise Refuse("E_EVIDENCE_PATH %s" % raw)
    parent = os.path.dirname(str(raw).replace("\\", "/"))
    if parent not in ("", "qa"):
        raise Refuse("E_EVIDENCE_PATH %s" % raw)
    return name


def write_evidence(name, text):
    qa_log = load_module(os.path.join(ROOT, QA_LOG_REL), "_bs_qa_log")
    qa_log.do_write(name, text.encode("utf-8"), directory=QA_DIR)
    path = os.path.join(QA_DIR, name)
    proof = qa_log.verify_written(path)
    return proof


def do_check(name):
    """Read the evidence back and recompute its counts from its own rows."""
    path = os.path.join(QA_DIR, name)
    if not os.path.exists(path):
        print("SHARD-CHECK RED reason=missing name=%s" % name)
        return 2
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print("SHARD-CHECK RED reason=undecodable name=%s" % name)
        return 2
    rows = [l for l in text.splitlines() if l.startswith("SHARD row ")]
    closing = [l for l in text.splitlines() if l.startswith("SHARD rc=")]
    battery = [l for l in text.splitlines() if l.startswith("BATTERY")]
    fails = []
    if not rows:
        fails.append("E_NO_ROWS")
    if len(closing) != 1:
        fails.append("E_CLOSING_ROWS=%d" % len(closing))
    if battery:
        fails.append("E_BATTERY_LINE=%d" % len(battery))
    executed = len(rows)
    green = len([l for l in rows if re.search(r"\brc=0\b", l)])
    if closing and not fails:
        announced = re.search(r"\bexecuted=(\d+)\b", closing[0])
        if not announced or int(announced.group(1)) != executed:
            fails.append("E_EXECUTED_MISMATCH")
        greens = re.search(r"\bgreen=(\d+)\b", closing[0])
        if not greens or int(greens.group(1)) != green:
            fails.append("E_GREEN_MISMATCH")
        verdict = re.search(r"\bSHARD rc=(\d+)\b", closing[0])
        expect = 0 if green == executed else 2
        if not verdict or int(verdict.group(1)) != expect:
            fails.append("E_VERDICT_MISMATCH")
    print("SHARD-CHECK name=%s rows=%d green=%d bytes=%dB"
          % (name, executed, green, len(raw)))
    if fails:
        print("SHARD-CHECK RED %s" % ",".join(fails))
        return 2
    print("SHARD-CHECK VERDICT PASS")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--match", action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--claim", default="")
    ap.add_argument("--evidence", default="")
    args = ap.parse_args(argv)
    try:
        return _round(args)
    except Refuse as exc:
        print(str(exc))
        return 2


def _round(args):
    # AC-BSH6: the evidence path is validated BEFORE any suite runs, including
    # in --dry mode, so a bad path can never be discovered after 10 minutes.
    if args.evidence:
        evidence_name(args.evidence)

    if args.claim and args.claim.strip().lower() == "full":
        print("E_NOT_FULL a shard cannot claim battery coverage; run the "
              "battery itself and adopt its closing row")
        return 2

    if args.check:
        if not args.evidence:
            print("E_NO_EVIDENCE --check needs --evidence")
            return 2
        return do_check(evidence_name(args.evidence))

    rows, base, cap, overrides = registry()
    picked = select(rows, args.match, args.limit)
    total_crit = sum(int(r[2]) for r in picked)
    print("SHARD scope=SHARD registry_suites=%d registry_criteria=%d "
          "selected=%d selected_criteria=%d cap=%ds overrides=%d"
          % (len(rows), sum(int(r[2]) for r in rows), len(picked),
             total_crit, cap, len(overrides)))
    for label, rel, crit in picked:
        print("SHARD selected %s crit=%d path=%s" % (label, crit, rel))
    if args.dry:
        print("SHARD rc=0 scope=SHARD dry=True executed=0 selected=%d" % len(picked))
        return 0

    lines = []
    executed = 0
    green = 0
    crit_run = 0
    mismatch = []
    reds = []
    started = time.time()
    for label, rel, crit in picked:
        code, out, secs = run_one(base, label, rel, cap, overrides)
        passes = len(re.findall(r"(?m)^PASS\b", out))
        fails = len(re.findall(r"(?m)^FAIL\b", out))
        m = SUITE_LINE.search(out)
        suite = ("%s %s/%s" % (m.group(1), m.group(2), m.group(3))) if m else "none"
        if m and int(m.group(3)) != int(crit):
            mismatch.append("%s:%s!=%d" % (label, m.group(3), crit))
        executed += 1
        crit_run += int(crit)
        if code == 0:
            green += 1
        else:
            reds.append("%s:rc=%d" % (label, code))
        line = ("SHARD row %s rc=%d pass=%d fail=%d suite=%s crit=%d %.1fs"
                % (label, code, passes, fails, suite, crit, secs))
        print(line)
        lines.append(line)
        if code != 0:
            for chunk in out.splitlines()[:40]:
                lines.append("SHARD detail %s %s" % (label, chunk))
    elapsed = time.time() - started
    rc = 0 if (green == executed == len(picked)) else 2
    closing = ("SHARD rc=%d scope=SHARD selected=%d executed=%d green=%d "
               "criteria=%d crit_mismatch=%d elapsed=%.1fs"
               % (rc, len(picked), executed, green, crit_run, len(mismatch), elapsed))
    print(closing)
    lines.insert(0, "SHARD scope=SHARD registry_suites=%d registry_criteria=%d "
                    "selected=%d selected_criteria=%d cap=%ds"
                 % (len(rows), sum(int(r[2]) for r in rows), len(picked),
                    total_crit, cap))
    lines.append(closing)
    if mismatch:
        print("SHARD disclosure crit_mismatch=%s" % ",".join(mismatch))
        lines.append("SHARD disclosure crit_mismatch=%s" % ",".join(mismatch))
    if reds:
        print("SHARD red %s" % ",".join(reds))
        lines.append("SHARD red %s" % ",".join(reds))
    if args.evidence:
        proof = write_evidence(evidence_name(args.evidence), "\n".join(lines) + "\n")
        print("SHARD evidence name=%s bytes=%d lines=%d sha256=%s dialect=utf-8/lf"
              % (evidence_name(args.evidence), proof["bytes"], proof["lines"],
                 proof["sha256"]))
    return rc


if __name__ == "__main__":
    sys.exit(main())
