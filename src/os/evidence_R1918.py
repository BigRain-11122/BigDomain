# -*- coding: utf-8 -*-
"""R1918 evidence-chain driver: five sections into
qa/birthcert-persist-R1918.log (the R1908-R1917
evidence_precedent structure, evidence_R1915 clone).
Pure stdlib, zero network."""
import hashlib
import os
import subprocess
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PY = sys.executable
SUITE = os.path.join("src", "sandbox", "member",
                     "test_birthcert_persist.py")
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
FPRINT = os.path.join("src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join("src", "sandbox", "migration_chains.json")
RUNNER_LOG = os.path.join("qa", "reconcile-all-R1918.log")
OUT = os.path.join("qa", "birthcert-persist-R1918.log")

sections = []


def run(cmd, cwd=ROOT):
    p = subprocess.run([PY, "-X", "utf8"] + cmd, cwd=cwd,
                       capture_output=True)
    # R1880/R1883 family law: child stdout arrives CRLF on the
    # Windows pipe; normalize before any byte hits the evidence
    # file (writer-dialect discipline - the log must land tee).
    return (p.returncode,
            p.stdout.decode("utf-8", "replace")
            .replace("\r\n", "\n"))


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def suite_lines(out):
    return [ln for ln in out.splitlines()
            if ln.startswith("PASS ") or ln.startswith("FAIL ")
            or ln.startswith("SUITE ")]


def main():
    print("[1] suite double-run ...", flush=True)
    rc1, out1 = run([SUITE])
    rc2, out2 = run([SUITE])
    l1 = suite_lines(out1)
    l2 = suite_lines(out2)
    identical = (l1 == l2 and len(l1) == 8 and len(l2) == 8)
    full_identical = out1 == out2
    sec1 = ["=== [1] suite double-run: test_birthcert_persist.py"
            " AC-BCP1..AC-BCP7 (full stdout carries zero volatile"
            " lines: no tmp paths, no ports, no ms timings) ===",
            "run1 rc=%d lines (%d):" % (rc1, len(l1))]
    sec1 += l1
    sec1 += ["run2 rc=%d lines (%d):" % (rc2, len(l2))]
    sec1 += l2
    sec1 += ["criteria-identical=%s full-stdout-identical=%s"
             " (lines %d/%d)"
             % (identical, full_identical, len(l1), len(l2)),
             "run1 full-stdout sha16=%s run2 full-stdout sha16=%s"
             % (sha16(out1), sha16(out2))]
    sections.append("\n".join(sec1))
    print("  suite rc %d/%d identical=%s full=%s"
          % (rc1, rc2, identical, full_identical), flush=True)

    print("[2] RUNNER full regression ...", flush=True)
    rc_r, out_r = run([RUNNER, RUNNER_LOG])
    tail_r = [ln for ln in out_r.splitlines()
              if ln.startswith("RUNNER")]
    sec2 = ["=== [2] RUNNER full regression ===",
            "runner rc=%d (runner Tee evidence = %s)"
            % (rc_r, RUNNER_LOG)]
    sec2 += tail_r if tail_r else [out_r[-400:]]
    sections.append("\n".join(sec2))
    print("  runner rc=%d %s"
          % (rc_r, tail_r[-1] if tail_r else "?"), flush=True)

    print("[3] suite matrix regen + --check x2 ...", flush=True)
    rc_g, out_g = run([MATRIX])
    rc_c1, out_c1 = run([MATRIX, "--check"])
    rc_c2, out_c2 = run([MATRIX, "--check"])
    same = out_c1 == out_c2
    check_tail = [ln for ln in out_c1.splitlines()
                  if ln.startswith("PASS check")][-1:]
    sec3 = ["=== [3] suite matrix regen + --check x2 ===",
            "regen rc=%d" % rc_g,
            "check1 rc=%d check2 rc=%d byte-identical=%s"
            % (rc_c1, rc_c2, same),
            "check tail: %s" % (check_tail[0] if check_tail
                                else "NO-CHECK-LINE")]
    sections.append("\n".join(sec3))
    print("  matrix %s" % (check_tail[0] if check_tail else "?"),
          flush=True)

    print("[4] qa writer census --check ...", flush=True)
    rc_w, out_w = run([CENSUS, "--check"])
    verdict_w = [ln for ln in out_w.splitlines()
                 if ln.startswith("verdict")]
    sec4 = ["=== [4] qa writer census --check ===",
            out_w.rstrip(), "census rc=%d" % rc_w]
    sections.append("\n".join(sec4))
    print("  census %s" % (verdict_w[-1] if verdict_w else "?"),
          flush=True)

    print("[5] fingerprint sentinel ...", flush=True)
    rc_f, out_f = run([FPRINT, "--chain", CHAIN, "--check"])
    sec5 = ["=== [5] fingerprint sentinel ===",
            out_f.rstrip(), "sentinel rc=%d" % rc_f]
    sections.append("\n".join(sec5))
    print("  sentinel rc=%d" % rc_f, flush=True)

    ok = (rc1 == 0 and rc2 == 0 and identical and full_identical
          and rc_r == 0 and rc_g == 0 and rc_c1 == 0 and rc_c2 == 0
          and same and rc_w == 0 and "DRIFT-CLEAN" in out_w
          and rc_f == 0 and "PASS" in out_f)
    body = "\n\n".join(sections) + "\n\nVERDICT " + \
        ("PASS" if ok else "FAIL") + "\n"
    with open(os.path.join(ROOT, OUT), "w",
              encoding="utf-8", newline="\n") as h:
        h.write(body)
    print("evidence log written: %s (%d bytes) VERDICT %s"
          % (OUT, len(body), "PASS" if ok else "FAIL"),
          flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
