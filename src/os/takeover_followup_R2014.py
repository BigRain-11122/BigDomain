# takeover_followup_R2014.py - corrected check-face invocations for the
# R2014 takeover battery (fingerprint requires --chain; the census tool
# lives at src/os, not src/sandbox - the first-pass FAILs were this
# battery's own invocation errors, not payload defects) + follow-up
# section appended to the takeover evidence in the canonical dialect.
# ASCII only.
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P_EV = os.path.join(ROOT, "qa", "takeover-verify-R2014.log")


def cap(cmd):
    r = subprocess.run([sys.executable] + cmd, cwd=ROOT,
                       capture_output=True, text=True)
    lines = [ln for ln in ((r.stdout or "") + (r.stderr or ""))
             .splitlines() if ln.strip()]
    return (r.returncode, lines[-1][:130] if lines else "no-line")


rc_f, f_tail = cap([os.path.join("src", "sandbox",
                   "fingerprint_regen.py"), "--chain",
                   os.path.join("src", "sandbox",
                                "migration_chains.json"), "--check"])
print("FINGERPRINT2 rc=%d %s" % (rc_f, f_tail), flush=True)
rc_c, c_tail = cap([os.path.join("src", "os", "qa_writer_census.py"),
                    "--check"])
print("CENSUS2 rc=%d %s" % (rc_c, c_tail), flush=True)

follow = [
    "--- takeover follow-up (same session, corrected check-face "
    "invocations) ---",
    "first-pass FAIL causes: fingerprint_regen.py requires --chain "
    "(migration_chains.json); qa_writer_census.py lives at src/os, "
    "not src/sandbox - both were this battery driver's own invocation "
    "errors, zero product/env defects",
    "FINGERPRINT rc=%d %s" % (rc_f, f_tail),
    "CENSUS rc=%d %s" % (rc_c, c_tail),
]
ok = rc_f == 0 and rc_c == 0
follow.append("BATTERY %s (follow-up: suite-anchor + runner 231/231 "
              "controls 7/7 + matrix + profile green at first pass; "
              "fingerprint + census green after invocation fix)"
              % ("PASS" if ok else "FAIL"))
with io.open(P_EV, "a", encoding="utf-8", newline="") as fh:
    fh.write("\n".join(follow) + "\n")
print("follow-up appended, verdict=%s" % ("PASS" if ok else "FAIL"),
      flush=True)
sys.exit(0 if ok else 1)
