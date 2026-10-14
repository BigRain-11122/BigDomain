# -*- coding: utf-8 -*-
"""R1953 takeover closeout evidence driver (orphan-payload
takeover, tenth case of the R1924/R1937/R1940/R1949/R1952
lineage). The crashed R1953 attempt delivered the full suite
payload (pre-registered criteria + suite source + RUNNER
registration + double-run evidence, verdict PASS) and crashed
before its RUNNER/matrix/census/fingerprint/bookkeeping steps
(state.json untouched at tick 1952). This round verified the
orphan live (single re-run rc=0 SUITE PASS 7/7 - the crashed
round's own double-run byte-identity sha16 6efe271a7c958624
stands as the canonical determinism evidence per the R1952
precedent) and now runs the missing closeout sections, appended
to the crashed round's evidence log as a takeover addendum
(LF single-writer, crashed content preserved as-is per the
evidence-integrity law). Pure stdlib, zero network, ASCII."""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PY = sys.executable
RUNNER = os.path.join("src", "sandbox", "reconcile_all.py")
MATRIX = os.path.join("src", "sandbox", "suite_matrix.py")
CENSUS = os.path.join("src", "os", "qa_writer_census.py")
FPRINT = os.path.join("src", "sandbox", "fingerprint_regen.py")
CHAIN = os.path.join("src", "sandbox", "migration_chains.json")
OUT = os.path.join("qa", "sistercity-persist-R1953.log")


def run(cmd):
    p = subprocess.run([PY, "-X", "utf8"] + cmd, cwd=ROOT,
                       capture_output=True)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace").replace("\r\n", "\n"),
            p.stderr.decode("utf-8", "replace").replace("\r\n", "\n"))


