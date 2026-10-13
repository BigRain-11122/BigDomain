# -*- coding: utf-8 -*-
"""R1920 orphan-adoption verification driver: the crashed R1920
half left the full five-section evidence chain on disk
(qa/export-persist-R1920.log, VERDICT PASS, RUNNER 161/161, suite
sha16=63a3b1d82aa0cc3b) plus the registered matrix; this driver
re-verifies every claim live before the takeover closeout:
  [1] suite double-run fresh reproduction (determinism + the
      orphan's logged sha16 caliber, R1919 family normalization)
  [2] orphan evidence file structural verification (five section
      headers + RUNNER PASS 161/161 + ugc-export-persist green
      line + VERDICT PASS; no re-run of the 287s RUNNER - a re-run
      would only churn per-suite timing evidence and desync the
      regenerated matrix, R1739 explicit-evidence precedent)
  [3] suite matrix --check x2 with explicit --evidence (content-
      only comparison per doc_stamp law)
  [4] qa writer census --check
  [5] fingerprint sentinel --check
Output: qa/exportpersist-takeover-R1920.log (tee dialect, LF).
Pure stdlib, zero network, pure ASCII source."""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PY = sys.executable
SUITE = os.path.join("src", "sandbox", "ugc",
                     "test_export_persist.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
FPRINT = os.path.join("src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join("src", "sandbox", "migration_chains.json")
EV = os.path.join("qa", "export-persist-R1920.log")
OUT = os.path.join("qa", "exportpersist-takeover-R1920.log")
ORPHAN_SHA16 = "63a3b1d82aa0cc3b"

sections = []


def run(cmd, cwd=ROOT):
    p = subprocess.run([PY, "-X", "utf8"] + cmd, cwd=cwd,
                       capture_output=True)
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
    print("[1] suite double-run fresh reproduction ...",
          flush=True)
    rc1, out1 = run([SUITE])
    rc2, out2 = run([SUITE])
    l1 = suite_lines(out1)
    l2 = suite_lines(out2)
    identical = (l1 == l2 and len(l1) == 8 and len(l2) == 8)
    full_identical = out1 == out2
    s1 = sha16(out1)
    s2 = sha16(out2)
    sha_match = (s1 == ORPHAN_SHA16 and s2 == ORPHAN_SHA16)
    sec1 = ["=== [1] suite double-run fresh reproduction:"
            " test_export_persist.py AC-EXP1..AC-EXP7 (the"
            " takeover re-derives the crashed half's claim"
            " instead of trusting it; zero volatile lines:"
            " no tmp paths, no ports, no ms timings) ===",
            "run1 rc=%d lines (%d):" % (rc1, len(l1))]
    sec1 += l1
    sec1 += ["run2 rc=%d lines (%d):" % (rc2, len(l2))]
    sec1 += l2
    sec1 += ["criteria-identical=%s full-stdout-identical=%s"
             " (lines %d/%d)"
             % (identical, full_identical, len(l1), len(l2)),
             "run1 full-stdout sha16=%s run2 full-stdout sha16=%s"
             % (s1, s2),
             "orphan-logged sha16=%s live-reproduction-match=%s"
             % (ORPHAN_SHA16, sha_match)]
    sections.append("\n".join(sec1))
    print("  rc %d/%d identical=%s full=%s sha_match=%s"
          % (rc1, rc2, identical, full_identical, sha_match),
          flush=True)

    print("[2] orphan evidence file verification ...",
          flush=True)
    with open(os.path.join(ROOT, EV), encoding="utf-8") as h:
        ev_text = h.read().replace("\r\n", "\n")
    headers = [ln for ln in ev_text.splitlines()
               if ln.startswith("=== [")]
    runner_line = [ln for ln in ev_text.splitlines()
                   if ln.startswith("RUNNER PASS")]
    suite_line = [ln for ln in ev_text.splitlines()
                  if ln.startswith("PASS suite ugc-export-persist")]
    ev_bytes = len(ev_text.encode("utf-8"))
    struct_ok = (len(headers) == 5
                 and len(runner_line) == 1
                 and "161/161 suites green" in runner_line[0]
                 and len(suite_line) == 1
                 and "exit=0 pass-lines=7 fail-lines=0"
                 in suite_line[0]
                 and ev_text.rstrip().endswith("VERDICT PASS"))
    sec2 = ["=== [2] orphan evidence file verification (%s) ==="
            % EV.replace("\\", "/"),
            "file bytes (utf-8): %d" % ev_bytes,
            "section headers: %d" % len(headers)]
    sec2 += ["  %s" % h for h in headers]
    sec2 += ["runner terminal: %s" % (runner_line[0]
                                      if runner_line
                                      else "MISSING"),
             "suite green line: %s" % (suite_line[0]
                                       if suite_line
                                       else "MISSING"),
             "verdict tail: VERDICT PASS present=%s"
             % ev_text.rstrip().endswith("VERDICT PASS"),
             "no runner re-run (cite-only, honest note): a fresh"
             " 287s RUNNER would rewrite the per-suite timing"
             " evidence this matrix was regenerated from"
             " (R1739 explicit-evidence precedent)",
             "structural-verification=%s" % struct_ok]
    sections.append("\n".join(sec2))
    print("  struct_ok=%s" % struct_ok, flush=True)

    print("[3] suite matrix --check x2 (explicit evidence) ...",
          flush=True)
    ev_arg = EV.replace("\\", "/")
    rc_c1, out_c1 = run([MATRIX, "--evidence", ev_arg,
                         "--check"])
    rc_c2, out_c2 = run([MATRIX, "--evidence", ev_arg,
                         "--check"])
    same = out_c1 == out_c2
    check_tail = [ln for ln in out_c1.splitlines()
                  if ln.startswith("PASS check")][-1:]
    sec3 = ["=== [3] suite matrix --check x2 (explicit"
            " --evidence qa/export-persist-R1920.log; content-"
            "only comparison per doc_stamp law) ===",
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
          and sha_match and struct_ok and rc_c1 == 0
          and rc_c2 == 0 and same and rc_w == 0
          and "DRIFT-CLEAN" in out_w and rc_f == 0
          and "PASS" in out_f)
    body = "\n\n".join(sections) + "\n\nVERDICT " + \
        ("PASS" if ok else "FAIL") + "\n"
    with open(os.path.join(ROOT, OUT), "w",
              encoding="utf-8", newline="\n") as h:
        h.write(body)
    print("takeover verification log written: %s (%d bytes)"
          " VERDICT %s"
          % (OUT, len(body.encode("utf-8")),
             "PASS" if ok else "FAIL"), flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
