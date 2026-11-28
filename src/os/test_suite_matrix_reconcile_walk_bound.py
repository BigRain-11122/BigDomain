"""AC-EDW1..AC-EDW4 (pinned in src/os/backlog.md at R3649, before any module
byte moved): the DECLARED walk ceiling must bound what the walk costs, not
only the half of it that decodes.

Measured before the fix (tmp/probe_R3649.py, qa/probe-R3649.log): seventy
unreadable candidates above one PASS leg, ceiling 64, and the walk opened all
seventy and answered PASS with walk={'considered': 71, 'decoded': 1} - no
bound engaged and no word about the files it could not read. A walk that
skipped seventy files printed the same line as a walk that read one of one.

AC-EDW1 the bound counts ATTEMPTS (a starved corrupt pile reads bounded).
AC-EDW2 skipped files are counted, and a clean world keeps the exact R2602
       shape {"considered", "decoded"} so the whole-dict pins still hold.
AC-EDW3 the accepted leg's rank is published only when it cannot be read off
       `decoded`, i.e. when skipped files sat above it.
AC-EDW4 the --check face names the leg it accepted.
"""
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for path in (os.path.join(REPO, "src", "os"), os.path.join(REPO, "src", "sandbox")):
    if path not in sys.path:
        sys.path.insert(0, path)

import suite_matrix_reconcile as SMR  # noqa: E402

PASS_LEG = "RUNNER PASS (2/2 suites green, reconcile controls 7/7, 1.0s)"
BAD_BYTES = b"\xff\xfe\x00not utf-8\x80"
EXPECTED_CRITERIA = 11


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return bool(ok)


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_bad(path):
    with open(path, "wb") as handle:
        handle.write(BAD_BYTES)


def pile(directory, bad, legs, name="qa"):
    """A candidate pile ordered newest-first by mtime: `bad` unreadable files
    above `legs` readable ones (each a PASS leg body), all inside `directory`."""
    root = os.path.join(directory, name)
    os.makedirs(root)
    stamp = 9000
    order = []
    for index in range(bad):
        path = os.path.join(root, "z%02d-bad.log" % index)
        write_bad(path)
        order.append(path)
        stamp -= 1
    for index in range(legs):
        path = os.path.join(root, "a%02d-pass.log" % index)
        write_text(path, PASS_LEG + "\n")
        order.append(path)
        stamp -= 1
    for offset, path in enumerate(order):
        when = 9000 - offset
        os.utime(path, (when, when))
    return root


