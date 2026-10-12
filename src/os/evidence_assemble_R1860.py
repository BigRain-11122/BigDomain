"""R1860 evidence assembler: qa/sec-batch-statuswin-R1860.log
(builds the evidence file for the AC-SB18..SB22 delivery round).
Double-run determinism compare follows the R1850 convention: PROF
lines carry real wall-clock measurements (AC-SB3 declared face) and
are excluded from the byte-identity compare; every criteria line
(PASS/SUITE) must be byte-identical across runs."""

import hashlib
import os

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R1 = os.path.join(ROOT, ".codely-cli", "tmp", "r1860_run1.out")
R2 = os.path.join(ROOT, ".codely-cli", "tmp", "r1860_run2.out")
OUT = os.path.join(ROOT, "qa", "sec-batch-statuswin-R1860.log")


def sha16(data):
    return hashlib.sha256(data).hexdigest()[:16]


def read_any(path):
    """BOM-detecting read (PS5.1 redirection writes UTF-16LE; the
    known shell-capture dialect - writer-census family face)."""
    raw = open(path, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8")


def deterministic(ln):
    """R1855 convention: PROF lines AND the AC-SB3 PASS line carry
    real wall-clock readings (declared measurement face since R1681);
    everything else must be byte-identical across runs."""
    if ln.startswith("PROF "):
        return False
    if ln.startswith("PASS AC-SB3:"):
        return False
    return True


def main():
    r1 = open(R1, "rb").read()
    r2 = open(R2, "rb").read()
    # decode run captures BEFORE embedding: raw UTF-16LE bytes inside
    # a UTF-8 log make the file undecodable (writer-census class
    # "other" - the live-fire catch this round, fixed at source).
    # The PS capture also rides CRLF; normalize to LF so the whole
    # evidence file is the healthy tee dialect (utf-8 + zero CRLF).
    t1 = read_any(R1).replace("\r\n", "\n")
    t2 = read_any(R2).replace("\r\n", "\n")
    full_identical = t1 == t2
    l1 = [ln for ln in t1.splitlines() if deterministic(ln)]
    l2 = [ln for ln in t2.splitlines() if deterministic(ln)]
    filt_identical = l1 == l2
    crit1 = [ln for ln in l1 if ln.startswith("PASS ") or
             ln.startswith("FAIL ") or ln.startswith("SUITE ")]
    crit2 = [ln for ln in l2 if ln.startswith("PASS ") or
             ln.startswith("FAIL ") or ln.startswith("SUITE ")]
    crit_identical = crit1 == crit2
    sect1 = [ln for ln in crit1 if ln.startswith("PASS AC-SB18") or
             ln.startswith("PASS AC-SB19") or
             ln.startswith("PASS AC-SB20") or
             ln.startswith("PASS AC-SB21") or
             ln.startswith("PASS AC-SB22") or
             ln.startswith("SUITE ")]
    sect_identical = (sect1 ==
                      [ln for ln in crit2 if ln in set(sect1)])
    with open(OUT, "wb") as fh:
        w = lambda s: fh.write(s.encode("utf-8"))  # noqa: E731
        w("=== run1 stdout verbatim ===\n")
        fh.write(t1.encode("utf-8"))
        w("\n=== run2 stdout verbatim ===\n")
        fh.write(t2.encode("utf-8"))
        w("\n=== double-run determinism (R1855 convention) ===\n")
        w("run1 bytes=%d run2 bytes=%d\n" % (len(r1), len(r2)))
        w("run1 sha256=%s run2 sha256=%s\n"
          % (hashlib.sha256(r1).hexdigest(),
             hashlib.sha256(r2).hexdigest()))
        w("full-identical=%s (PROF lines and the AC-SB3 PASS line "
          "carry real wall-clock values - declared measurement "
          "faces since R1681)\n" % full_identical)
        w("filtered-lines (PROF + AC-SB3 excluded) %d/%d identical=%s"
          "\n" % (len(l1), len(l2), filt_identical))
        w("criteria-lines (PASS/FAIL/SUITE, PROF/AC-SB3 excluded) "
          "%d/%d byte-identical=%s\n"
          % (len(crit1), len(crit2), crit_identical))
        w("R1860-section (AC-SB18..SB22 + SUITE) %d lines "
          "byte-identical=%s\n" % (len(sect1), sect_identical))
    print("evidence written: %s" % OUT)
    print("full_identical=%s filt_identical=%s crit_identical=%s "
          "sect_identical=%s crit_lines=%d"
          % (full_identical, filt_identical, crit_identical,
             sect_identical, len(crit1)))
    assert filt_identical, "deterministic lines differ across runs"
    assert crit_identical, "criteria lines differ across runs"
    assert sect_identical, "R1860 section lines differ across runs"
    assert len(sect1) == 6, "R1860 section expected 6 lines"
    assert all(ln.startswith("PASS ") for ln in crit1[:-1])
    assert crit1[-1] == "SUITE PASS: 22/22", crit1[-1]


if __name__ == "__main__":
    main()
