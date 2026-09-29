"""Product health-check runner (BigDomain explore-line item #9, R594).

One command = the full sandbox regression fan-out (nine acceptance
suites, 100 pre-registered criteria in total) plus the standalone
ledger reconcile product face: a canonical demo state built via the
ledger public API (reuse, zero schema duplication), the eight-check
reconcile script must PASS clean, and a tampered copy (materialized
balance +1) must FAIL with exit 2. Process exit code 0 iff every
suite exits 0 and both reconcile controls land as expected.

Suite scenario logic stays inside each acceptance suite - this
runner orchestrates, it does not duplicate (no-reinvent-wheel law).
Pre-registered criteria AC-RA1..RA5: src/os/backlog.md R594 row.
Pay/member standalone-reconcile demo builders and live-db passthrough
args are honestly split to a follow-up row: this round proves the
pattern end-to-end on the ledger domain (the token-ledger core).

Usage:
    python reconcile_all.py [evidence_log_path]
(the optional path makes this runner tee its own utf-8 evidence log
while still streaming to the console; pass e.g.
qa/reconcile-all-R594.log)
"""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "ledger")

SUITES = [
    # (label, suite path relative to the sandbox root, expected criteria)
    ("lobby", os.path.join("lobby", "test_client.py"), 13),
    ("ledger", os.path.join("ledger", "test_ledger.py"), 11),
    ("ugc", os.path.join("ugc", "test_ugc.py"), 12),
    ("pay", os.path.join("pay", "test_pay.py"), 16),
    ("pay-v3", os.path.join("pay", "test_pay_v3.py"), 14),
    ("member", os.path.join("member", "test_member.py"), 16),
    ("watermark", os.path.join("watermark", "test_watermark.py"), 5),
    ("watermark-robust",
     os.path.join("watermark", "test_watermark_robust.py"), 6),
    ("dual-track", os.path.join("watermark", "test_dual_track.py"), 7),
]

FAILS = 0


class Tee(object):
    """Stream to the console and mirror everything to a utf-8 log file."""

    def __init__(self, path):
        self.file = open(path, "w", encoding="utf-8", newline="\n")
        self.stdout = sys.stdout

    def write(self, data):
        self.file.write(data)
        try:
            self.stdout.write(data)
        except UnicodeEncodeError:
            # console is locale-encoded (cp936 here); never let an
            # echo kill the run - lossy for console only, file stays
            # full-fidelity utf-8
            enc = getattr(self.stdout, "encoding", None) or "ascii"
            self.stdout.write(
                data.encode(enc, "replace").decode(enc, "replace"))

    def flush(self):
        self.file.flush()
        self.stdout.flush()

    def close(self):
        self.file.close()


def note(ok, line):
    global FAILS
    if not ok:
        FAILS += 1
    print("%s %s" % ("PASS" if ok else "FAIL", line), flush=True)


def run_cmd(cmd, cwd):
    # child pythons emit pipe output in the machine locale (cp936 on
    # this zh-CN Windows) - decode with the same locale, not utf-8
    proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True,
                           errors="replace", cwd=cwd, timeout=300)
    return proc.returncode, proc.stdout or ""


def echo(out):
    for line in out.splitlines():
        print("  | %s" % line)


def phase_suites():
    green = 0
    total = 0
    for label, rel, crit in SUITES:
        path = os.path.join(BASE, rel)
        t0 = time.time()
        code, out = run_cmd([sys.executable, path], cwd=os.path.dirname(path))
        echo(out)
        passes = len(re.findall(r"(?m)^PASS\b", out))
        fails = len(re.findall(r"(?m)^FAIL\b", out))
        total += crit
        ok = code == 0
        if ok:
            green += 1
        note(ok, "suite %s exit=%d pass-lines=%d fail-lines=%d criteria=%d %.1fs"
             % (label, code, passes, fails, crit, time.time() - t0))
    note(green == len(SUITES),
         "suites %d/%d green, expected criteria total=%d"
         % (green, len(SUITES), total))
    return green == len(SUITES)


def build_demo_state(db_path):
    """Canonical ledger demo state via the public API only (reuse law)."""
    sys.path.insert(0, LEDGER)
    import ledger as L  # noqa: E402 (product module, reuse-not-copy)
    with open(os.path.join(LEDGER, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    led = L.Ledger(db_path, cfg)
    led.mint_to_pool("pool:reward", 500, "DEMO-MINT-1")
    led.mint_to_pool("pool:share", 300, "DEMO-MINT-2")
    led.ensure_account("usr:demo1", "AV-DEMO-1")
    led.ensure_account("usr:demo2", "AV-DEMO-2")
    led.grant_reward("usr:demo1", "login", "DEMO-EVT-1")
    led.record_gate_pass("DEMO-EVT-G1")
    led.grant_reward("usr:demo1", "cocreate", "DEMO-EVT-G1")
    led.share_from_pool("pool:share", "usr:demo2", 40, "DEMO-SHARE-1")
    led.spend("usr:demo2", 10, "DEMO-ORDER-1")
    led.close()


def phase_reconcile(tmp):
    db = os.path.join(tmp, "ledger.db")
    build_demo_state(db)
    code, out = run_cmd([sys.executable, os.path.join(LEDGER, "reconcile.py"),
                         db], cwd=LEDGER)
    echo(out)
    note(code == 0 and "RECONCILE PASS" in out,
         "reconcile ledger-demo exit=%d (expect 0, clean eight checks)" % code)
    tampered = os.path.join(tmp, "ledger-tampered.db")
    shutil.copyfile(db, tampered)
    conn = sqlite3.connect(tampered)
    conn.execute("UPDATE ledger_accounts SET balance = balance + 1"
                 " WHERE account_id = 'usr:demo1'")
    conn.commit()
    conn.close()
    code2, out2 = run_cmd([sys.executable, os.path.join(LEDGER, "reconcile.py"),
                           tampered], cwd=LEDGER)
    echo(out2)
    note(code2 == 2 and "RECONCILE FAIL" in out2,
         "reconcile tamper-control exit=%d (expect 2, FAIL detected)" % code2)


def main(argv):
    tee = None
    if len(argv) > 1:
        tee = Tee(argv[1])
        sys.stdout = tee
    t0 = time.time()
    suites_ok = phase_suites()
    tmp = tempfile.mkdtemp(prefix="reconcile-all-")
    try:
        phase_reconcile(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILS == 0 and suites_ok:
        print("RUNNER PASS (%d/%d suites green, reconcile controls 2/2, %.1fs)"
              % (len(SUITES), len(SUITES), time.time() - t0), flush=True)
        code = 0
    else:
        print("RUNNER FAIL (%d failed assertions)" % FAILS, flush=True)
        code = 1
    if tee is not None:
        sys.stdout = tee.stdout
        tee.close()
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
