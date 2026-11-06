"""export_consistency_queue_face suite (R2498).

Criteria AC-ECQF1..AC-ECQF6 were pinned inside the R2497 tech seed row of
state/queue/tech.md:533 BEFORE this code existed.

What this proves: check_export_consistency is the twenty-one-check face every
window trusts, and it never opens the export's queue block. R2497 MEASURED a
doctored export reading pass=21 fail=0 while queue_export_freshness_gate read
STALE on the same document. One face now asks that shipped gate at CALL time and
publishes its verdict beside the twenty-one checks, never inside them.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import export_consistency_queue_face as ECQF  # noqa: E402
import queue_export_freshness_gate as QEF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_consistency_queue_face.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
LABEL = "os-export-consistency-queue-face"
WIRED_EXPECT = '"test_export_consistency_queue_face.py"), 6),'
ALLOWED_IMPORTS = {"json", "os", "sys", "check_export_consistency",
                   "queue_export_freshness_gate"}

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


class patched(object):
    """Temporarily replace one attribute so a CALL-time ask is observable."""

    def __init__(self, module, name, value):
        self.module = module
        self.name = name
        self.value = value

    def __enter__(self):
        self.old = getattr(self.module, self.name)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.old)
        return False


def doctored_export(tmpdir):
    """The real export with its queue block moved away from the live reading."""
    data = json.loads(read_text(EXPORT))
    doc = copy.deepcopy(data)
    block = doc.get("queue")
    if not isinstance(block, dict):
        return None
    block["shortfall_total"] = int(block.get("shortfall_total") or 0) + 99
    block["verdict"] = "FLOOR-DEBT"
    for row in block.get("queues") or ():
        if isinstance(row, dict) and row.get("queue") == "tech":
            row["claimable"] = 0
    path = os.path.join(tmpdir, "doctored-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    return path


def current_export(tmpdir):
    """The real export with its queue block set to the LIVE reading (CURRENT)."""
    doc = json.loads(read_text(EXPORT))
    doc["queue"] = QEF.live_section(REPO)
    doc = json.loads(json.dumps(doc))
    path = os.path.join(tmpdir, "current-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    return path


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args, cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode, proc.stdout.decode("utf-8"),
            proc.stderr.decode("utf-8"))


def ac_ecqf1_call_time():
    """AC-ECQF1 the queue reading is asked at CALL time, never a constant."""
    fake = {"label": QEF.LABEL, "verdict": "STALE",
            "drifted": ["queue:main", "section:verdict"],
            "claimable": [1, 2, 3], "delivered_total": 0}
    seen = {"root": None, "path": None}

    def fake_check(root, path):
        seen["root"] = root
        seen["path"] = path
        return fake, 2

    with patched(QEF, "check", fake_check):
        result = ECQF.read(REPO, EXPORT)
    check(result["queue_verdict"] == "STALE"
          and result["queue_drifted"] == ["queue:main", "section:verdict"]
          and result["verdict"] == "DRIFT" and result["exit_code"] == 2
          and seen["root"] == REPO and seen["path"] == EXPORT,
          "AC-ECQF1 queue reading asked at CALL time (patched gate moves it)")

    fake_base = (["PASS base.sentinel stored=1"], 21, 0)
    with patched(CEC, "check", lambda: fake_base):
        result = ECQF.read(REPO, EXPORT)
    check(result["base_lines"] == ["PASS base.sentinel stored=1"]
          and result["base_pass"] == 21 and result["base_fail"] == 0,
          "AC-ECQF1 base checks asked at CALL time (patched face moves them)")


def ac_ecqf2_base_unchanged():
    """AC-ECQF2 the twenty-one checks keep names, order and verdicts."""
    lines, n_pass, n_fail = CEC.check()
    result = ECQF.read(REPO, EXPORT)
    check(result["base_lines"] == lines
          and result["base_checks"] == n_pass + n_fail == 21,
          "AC-ECQF2 twenty-one base lines identical and counted")


def ac_ecqf3_drift_named():
    """AC-ECQF3 a stale block reads DRIFT, names every drift, folds into none."""
    tmpdir = tempfile.mkdtemp(prefix="ecqf-")
    try:
        path = doctored_export(tmpdir)
        check(path is not None, "AC-ECQF3 fixture built from the real export")
        if path is None:
            return
        result = ECQF.read(REPO, path)
        drifted = result["queue_drifted"]
        check(result["verdict"] == "DRIFT"
              and result["queue_verdict"] == "STALE"
              and "queue:tech" in drifted
              and any(name.startswith("section:") for name in drifted),
              "AC-ECQF3 stale block reads DRIFT naming queue and sections")
        check(result["base_fail"] == 0 and result["base_pass"] == 21
              and result["base_lines"] == CEC.check()[0],
              "AC-ECQF3 queue drift is never folded into the twenty-one")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ac_ecqf4_current_shape():
    """AC-ECQF4 a CURRENT document keeps today's lines and code, plus one."""
    lines, _n_pass, _n_fail = CEC.check()
    before = read_bytes(EXPORT)
    tmpdir = tempfile.mkdtemp(prefix="ecqf-cur-")
    try:
        path = current_export(tmpdir)
        result = ECQF.read(REPO, path)
        check(result["verdict"] == "AGREE" and result["exit_code"] == 0
              and result["base_lines"] == lines
              and result["queue_verdict"] == "CURRENT"
              and result["queue_drifted"] == [],
              "AC-ECQF4 CURRENT document reads AGREE at exit 0 with base intact")
        code, out, err = run_cli(["--check", "--root", REPO, "--export", path])
        expected = "".join(line + "\n" for line in lines)
        check(code == 0 and out.startswith(expected)
              and out[len(expected):].startswith(
                  "QUEUE %s verdict=CURRENT" % QEF.LABEL)
              and out.count("\n") == len(lines) + 2 and err == "",
              "AC-ECQF4 CLI prints the base lines then exactly one queue line")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    check(before == read_bytes(EXPORT),
          "AC-ECQF4 the reading left the export byte-identical")


