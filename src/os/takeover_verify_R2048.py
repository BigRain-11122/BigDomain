# takeover_verify_R2048.py - R2048 orphan-payload takeover
# verification. The prior session (crashed round R2048, died
# pre-closeout ~00:14 after a full RUNNER attempt) left the
# funnel CLI bad-args gate suite (AC-FCG1..FCG7) delivered and
# wired, with a standalone double-run evidence log written in a
# BAD DIALECT (pwsh-capture class -> census new-dialect flag =
# the only red suite in its RUNNER pass: reconcile-daily-census
# 7/8, RUNNER 256/257). This script (1) re-runs the suite twice
# in-process-clean subprocesses, (2) asserts the double-run is
# byte-identical, (3) asserts sha16 cross-match against the
# orphan evidence value 8f29b21a8aaa7afa (takeover evidence-chain
# closure, R2045 precedent), (4) rebuilds the evidence file at
# the same path with a python single-writer utf-8 LF canonical
# body (R1924/R2033/R2045 dialect law - G6 fix per the
# reconcile-daily runbook), and (5) prints the pre-rebuild byte
# head of the dialect-sick artifact for the record. Pure ASCII.
import hashlib
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normcase(os.path.normpath(
    os.path.join(HERE, "..", "..")))
SUITE = os.path.join(ROOT, "src", "sandbox", "funnel",
                     "test_funnel_cli_gates.py")
EVID = os.path.join(ROOT, "qa", "funnel-cli-gates-R2048.log")
EXPECT_SHA16 = "8f29b21a8aaa7afa"


def run_once():
    p = subprocess.run([sys.executable, SUITE],
                       capture_output=True)
    # R2023/R2045 dialect law: the child stdout carries the
    # Windows newline translation; keep the raw stream for the
    # orphan cross-match basis, LF-normalize for the canonical
    # evidence basis.
    return (p.returncode, p.stdout,
            p.stdout.replace(b"\r\n", b"\n").decode("utf-8"))


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    old = open(EVID, "rb").read()
    print("pre-rebuild dialect head: %s"
          % " ".join(format(b, "02x") for b in old[:12]))
    rc_a, raw_a, out_a = run_once()
    rc_b, raw_b, out_b = run_once()
    if rc_a != 0 or rc_b != 0:
        die("suite rerun nonzero rc %r/%r" % (rc_a, rc_b))
    if raw_a != raw_b:
        die("double-run raw streams not byte-identical")
    raw_sha = hashlib.sha256(raw_a).hexdigest()[:16]
    if raw_sha != EXPECT_SHA16:
        die("cross-match FAIL vs orphan evidence: "
            "%s != %s" % (raw_sha, EXPECT_SHA16))
    if out_a != out_b:
        die("double-run LF bodies not byte-identical")
    lf_a = hashlib.sha256(
        out_a.encode("utf-8")).hexdigest()[:16]
    lf_b = hashlib.sha256(
        out_b.encode("utf-8")).hexdigest()[:16]
    if lf_a != lf_b:
        die("lf sha mismatch within double run")
    body = [
        "=== funnel CLI gates suite double-run evidence"
        " (R2048) ===",
        "--- run A exit=0 lf-sha16=%s ---" % lf_a,
        out_a.rstrip("\n"),
        "--- run B exit=0 lf-sha16=%s ---" % lf_b,
        out_b.rstrip("\n"),
        "double-run byte-identical: YES",
        ("orphan cross-match: raw-stream sha16 %s == orphan"
         " evidence value (chain closure; raw stream = child"
         " stdout pre-LF-normalization, embedded bodies"
         " LF-normalized per the R2023/R2045 dialect law)"
         % raw_sha),
        "VERDICT PASS",
    ]
    content = "\n".join(body) + "\n"
    with io.open(EVID, "w", encoding="utf-8",
                newline="\n") as h:
        h.write(content)
    raw = open(EVID, "rb").read()
    if b"\r" in raw or raw.startswith(b"\xef\xbb\xbf"):
        die("rebuilt evidence not canonical utf-8 LF")
    print("TAKEOVER-VERIFY PASS: raw-sha16=%s cross-match "
          "orphan=%s MATCH; lf-sha16=%s; evidence rebuilt "
          "canonical python-single-writer utf-8 LF (%d bytes)"
          % (raw_sha, EXPECT_SHA16, lf_a, len(raw)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
