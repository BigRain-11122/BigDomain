"""Suite-matrix default-evidence discovery-face tests (R1708, P2
tech-queue head; AC-SM1..SM7 pre-registered in state/queue/tech.md
claim row, before this file existed - honesty law).

The R1695 naming gap: suite_matrix.default_evidence() used to glob
reconcile-all-R*.log only, so whenever the freshest full-regression
record shipped inside a suite evidence log (R1695 showroom log,
R1703 window-cap log) the default face could not see it and the
operator had to pass --evidence explicitly. The fix walks every
qa/*.log newest-by-mtime and takes the first eligible one (AC-SM1),
with four fail-closed eligibility checks (AC-SM2).

Fixture states run against a monkeypatched QA_DIR (AC-SM3) - the
live qa/ directory is never touched by the fixture cases; the live
case (case 7) is read-only and asserted as "newest eligible", not
against a pinned filename, so it survives future rounds.

Explicit --evidence stays lenient by design (AC-SM4): absent suites
are labeled no-evidence instead of refused; validation lives only
in the default discovery face.
"""

import os
import re
import subprocess
import sys
import tempfile

import suite_matrix as SM

MINI_EVIDENCE = (
    "PASS suite ledger exit=0 pass-lines=11 fail-lines=0"
    " criteria=11 0.5s\n"
    "PASS suite lobby exit=0 pass-lines=16 fail-lines=0"
    " criteria=16 0.3s\n"
    "RUNNER PASS (2/2 suites green, reconcile controls 6/6, 0.8s)\n")


def _write(path, text, mtime=None):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def _runner_fail_evidence():
    return MINI_EVIDENCE.replace("RUNNER PASS (2/2", "RUNNER FAIL (1/2")


def _with_qa_dir(tmp):
    """Bind SM.QA_DIR to a fixture dir; returns the real value for
    restore. os.listdir/getmtime in default_evidence read the module
    global at call time, so rebinding works."""
    saved = SM.QA_DIR
    SM.QA_DIR = tmp
    return saved


def case_fixture_gap_replay(tmp):
    """AC-SM3 state 1 (R1695 gap shape): newest eligible evidence
    lives outside the reconcile-all-R* naming family; new face must
    find it, old glob face would not."""
    old = os.path.join(tmp, "reconcile-all-R1699.log")
    new = os.path.join(tmp, "showroom-R1700.log")
    _write(old, MINI_EVIDENCE, mtime=1_700_000_000)
    _write(new, MINI_EVIDENCE, mtime=1_700_000_100)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        # old-face control group (inlined, glob+max-round semantics)
        import glob
        legacy_best = None
        for path in glob.glob(os.path.join(tmp, "reconcile-all-R*.log")):
            match = re.search(r"R(\d+)", os.path.basename(path))
            if match and (legacy_best is None
                          or int(match.group(1)) > int(re.search(
                              r"R(\d+)", os.path.basename(legacy_best)
                          ).group(1))):
                legacy_best = path
        assert picked == new, "new face must pick newest eligible"
        assert legacy_best == old, "old glob face picks by name family"
        assert picked != legacy_best, "gap replay must differ"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-gap-replay: new face picked %s, old glob face"\
           " would have picked %s (naming-gap difference proven)" % (
               os.path.basename(new), os.path.basename(old))


def case_fixture_none_eligible(tmp):
    """AC-SM3 state 2: no eligible log -> None -> main() exit 2
    (existing fail-closed path, called in-process so the QA_DIR
    monkeypatch applies)."""
    _write(os.path.join(tmp, "notes.log"), "some prose, no runner\n")
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked is None, "must return None when nothing parses"
        out_path = os.path.join(tmp, "doc.md")
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            # expected refusal banner stays out of this suite's own
            # output so the runner's ^FAIL\b count is not polluted
            code = SM.main(["suite_matrix.py", "--out", out_path])
        assert code == 2, "main must exit 2 with no default evidence"
        assert not os.path.exists(out_path), "no doc on refusal"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-none-eligible: default None + main exit=2"


