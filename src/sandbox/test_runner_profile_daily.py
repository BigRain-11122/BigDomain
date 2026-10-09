"""Runner-profile daily-variant suite (R1715, P2 tech-queue item;
criteria AC-RD1..RD6 pre-registered in state/queue/tech.md before
this suite existed - honesty law).

The daily face is a discovery restriction + a separate baseline
file; parse_log must stay inert to the sentinel section that
reconcile_daily.py appends to its dated evidence logs. Fixtures
mirror the real daily-log shape; QA_DIR is monkeypatched to a temp
dir so the live qa/ population is never touched.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import runner_profile as RP  # noqa: E402 (module under test)


def write_log(dirpath, name, suites, runner_secs, sentinel=True,
              runner_fail=False):
    lines = []
    for label, secs in suites:
        lines.append("PASS suite %s exit=0 pass-lines=1 fail-lines=0 "
                     "criteria=1 %.1fs" % (label, secs))
    if runner_fail:
        lines.append("RUNNER FAIL (1/2 suites green, reconcile "
                     "controls 5/6, %.1fs)" % runner_secs)
    else:
        lines.append("RUNNER PASS (%d/%d suites green, reconcile "
                     "controls 6/6, %.1fs)"
                     % (len(suites), len(suites), runner_secs))
    if sentinel and not runner_fail:
        lines.append("--- sentinel: fingerprint-regen --check ---")
        lines.append("PASS domain=ledger baseline matches live "
                     "constructor (R1676 cross-validation)")
        lines.append("verdict CLEAN domains=5")
        lines.append("sentinel exit=0")
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def main():
    tmp = tempfile.mkdtemp(prefix="runner-profile-daily-suite-")
    saved_qa = RP.QA_DIR
    RP.QA_DIR = tmp
    problems = []
    try:
        daily = write_log(tmp, "reconcile-daily-20260999.log",
                          [("lobby", 5.0), ("pay", 9.5)], 14.5)
        # AC-RD2: the sentinel section is inert to the parser
        parsed = RP.parse_log(daily)
        ok = (len(parsed["suites"]) == 2
              and parsed["runner_total"] == 14.5)
        print("%s rd2-sentinel-section-inert (suites=%d)"
              % ("PASS" if ok else "FAIL", len(parsed["suites"])))
        if not ok:
            problems.append("rd2")
        # AC-RD1: face isolation - a newer non-daily log never leaks
        # into the daily population, and the main face still sees it
        newer = write_log(tmp, "reconcile-all-R9999.log",
                          [("ledger", 3.0)], 3.0, sentinel=False)
        os.utime(daily, (1000000, 1000000))
        os.utime(newer, (2000000, 2000000))
        d_path = RP.discover_daily()["path"]
        m_path = RP.discover_target()["path"]
        ok = (os.path.basename(d_path)
              == "reconcile-daily-20260999.log"
              and os.path.basename(m_path) == "reconcile-all-R9999.log")
        print("%s rd1-discovery-face-isolation (daily=%s main=%s)"
              % ("PASS" if ok else "FAIL",
                 os.path.basename(d_path), os.path.basename(m_path)))
        if not ok:
            problems.append("rd1-isolation")
        # AC-RD1: baseline split - --daily writes the daily file only
        code = RP.main(["runner_profile.py", "--daily", "--log", daily,
                        "--update-baseline"])
        dbase = RP.baseline_path(True)
        mbase = RP.baseline_path(False)
        ok = (code == 0 and os.path.exists(dbase)
              and not os.path.exists(mbase))
        print("%s rd1-baseline-split (daily-baseline=%s main=%s)"
              % ("PASS" if ok else "FAIL",
                 os.path.exists(dbase), os.path.exists(mbase)))
        if not ok:
            problems.append("rd1-split")
        # AC-RD3: drift negative path flags on the daily face
        # (lobby base 5.0s -> 8.0s vs slack 2.5s = past threshold)
        drifted = write_log(tmp, "reconcile-daily-20260998.log",
                            [("lobby", 8.0), ("pay", 9.5)], 17.5)
        os.utime(drifted, (3000000, 3000000))
        code = RP.main(["runner_profile.py", "--daily", "--log",
                        drifted])
        ok = code == 2
        print("%s rd3-drift-flag-exit2 (exit=%d)"
              % ("PASS" if ok else "FAIL", code))
        if not ok:
            problems.append("rd3-drift")
        # AC-RD3: --check stale detection on the daily face
        code = RP.main(["runner_profile.py", "--daily", "--check"])
        clean_exit = code
        with open(RP.baseline_path(True), "ab") as handle:
            handle.write(b" ")
        code = RP.main(["runner_profile.py", "--daily", "--check"])
        ok = clean_exit == 0 and code == 2
        print("%s rd3-check-stale-detect (clean=%d tampered=%d)"
              % ("PASS" if ok else "FAIL", clean_exit, code))
        if not ok:
            problems.append("rd3-check")
        # AC-RD4: fail-closed refusal when only a RUNNER FAIL daily
        # log exists (discovery skips it, then refuses)
        only_fail = os.path.join(tmp, "fail-only")
        os.makedirs(only_fail)
        RP.QA_DIR = only_fail
        write_log(only_fail, "reconcile-daily-20260997.log",
                  [("lobby", 1.0)], 1.0, runner_fail=True)
        code = RP.main(["runner_profile.py", "--daily"])
        ok = code == 3
        print("%s rd4-runner-fail-refusal-exit3 (exit=%d)"
              % ("PASS" if ok else "FAIL", code))
        if not ok:
            problems.append("rd4-refusal")
        # AC-RD1: main face unchanged - absent baseline keeps the
        # historical ABSENT path, and no main-face file is created
        RP.QA_DIR = tmp
        os.remove(RP.baseline_path(True))
        code = RP.main(["runner_profile.py", "--log", daily])
        ok = (code == 0 and not os.path.exists(RP.baseline_path(False)))
        print("%s rd1-main-face-zero-drift (exit=%d)"
              % ("PASS" if ok else "FAIL", code))
        if not ok:
            problems.append("rd1-main-face")
        # AC-RD5: hygiene - ascii source, no network imports
        hyg = RP.hygiene_report()
        ok = not hyg
        print("%s rd5-hygiene-ascii-no-net (%s)"
              % ("PASS" if ok else "FAIL", hyg or "clean"))
        if not ok:
            problems.append("rd5-hygiene")
    finally:
        RP.QA_DIR = saved_qa
        shutil.rmtree(tmp, ignore_errors=True)
    if problems:
        print("SUITE FAIL (%s)" % ",".join(problems))
        return 1
    print("SUITE PASS 8/8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
