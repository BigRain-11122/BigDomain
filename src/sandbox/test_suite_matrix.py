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

R1709 (AC-TIE1..TIE7, pre-registered in state/queue/tech.md before
these cases existed): the four fixture states never covered the
same-mtime tie shape a git checkout produces - every qa/ file then
gets one restoration mtime and discovery falls entirely onto the
name key. Five cases pin the tie semantics: name-asc resolution,
in-tie-group skip past an ineligible file, a fully flattened tree
with repeated-call determinism, enumeration-order independence
(reversed os.listdir), and a live determinism/tie probe.

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


def case_fixture_tie_name_asc(tmp):
    """AC-TIE1: three eligible files share ONE mtime -> the (mtime
    desc, name asc) key pair falls through to the name key; the
    lexicographically smallest name must win (post-checkout shape
    where every file gets the same restoration mtime)."""
    tie = 1_700_000_400
    for name in ("z-zed.log", "m-mid.log", "a-ace.log"):
        _write(os.path.join(tmp, name), MINI_EVIDENCE, mtime=tie)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked == os.path.join(tmp, "a-ace.log"), \
            "tie group must resolve to the smallest name"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-tie-name-asc: 3-way same-mtime tie -> %s" % (
        os.path.basename(picked))


def case_fixture_tie_ineligible_mix(tmp):
    """AC-TIE2: within ONE same-mtime group an ineligible file
    (RUNNER FAIL, smallest name) is skipped and discovery continues
    INSIDE the tie group to the eligible file - it must not fall
    through to the older mtime group."""
    tie = 1_700_000_400
    fail_first = os.path.join(tmp, "a-fail.log")
    tie_pass = os.path.join(tmp, "z-tie-pass.log")
    old_pass = os.path.join(tmp, "m-old-pass.log")
    _write(fail_first, _runner_fail_evidence(), mtime=tie)
    _write(tie_pass, MINI_EVIDENCE, mtime=tie)
    _write(old_pass, MINI_EVIDENCE, mtime=tie - 100)
    saved = _with_qa_dir(tmp)
    try:
        picked = SM.default_evidence()
        assert picked == tie_pass, \
            "must continue inside the tie group past ineligible file"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-tie-ineligible-mix: skipped %s inside tie," \
           " picked %s (older %s not reached)" % (
               os.path.basename(fail_first), os.path.basename(tie_pass),
               os.path.basename(old_pass))


def case_fixture_all_flattened(tmp):
    """AC-TIE3: git-checkout simulation - EVERY file in the fixture
    dir shares one mtime (mixed eligible/ineligible). Discovery must
    stay deterministic: the unique winner is the smallest-named
    eligible file, and three consecutive calls return the same path
    (os.listdir order is not stable across calls)."""
    flat = 1_700_000_400
    _write(os.path.join(tmp, "z-fail.log"), _runner_fail_evidence(),
           mtime=flat)
    _write(os.path.join(tmp, "m-mid.log"), MINI_EVIDENCE, mtime=flat)
    _write(os.path.join(tmp, "a-ace.log"), MINI_EVIDENCE, mtime=flat)
    _write(os.path.join(tmp, "notes.log"), "prose, no runner\n",
           mtime=flat)
    saved = _with_qa_dir(tmp)
    try:
        picks = [SM.default_evidence() for _ in range(3)]
        assert picks[0] == os.path.join(tmp, "a-ace.log"), \
            "flattened tree must resolve to smallest eligible name"
        assert picks[0] == picks[1] == picks[2], \
            "three consecutive calls must agree byte-for-byte"
    finally:
        SM.QA_DIR = saved
    return "PASS fixture-all-flattened: 4 files one mtime -> %s x3" \
        % os.path.basename(picks[0])


def case_listdir_order_independence(tmp):
    """AC-TIE4: os.listdir is monkeypatched to return entries in
    REVERSE order - the discovery sort key must fully absorb the
    enumeration order (the winner must not depend on directory
    enumeration luck)."""
    tie = 1_700_000_400
    expected = os.path.join(tmp, "a-ace.log")
    _write(expected, MINI_EVIDENCE, mtime=tie)
    _write(os.path.join(tmp, "z-zed.log"), MINI_EVIDENCE, mtime=tie)
    saved_dir = _with_qa_dir(tmp)
    saved_listdir = os.listdir
    try:
        def reversed_listdir(path):
            return list(reversed(saved_listdir(path)))
        os.listdir = reversed_listdir
        picked = SM.default_evidence()
        assert picked == expected, \
            "reversed listdir must not change the tie winner"
    finally:
        os.listdir = saved_listdir
        SM.QA_DIR = saved_dir
    return "PASS listdir-order-independence: reversed enumeration ->" \
           " same winner %s" % os.path.basename(expected)


def case_live_tie_probe(tmp):
    """AC-TIE5: live determinism - three consecutive live calls agree
    byte-for-byte; tie status is reported honestly (if eligible files
    share the winner's exact mtime, the winner must be the smallest
    name among them; otherwise reported as no-live-tie)."""
    picks = [SM.default_evidence() for _ in range(3)]
    assert picks[0] is not None, "live qa/ must hold eligible evidence"
    assert picks[0] == picks[1] == picks[2], "live calls must agree"
    winner = picks[0]
    names = [name for name in os.listdir(SM.QA_DIR)
             if name.endswith(".log")
             and not name.startswith("suite-matrix-")]
    win_mtime = os.path.getmtime(winner)
    tie_peers = [name for name in names
                 if os.path.getmtime(os.path.join(SM.QA_DIR, name))
                 == win_mtime
                 and SM._evidence_eligible(
                     os.path.join(SM.QA_DIR, name))]
    if len(tie_peers) > 1:
        assert os.path.basename(winner) == min(tie_peers), \
            "live tie: winner must be smallest name among tie peers"
    return "PASS live-tie-probe: %s x3 identical, tie_peers=%d%s" % (
        os.path.basename(winner), len(tie_peers),
        "" if len(tie_peers) > 1 else " (no live tie)")


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
        case_fixture_tie_name_asc,
        case_fixture_tie_ineligible_mix,
        case_fixture_all_flattened,
        case_listdir_order_independence,
        case_live_tie_probe,
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