def case_fixture_runner_fail_fallback(tmp):
    """AC-SM3 state 3: newest log is RUNNER FAIL -> skipped, next
    eligible PASS log wins (FAIL evidence stays reachable via
    explicit --evidence; R1684 discovery-face precedent)."""
    newest = os.path.join(tmp, "z-newest-fail.log")
    older = os.path.join(tmp, "a-older-pass.log")
    _write(newest, _runner_fail_evidence(), mtime=1_700_000_200)
    _write(older, MINI_EVIDENCE, mtime=1_700_000_100)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked == older, "must fall back past RUNNER FAIL"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-runner-fail-fallback: skipped %s, picked %s" % (
        os.path.basename(newest), os.path.basename(older))


def case_fixture_self_evidence_skip(tmp):
    """AC-SM3 state 4: suite-matrix-* self evidence is skipped even
    when newest and eligible (anti self-pointing; this tool's own
    evidence logs embed regression sections)."""
    self_log = os.path.join(tmp, "suite-matrix-self-R9999.log")
    other = os.path.join(tmp, "a-other.log")
    _write(self_log, MINI_EVIDENCE, mtime=1_700_000_300)
    _write(other, MINI_EVIDENCE, mtime=1_700_000_100)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked == other, "self evidence must be skipped"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-self-evidence-skip: skipped %s, picked %s" % (
        os.path.basename(self_log), os.path.basename(other))


def case_fixture_duplicate_labels_refused(tmp):
    """AC-SM2 check 3: duplicate suite labels -> ineligible."""
    dup = os.path.join(tmp, "z-dup.log")
    dup_text = MINI_EVIDENCE + MINI_EVIDENCE.splitlines()[0] + "\n"
    _write(dup, dup_text, mtime=1_700_000_300)
    other = os.path.join(tmp, "a-clean.log")
    _write(other, MINI_EVIDENCE, mtime=1_700_000_100)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked == other, "duplicate-label log must be refused"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-duplicate-labels-refused: fell to %s" % (
        os.path.basename(other))


def case_fixture_count_mismatch_refused(tmp):
    """AC-SM2 check 4: suite-line count != RUNNER total -> ineligible
    (guards against partially copied evidence)."""
    bad = os.path.join(tmp, "z-short.log")
    _write(bad, MINI_EVIDENCE.rsplit("\n", 1)[0] +
           "\nRUNNER PASS (2/2 suites green, reconcile controls 6/6,"
           " 0.8s)\nPASS suite ledger exit=0 pass-lines=11"
           " fail-lines=0 criteria=11 0.5s\n", mtime=1_700_000_300)
    other = os.path.join(tmp, "a-clean.log")
    _write(other, MINI_EVIDENCE, mtime=1_700_000_100)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked == other, "count-mismatch log must be refused"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-count-mismatch-refused: fell to %s" % (
        os.path.basename(other))


def case_live_default_discovery(tmp):
    """AC-SM5 live face: on the real qa/ the default must return the
    NEWEST ELIGIBLE log (recomputed here independently), not any
    pinned filename - survives future rounds."""
    picked = SM.default_evidence()
    assert picked is not None, "live qa/ must hold eligible evidence"
    assert SM._evidence_eligible(picked), "picked log must be eligible"
    names = [name for name in os.listdir(SM.QA_DIR)
             if name.endswith(".log")
             and not name.startswith("suite-matrix-")]
    best = None
    for name in sorted(names,
                       key=lambda n: (-os.path.getmtime(
                           os.path.join(SM.QA_DIR, n)), n)):
        if SM._evidence_eligible(os.path.join(SM.QA_DIR, name)):
            best = os.path.join(SM.QA_DIR, name)
            break
    assert os.path.basename(picked) == os.path.basename(best), \
        "live default must equal newest eligible by mtime"
    return "PASS live-default-discovery: newest eligible = %s" % (
        os.path.basename(picked))


