"""Writer-census additive disposition suite (R2712).

Criteria AC-WCB7-1..AC-WCB7-6 were pinned in this header BEFORE the
face was written (honesty law): the shipped disposition face is
one-directional, so a genuine one-off evidence file in a non-tee
dialect flags new-dialect forever, and its only exit was
--update-baseline, a whole-baseline re-freeze that would also mask
unrelated drift. This suite proves the narrow additive face adds
exactly ONE named file and keeps the gate's teeth for every other.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import glob
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import qa_writer_census as CENSUS  # noqa: E402

BASELINE_NAME = CENSUS.BASELINE_NAME
EXPECTED_CRITERIA = 6
TEE = b"PASS suite census baseline add\n"
# cp936 bytes that are NOT valid utf-8 (a pure-ASCII payload would be
# classified pwsh-capture, so the literal carries a Chinese sentinel).
CMD_RAW = u"\u5224\u5b9a".encode("gbk") + b"\r\n"
PWSH = u"\u5224\u5b9a".encode("utf-8") + b"\r\n"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def write(path, payload):
    with open(path, "wb") as handle:
        handle.write(payload)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def blob(lines):
    return "\n".join(lines)


def run():
    world = tempfile.mkdtemp(prefix="census-add-world-")
    try:
        wp = lambda name: os.path.join(world, name)  # noqa: E731
        bpath = os.path.join(world, BASELINE_NAME)
        write(wp("base-cmdraw.log"), CMD_RAW)
        write(wp("base-tee.log"), TEE)
        freeze_lines, freeze_code, _base = CENSUS.write_baseline(
            world, bpath)
        if freeze_code != 0:
            check(False, "AC-WCB7-0 fixture freeze failed: %s"
                  % blob(freeze_lines))
            return

        # AC-WCB7-1: a genuine one-off evidence file in a non-tee
        # dialect flags, and ONE named add returns the detector to
        # DRIFT-CLEAN without touching any other class.
        write(wp("one-off.log"), PWSH)
        before_lines, before_code = CENSUS.check_against_baseline(
            world, bpath)
        with io.open(bpath, "r", encoding="utf-8") as handle:
            pre = json.load(handle)
        add_lines, add_code = CENSUS.baseline_add(world, bpath,
                                                 "one-off.log")
        after_lines, after_code = CENSUS.check_against_baseline(
            world, bpath)
        with io.open(bpath, "r", encoding="utf-8") as handle:
            post = json.load(handle)
        check(before_code == 2
              and "[flag] new-dialect: one-off.log (class=pwsh-capture)"
              in blob(before_lines)
              and add_code == 0
              and "added: one-off.log (class=pwsh-capture)"
              in blob(add_lines)
              and "post-check exit=0" in blob(add_lines)
              and after_code == 0
              and "DRIFT-CLEAN" in blob(after_lines)
              and "[flag]" not in blob(after_lines)
              and post["pwsh-capture"] == ["one-off.log"]
              and post["cmd-raw"] == pre["cmd-raw"]
              and set(post.keys()) == set(CENSUS.BASELINE_CLASSES)
              and all(post[c] == sorted(post[c])
                      for c in CENSUS.BASELINE_CLASSES),
              "AC-WCB7-1 one named add returns DRIFT-CLEAN, others "
              "untouched")

        # AC-WCB7-2: a second add of the same name is a no-write no-op.
        before2 = read_bytes(bpath)
        again_lines, again_code = CENSUS.baseline_add(world, bpath,
                                                     "one-off.log")
        check(again_code == 0
              and "already-baselined: one-off.log (class=pwsh-capture)"
              in blob(again_lines)
              and read_bytes(bpath) == before2,
              "AC-WCB7-2 second add idempotent, baseline byte-equal")

        # AC-WCB7-3: the healthy dialect is never baselined.
        write(wp("healthy.log"), TEE)
        tee_lines, tee_code = CENSUS.baseline_add(world, bpath,
                                                 "healthy.log")
        check(tee_code == 2
              and "refused: healthy.log is class=tee" in blob(tee_lines)
              and read_bytes(bpath) == before2,
              "AC-WCB7-3 tee file refused, baseline byte-equal")

        # AC-WCB7-4: a name that is not on disk, and a name that could
        # escape the target dir, are both refused with no write.
        miss_lines, miss_code = CENSUS.baseline_add(world, bpath,
                                                   "ghost.log")
        esc_lines, esc_code = CENSUS.baseline_add(world, bpath,
                                                 "../escape.log")
        sub_lines, sub_code = CENSUS.baseline_add(world, bpath,
                                                 os.path.join("sub",
                                                              "x.log"))
        check(miss_code == 2 and "not on disk" in blob(miss_lines)
              and esc_code == 2 and "bare file name" in blob(esc_lines)
              and sub_code == 2 and "bare file name" in blob(sub_lines)
              and read_bytes(bpath) == before2,
              "AC-WCB7-4 missing and escaping names refused, no write")

        # AC-WCB7-5: unrelated drift is NOT masked - with TWO new
        # non-tee files present, adding one leaves the other flagged,
        # and the add face reports that honestly (exit 2) instead of
        # claiming a green it does not have.
        write(wp("second-drift.log"), CMD_RAW)
        write(wp("third-drift.log"), PWSH)
        partial_lines, partial_code = CENSUS.baseline_add(
            world, bpath, "second-drift.log")
        partial_blob = blob(partial_lines)
        with io.open(bpath, "r", encoding="utf-8") as handle:
            distilled = json.load(handle)
        check(partial_code == 2
              and "added: second-drift.log (class=cmd-raw)"
              in partial_blob
              and "post-check exit=2" in partial_blob
              and "[flag] new-dialect: third-drift.log "
              "(class=pwsh-capture)" in partial_blob
              and distilled["cmd-raw"] == ["base-cmdraw.log",
                                           "second-drift.log"]
              and distilled["pwsh-capture"] == ["one-off.log"],
              "AC-WCB7-5 post-check reports remaining drift, no false "
              "green")
        write(wp("second-drift.log"), TEE)  # keep later steps quiet
        write(wp("third-drift.log"), TEE)

        # AC-WCB7-6: hygiene, argument guard and the shipped faces.
        with io.open(os.path.abspath(__file__), "r", encoding="ascii",
                     errors="strict") as handle:
            mine = handle.read()
        net = [m for m in CENSUS.NET_IMPORTS if m in mine]
        guard = 0
        sink = io.StringIO()
        try:
            with contextlib.redirect_stdout(sink), \
                    contextlib.redirect_stderr(sink):
                CENSUS.main(["--dir", world, "--baseline", bpath,
                             "--baseline-add", "one-off.log",
                             "--check"])
        except SystemExit as exc:
            guard = exc.code
        write(wp("rebuilt.log"), TEE)
        rebuilt_pre, rebuilt_code = CENSUS.baseline_add(
            world, os.path.join(world, "no-such.json"), "rebuilt.log")
        accept_lines, accept_code = CENSUS.accept_reconciled(
            world, bpath, "base-cmdraw.log")
        write(wp("base-cmdraw.log"), TEE)
        accept_lines2, accept_code2 = CENSUS.accept_reconciled(
            world, bpath, "base-cmdraw.log")
        check(not net and guard == 2
              and rebuilt_code == 2
              and "probe not deployed" in blob(rebuilt_pre)
              and accept_code == 2
              and accept_code2 == 0
              and "accepted: base-cmdraw.log (base=cmd-raw cur=tee)"
              in blob(accept_lines2)
              and not glob.glob(os.path.join(world, ".wc-baseline-*"))
              and EXPECTED_CRITERIA == 6,
              "AC-WCB7-6 hygiene, guard pair, accept face intact, "
              "no temp residue")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("suite: writer-census additive disposition (R2712 "
          "AC-WCB7-1..6)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())