def ac_ecqf5_purity():
    """AC-ECQF5 the reading writes nothing and reads no clock of its own."""
    src = read_text(MODULE)
    stray = 0
    for line in src.splitlines():
        if (".write(" in line and "stdout.write(" not in line
                and "stderr.write(" not in line and "buffer.write(" not in line):
            stray += 1
    check("import time" not in src and "datetime" not in src
          and "open(" not in src and stray == 0,
          "AC-ECQF5 source carries no clock and no file write call")
    before = read_bytes(EXPORT)
    ECQF.read(REPO, EXPORT)
    ECQF.read(REPO, EXPORT)
    check(read_bytes(EXPORT) == before,
          "AC-ECQF5 two readings left the export byte-identical")


def ac_ecqf6_hygiene():
    """AC-ECQF6 pure ASCII, stdlib, one registry row wiring this suite."""
    raw = read_bytes(MODULE)
    check(all(byte < 128 for byte in raw), "AC-ECQF6 module source is pure ASCII")
    names = set()
    for line in read_text(MODULE).splitlines():
        text = line.strip()
        if text.startswith("import "):
            names.add(text.split()[1].split(".")[0])
        elif text.startswith("from ") and " import " in text:
            names.add(text.split()[1].split(".")[0])
    check(names <= ALLOWED_IMPORTS and names - {"check_export_consistency",
                                               "queue_export_freshness_gate"} <= {"json", "os", "sys"},
          "AC-ECQF6 imports are stdlib plus the two shipped faces only")
    runner = read_text(RUNNER)
    check(runner.count(WIRED_EXPECT) == 1 and runner.count('"%s"' % LABEL) == 1,
          "AC-ECQF6 exactly one registry row wires this suite with 6 criteria")
    check(EXPECTED_CRITERIA == 6, "AC-ECQF6 six criteria declared")


def main():
    ac_ecqf1_call_time()
    ac_ecqf2_base_unchanged()
    ac_ecqf3_drift_named()
    ac_ecqf4_current_shape()
    ac_ecqf5_purity()
    ac_ecqf6_hygiene()
    print("SUMMARY pass=%d fail=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())