def case_explicit_evidence_lenient(tmp):
    """AC-SM4: explicit --evidence stays lenient - a runner-line-only
    log (zero suite lines) is accepted, every registry suite lands
    no-evidence (fail-closed labeling, never fabricated)."""
    runner_only = os.path.join(tmp, "runner-only.log")
    _write(runner_only,
           "RUNNER PASS (2/2 suites green, reconcile controls 6/6,"
           " 0.8s)\n")
    status, run = SM.parse_evidence(runner_only)
    assert status == {} and run is not None and run["verdict"] == "PASS"
    out_path = os.path.join(tmp, "doc-lenient.md")
    proc = subprocess.run(
        [sys.executable, SM.__file__, "--evidence", runner_only,
         "--out", out_path], capture_output=True, text=True)
    assert proc.returncode == 0, "explicit lenient face must exit 0"
    with open(out_path, encoding="utf-8") as handle:
        doc = handle.read()
    assert "no-evidence %d" % len(SM.RA.SUITES) in doc, \
        "all registry suites must be labeled no-evidence"
    return "PASS explicit-evidence-lenient: runner-only log accepted,"\
           " %d suites no-evidence" % len(SM.RA.SUITES)


def case_check_roundtrip_tmp(tmp):
    """AC-SM4/Semantics: generate against a fixture evidence log,
    then --check byte-identical exit 0; tamper -> stale exit 2."""
    ev = os.path.join(tmp, "a-evidence.log")
    _write(ev, MINI_EVIDENCE)
    out_path = os.path.join(tmp, "doc-rt.md")
    base = [sys.executable, SM.__file__, "--evidence", ev,
            "--out", out_path]
    proc = subprocess.run(base, capture_output=True, text=True)
    assert proc.returncode == 0, "generate must exit 0"
    proc = subprocess.run(base + ["--check"], capture_output=True,
                           text=True)
    assert proc.returncode == 0, "check must be byte-identical exit 0"
    with open(out_path, encoding="utf-8") as handle:
        doc = handle.read()
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(doc.replace("| 1 |", "| 9 |", 1))
    proc = subprocess.run(base + ["--check"], capture_output=True,
                          text=True)
    assert proc.returncode == 2, "tampered doc must be flagged exit 2"
    return "PASS check-roundtrip-tmp: identical exit 0, tamper exit 2"


def case_hygiene_self_checks(tmp):
    """AC-SM6: self_checks() clean on the current source."""
    problems = SM.self_checks()
    assert problems == [], "hygiene problems: %r" % problems
    return "PASS hygiene-self-checks: pure-ascii, zero network imports"


def main():
    cases = [
        case_fixture_gap_replay,
        case_fixture_none_eligible,
        case_fixture_runner_fail_fallback,
        case_fixture_self_evidence_skip,
        case_fixture_duplicate_labels_refused,
        case_fixture_count_mismatch_refused,
        case_live_default_discovery,
        case_explicit_evidence_lenient,
        case_check_roundtrip_tmp,
        case_hygiene_self_checks,
    ]
    failures = 0
    for case in cases:
        handle = tempfile.mkdtemp(prefix="sm-fix-")
        try:
            line = case(handle)
        except AssertionError as exc:
            failures += 1
            print("FAIL %s: %s" % (case.__name__, exc))
            continue
        except Exception as exc:  # noqa: BLE001 (report, keep going)
            failures += 1
            print("FAIL %s raised %r" % (case.__name__, exc))
            continue
        finally:
            import shutil
            shutil.rmtree(handle, ignore_errors=True)
        print(line)
    print("SUITE %s (%d/%d cases)"
          % ("PASS" if failures == 0 else "FAIL",
             len(cases) - failures, len(cases)))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