def main():
    with open(os.path.join(ROOT, OUT), "rb") as fh:
        raw = fh.read()
    log = raw.decode("utf-8")
    assert log.rstrip().endswith("verdict PASS"), (
        "crashed log tail is not the PASS verdict line")
    assert "takeover addendum" not in log, (
        "addendum already present")
    # R1884 capture-normalization law (R1952 addendum precedent):
    # the crashed round's driver wrote the suite stdout raw (its
    # run_once lacked the CRLF->LF replace the R1951 template
    # carries - Windows python text-mode pipes emit CRLF), so 8
    # suite lines carry CRLF. Content preserved; the whole file
    # is normalized to pure LF = the tee class, the healthy
    # census dialect.
    log = log.replace("\r\n", "\n")
    assert "\r" not in log, "CR survives normalization"
    if not log.endswith("\n"):
        log += "\n"
    # Write the normalized [1] content to disk BEFORE the steps:
    # the RUNNER's daily-census cd7 live-tree probe and the [4]
    # census --check both scan qa/ mid-run; leaving the CRLF pairs
    # on disk until the end (the first attempt's timing) makes the
    # live census flag class=other drift and fails cd7. Normalize
    # first, then run.
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(log)
    print("normalized [1] content written to disk first", flush=True)

    sections = []

    print("[2] RUNNER full regression ...", flush=True)
    rc2, o2, e2 = run([RUNNER])
    with open(os.path.join(ROOT, "qa", "reconcile-all-R1953.log"),
              "w", encoding="utf-8", newline="\n") as fh:
        fh.write(o2)
        if o2 and not o2.endswith("\n"):
            fh.write("\n")
    sections.append("--- [2] RUNNER (rc %s) tail ---\n%s"
                    % (rc2, "\n".join(o2.splitlines()[-12:])))
    print("    rc=%s" % rc2, flush=True)

    print("[3] suite matrix regen + --check ...", flush=True)
    rc3, o3, _ = run([MATRIX])
    sections.append("--- [3] matrix regen (rc %s) ---\n%s"
                    % (rc3, o3[-800:]))
    rc4, o4, _ = run([MATRIX, "--check"])
    sections.append("--- [3b] matrix --check (rc %s) ---\n%s"
                    % (rc4, o4[-400:]))
    print("    regen rc=%s check rc=%s" % (rc3, rc4), flush=True)

    print("[4] qa writer census --check ...", flush=True)
    rc5, o5, _ = run([CENSUS, "--check"])
    sections.append("--- [4] census --check (rc %s) ---\n%s"
                    % (rc5, o5[-600:]))
    print("    rc=%s" % rc5, flush=True)

    print("[5] fingerprint sentinel --check ...", flush=True)
    rc6, o6, _ = run([FPRINT, "--chain", CHAIN, "--check"])
    sections.append("--- [5] fingerprint --check (rc %s) ---\n%s"
                    % (rc6, o6[-600:]))
    print("    rc=%s" % rc6, flush=True)

    print("[6] git status hygiene ...", flush=True)
    p = subprocess.run(["git", "status", "--short"], cwd=ROOT,
                       capture_output=True)
    tree = (p.stdout.decode("utf-8", "replace")
            .replace("\r\n", "\n"))
    sections.append("--- [6] git status --short ---\n%s" % tree)
    print("    dirty lines=%d" % len(tree.splitlines()), flush=True)

    verdict = (rc2 == 0 and rc4 == 0 and rc5 == 0 and rc6 == 0)
    addendum_head = (
        "--- [7] takeover addendum (R1953 closeout; orphan-payload\n"
        "takeover per the R1924/R1937/R1940/R1949/R1952 lineage,\n"
        "tenth case) ---\n"
        "context: the crashed R1953 attempt left the full payload\n"
        "on disk (pre-registered AC-SCP1..SCP7 criteria in\n"
        "state/queue/tech.md + suite source + RUNNER registration\n"
        "+ [1] double-run evidence verdict PASS) and crashed before\n"
        "its RUNNER/matrix/census/fingerprint/bookkeeping steps\n"
        "(state.json untouched at tick 1952). This closeout round\n"
        "verified the orphan live: suite single re-run rc=0 SUITE\n"
        "PASS 7/7 (all seven AC-SCP lines PASS; the crashed round's\n"
        "own double-run byte-identity sha16 6efe271a7c958624 stands\n"
        "as the canonical determinism evidence per the R1952\n"
        "precedent) and then ran the missing closeout sections\n"
        "above (LF single-writer; crashed [1] content preserved\n"
        "as-is per the evidence-integrity law).\n"
        "dialect note: the crashed round's evidence driver wrote\n"
        "the suite stdout raw - its run_once lacked the CRLF->LF\n"
        "replace the R1951 template carries (Windows python\n"
        "text-mode pipes emit CRLF), leaving 8 CRLF pairs in the\n"
        "crashed [1] section. Per the R1884 capture-normalization\n"
        "law (R1952 addendum precedent) the whole file is\n"
        "normalized to pure LF = the tee class, the healthy census\n"
        "dialect; content preserved.\n"
        "first-attempt note: this closeout's first driver run\n"
        "failed twice by its own wiring - it normalized the [1]\n"
        "content only in memory (so the RUNNER's cd7 live-tree\n"
        "census probe and the [4] census --check still saw the 8\n"
        "CRLF pairs on disk and flagged class=other drift, RUNNER\n"
        "rc=1 exactly the R1952 crashed-run signature), and its\n"
        "ruling line was hardcoded VERDICT PASS regardless of the\n"
        "real verdict (honesty-law violation, caught by the\n"
        "driver's own stdout VERDICT FAIL before any bookkeeping;\n"
        "evidence file restored to the crashed [1] base by\n"
        "restore_R1953.py, driver fixed: disk-write the\n"
        "normalized content first, ruling carries the real\n"
        "verdict). This re-run is the canonical closeout.\n")
    ruling = ("VERDICT %s (takeover closeout ruling: [1] SUITE 7/7\n"
              "double-run identical + [2] RUNNER rc=%s + [3]/[3b]\n"
              "matrix --check byte-identical rc=%s + [4] census\n"
              "rc=%s + [5] fingerprint rc=%s)\n"
              % ("PASS" if verdict else "FAIL", rc2, rc4, rc5, rc6))
    body = "\n".join(sections)
    log += addendum_head + body
    if not log.endswith("\n"):
        log += "\n"
    log += ruling
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(log)
    print("VERDICT %s" % ("PASS" if verdict else "FAIL"), flush=True)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