def main():
    results = []
    work = tempfile.mkdtemp(prefix="edw-")
    try:
        # AC-EDW1: the ceiling counts attempts. Seventy unreadable candidates
        # above one PASS leg at ceiling 64 must starve, not walk past the
        # bound and answer.
        starved_root = pile(os.path.join(work, "one"), 70, 1)
        path, run, walk = SMR.newest_pass_leg_scanned(starved_root, ceiling=64)
        results.append(check(
            path is None and run is None
            and walk.get("bounded") is True and walk.get("ceiling") == 64
            and walk.get("decoded") == 0 and walk.get("unreadable") == 64
            and walk.get("considered") == 71,
            "AC-EDW1 corrupt pile starves at the declared ceiling: %s" % walk))

        # AC-EDW1 negative control: the same pile with a ceiling wide enough
        # to reach the leg does answer, so the None above is the bound and not
        # an empty pile.
        reach_path, reach_run, reach_walk = SMR.newest_pass_leg_scanned(
            starved_root, ceiling=80)
        results.append(check(
            reach_path is not None and (reach_run or {}).get("verdict") == "PASS"
            and os.path.basename(reach_path) == "a00-pass.log"
            and reach_walk.get("decoded") == 1
            and reach_walk.get("unreadable") == 70,
            "AC-EDW1 the leg is reachable above the old bound: %s"
            % reach_walk))

        # AC-EDW1 (spend evidence): with the bound counting attempts the
        # walk may not read more than `ceiling` candidates at all. Counted by
        # wrapping the shipped parse_evidence, not by trusting the block.
        fresh_root = pile(os.path.join(work, "two"), 90, 1)
        calls = {"n": 0}
        real = SMR.SM.parse_evidence

        def counting(candidate):
            calls["n"] += 1
            return real(candidate)

        SMR.SM.parse_evidence = counting
        try:
            SMR.newest_pass_leg_scanned(fresh_root, ceiling=10)
        finally:
            SMR.SM.parse_evidence = real
        results.append(check(
            calls["n"] == 10,
            "AC-EDW1 the walk reads exactly ceiling=10 candidates, not more"
            " (read %d)" % calls["n"]))

        # AC-EDW2: a clean pile keeps the exact R2602 shape, so the whole-dict
        # pins that compare by equality stay honest.
        clean_root = pile(os.path.join(work, "three"), 0, 3)
        os.utime(os.path.join(clean_root, "a01-pass.log"), (1, 1))
        os.utime(os.path.join(clean_root, "a02-pass.log"), (1, 1))
        clean_path, clean_run, clean_walk = SMR.newest_pass_leg_scanned(
            clean_root)
        results.append(check(
            clean_path is not None
            and clean_walk == {"considered": 3, "decoded": 1},
            "AC-EDW2 clean pile publishes considered/decoded only: %s"
            % clean_walk))

        # AC-EDW2: skipped files are counted, never silently dropped.
        mixed_root = pile(os.path.join(work, "four"), 2, 1)
        mixed_path, mixed_run, mixed_walk = SMR.newest_pass_leg_scanned(
            mixed_root)
        results.append(check(
            mixed_path is not None and mixed_walk.get("unreadable") == 2
            and mixed_walk.get("decoded") == 1
            and mixed_walk.get("considered") == 3,
            "AC-EDW2 two skipped files are named: %s" % mixed_walk))

        # AC-EDW3: the rank rides along only when skipped files sat above the
        # accepted leg, because only then can `decoded` not imply it.
        results.append(check(
            mixed_walk.get("leg_rank") == 3,
            "AC-EDW3 rank published when skipped files sat above: %s"
            % mixed_walk))

        results.append(check(
            "leg_rank" not in clean_walk,
            "AC-EDW3 rank omitted when decoded already implies it: %s"
            % clean_walk))

        # AC-EDW3 negative control: the starved block publishes no rank at
        # all - it never accepted a leg to rank.
        results.append(check(
            "leg_rank" not in walk,
            "AC-EDW3 no rank on a starved walk: %s" % walk))

        # AC-EDW4: the check face names the leg it accepted, and the name is
        # the one the report derived at CALL time rather than a pinned string.
        live = SMR.report()
        buffer = io.StringIO()
        stdout = sys.stdout
        sys.stdout = buffer
        try:
            code = SMR.main(["suite_matrix_reconcile.py", "--check"])
        finally:
            sys.stdout = stdout
        printed = buffer.getvalue()
        results.append(check(
            code == 0 and live.get("verdict") == SMR.WORD_CURRENT
            and ("  evidence=%s" % live["evidence"]) in printed,
            "AC-EDW4 DOC-CURRENT names the leg it accepted: %s"
            % live.get("evidence")))

        # AC-EDW4: the --json face carries the same leg, so a machine reader
        # and a human reader no longer disagree about which leg answered.
        buffer = io.StringIO()
        sys.stdout = buffer
        try:
            jcode = SMR.main(["suite_matrix_reconcile.py", "--check", "--json"])
        finally:
            sys.stdout = stdout
        payload = json.loads(buffer.getvalue())
        results.append(check(
            jcode == 0 and payload.get("evidence") == live.get("evidence")
            and payload.get("evidence_source") == "walk-leg",
            "AC-EDW4 json face carries the same leg: %s/%s"
            % (payload.get("evidence"), payload.get("evidence_source"))))

        # AC-EDW4: the published walk block still names the cost in the same
        # words the operator reads, with the new fields only when they carry
        # news.
        results.append(check(
            "evidence-walk considered=%d decoded=%d"
            % (live["walk"]["considered"], live["walk"]["decoded"]) in printed
            and set(live["walk"]) <= {"considered", "decoded", "unreadable",
                                      "leg_rank", "ceiling", "bounded"},
            "AC-EDW4 live walk prints its cost: %s" % live.get("walk")))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    total = len(results)
    print("SUITE %s %d/%d" % ("PASS" if all(results) and
                              total == EXPECTED_CRITERIA else "FAIL",
                              sum(results), EXPECTED_CRITERIA))
    return 0 if all(results) and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())
