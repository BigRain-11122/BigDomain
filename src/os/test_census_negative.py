"""Writer-census negative-family suite (R2151; criteria
AC-CDN1..AC-CDN8 pre-registered in state/queue/tech.md BEFORE this
code existed - honesty law).

What this proves: the R1841 drift detector really does catch the three
shell-capture dialects (CRLF cp936, CRLF utf-8, UTF-16 BOM) by name,
and a file rebuilt in the healthy tee dialect can return to
DRIFT-CLEAN through the new per-file disposition face (--accept) -
not through a whole-baseline re-freeze that would mask unrelated
drift. Every refusal must leave the baseline byte-identical.

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
EXPECTED_CRITERIA = 12
TEE = b"PASS suite census negative\n"
# cp936 bytes that are NOT valid utf-8 (a pure-ASCII payload would be
# classified pwsh-capture, so the literal carries a Chinese sentinel).
CMD_RAW = u"\u5224\u5b9a".encode("gbk") + b"\r\n"
PWSH = u"\u5224\u5b9a".encode("utf-8") + b"\r\n"
UTF16 = b"\xff\xfe" + "hello utf16le\n".encode("utf-16-le")

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
    world = tempfile.mkdtemp(prefix="census-neg-world-")
    try:
        wp = lambda name: os.path.join(world, name)  # noqa: E731
        bpath = os.path.join(world, BASELINE_NAME)
        write(wp("b-cmdraw.log"), CMD_RAW)
        write(wp("b-pwsh.log"), PWSH)
        write(wp("b-utf16.log"), UTF16)
        write(wp("b-tee.log"), TEE)
        freeze_lines, freeze_code, freeze_base = CENSUS.write_baseline(
            world, bpath)
        if freeze_code != 0:
            check(False, "AC-CDN0 fixture freeze failed: %s"
                  % blob(freeze_lines))
            return

        # AC-CDN2 (pre): a NEW tee evidence product never flags.
        write(wp("new-tee.log"), TEE)
        clines, ccode = CENSUS.check_against_baseline(world, bpath)
        check(ccode == 0 and "[flag]" not in blob(clines)
              and "DRIFT-CLEAN" in blob(clines),
              "AC-CDN2 new tee file is a normal product, zero flag")

        # AC-CDN1: three negative fixture dialects must all be caught by
        # name, with no fourth accidental flag (the new tee file above).
        write(wp("n-cmdraw.log"), CMD_RAW)
        write(wp("n-pwsh.log"), PWSH)
        write(wp("n-utf16.log"), UTF16)
        dlines, dcode = CENSUS.check_against_baseline(world, bpath)
        dblob = blob(dlines)
        check(dcode == 2 and dblob.count("[flag] new-dialect:") == 3
              and "[flag] new-dialect: n-cmdraw.log (class=cmd-raw)"
              in dblob
              and "[flag] new-dialect: n-pwsh.log (class=pwsh-capture)"
              in dblob
              and "[flag] new-dialect: n-utf16.log (class=ps-utf16)"
              in dblob
              and "DRIFT-FLAG" in dblob,
              "AC-CDN1 three negative dialects caught by name, exit 2")

        # AC-CDN2: rebuild each in the healthy tee dialect, accept, and
        # the detector must return to DRIFT-CLEAN.
        accepted = []
        for name in ("n-cmdraw.log", "n-pwsh.log", "n-utf16.log"):
            write(wp(name), TEE)
            alines, acode = CENSUS.accept_reconciled(world, bpath, name)
            accepted.append((name, acode, alines))
        rlines, rcode = CENSUS.check_against_baseline(world, bpath)
        rblob = blob(rlines)
        check(all(a[1] == 0 for a in accepted)
              and rcode == 0 and "DRIFT-CLEAN" in rblob
              and "[flag]" not in rblob,
              "AC-CDN2 rebuilt+accepted returns to DRIFT-CLEAN exit 0")

        # AC-CDN2/6: baseline keeps exactly four sorted keys; rebuilt
        # names are gone from every class and tee files stay unbaselined.
        with io.open(bpath, "r", encoding="utf-8") as handle:
            base = json.load(handle)
        all_names = [n for c in CENSUS.BASELINE_CLASSES for n in base[c]]
        check(set(base.keys()) == set(CENSUS.BASELINE_CLASSES)
              and all(base[c] == sorted(base[c])
                      for c in CENSUS.BASELINE_CLASSES)
              and not any(n.startswith("n-") for n in all_names)
              and "new-tee.log" not in all_names,
              "AC-CDN2 baseline keeps four sorted classes, tee unbaselined")

        # AC-CDN3 (1): a not-baselined file that is still a bad dialect
        # must be refused, and the baseline file must not move.
        before = read_bytes(bpath)
        write(wp("n2-bad.log"), CMD_RAW)
        glines, gcode = CENSUS.accept_reconciled(world, bpath, "n2-bad.log")
        check(gcode == 2 and "refused:" in blob(glines)
              and read_bytes(bpath) == before,
              "AC-CDN3 not-baselined bad dialect refused, baseline intact")

        # AC-CDN3 (2): a baselined file that is still non-tee (not yet
        # rebuilt) must be refused.
        glines2, gcode2 = CENSUS.accept_reconciled(world, bpath, "b-pwsh.log")
        check(gcode2 == 2 and "still" not in blob(glines2)
              and "class=pwsh-capture" in blob(glines2)
              and read_bytes(bpath) == before,
              "AC-CDN3 baselined non-tee file refused, baseline intact")

        # AC-CDN3 (3)+(4): disappeared baselined file and missing
        # baseline file are both refusals.
        os.unlink(wp("b-utf16.log"))
        glines3, gcode3 = CENSUS.accept_reconciled(world, bpath, "b-utf16.log")
        mlines, mcode = CENSUS.accept_reconciled(
            world, os.path.join(world, "no-such-baseline.json"),
            "b-pwsh.log")
        check(gcode3 == 2 and "not on disk" in blob(glines3)
              and mcode == 2 and "probe not deployed" in blob(mlines)
              and read_bytes(bpath) == before,
              "AC-CDN3 disappeared + missing baseline refused")

        # AC-CDN5: rewriting a baselined file to tee WITHOUT accept must
        # still flag - there is no silent auto-heal.
        write(wp("b-cmdraw.log"), TEE)
        klines, kcode = CENSUS.check_against_baseline(world, bpath)
        check(kcode == 2
              and "[flag] class-migrated: b-cmdraw.log (base=cmd-raw "
              "cur=tee)" in blob(klines),
              "AC-CDN5 no silent auto-heal without accept")

        # snapshot untouched classes before the disposition accept
        with io.open(bpath, "r", encoding="utf-8") as handle:
            pre = json.load(handle)

        # AC-CDN7: audit face shapes and reconciled count.
        alines2, acode2 = CENSUS.accept_reconciled(world, bpath,
                                                   "b-cmdraw.log")
        ab = blob(alines2)
        check(acode2 == 0
              and "accepted: b-cmdraw.log (base=cmd-raw cur=tee)" in ab
              and ("baseline: %s" % os.path.abspath(bpath)) in ab
              and "reconciled=0" in ab,
              "AC-CDN7 audit lines carry file, baseline path, count")

        # AC-CDN6: atomic write leaves no temp residue and leaves the
        # untouched classes item-for-item identical.
        with io.open(bpath, "r", encoding="utf-8") as handle:
            post = json.load(handle)
        check(not glob.glob(os.path.join(world, ".wc-baseline-*"))
              and all(pre[c] == post[c] for c in
                      ("pwsh-capture", "ps-utf16", "other"))
              and post["cmd-raw"] == [],
              "AC-CDN6 atomic write, no temp residue, others unchanged")

        # AC-CDN4: second accept is idempotent, reports
        # already-reconciled, and never rewrites the baseline.
        before2 = read_bytes(bpath)
        ilines, icode = CENSUS.accept_reconciled(world, bpath,
                                                 "b-cmdraw.log")
        ilines2, icode2 = CENSUS.accept_reconciled(world, bpath,
                                                   "b-cmdraw.log")
        check(icode == 0 and icode2 == 0
              and "already-reconciled: b-cmdraw.log" in blob(ilines)
              and (ilines, icode) == (ilines2, icode2)
              and read_bytes(bpath) == before2,
              "AC-CDN4 second accept idempotent and deterministic")

        # AC-CDN8: hygiene, wiring label, criteria count, and the R1841
        # selftest must stay green (zero regression).
        with io.open(os.path.abspath(__file__), "r", encoding="ascii",
                     errors="strict") as handle:
            mine = handle.read()
        net = [m for m in CENSUS.NET_IMPORTS if m in mine]
        selftest_code = 0
        sink = io.StringIO()
        try:
            with contextlib.redirect_stdout(sink), \
                    contextlib.redirect_stderr(sink):
                selftest_code, _checks = CENSUS._selftest()
        except SystemExit as exc:
            selftest_code = exc.code
        runner = os.path.join(SRC, "sandbox", "reconcile_all.py")
        with io.open(runner, "r", encoding="utf-8") as handle:
            rsrc = handle.read()
        check(not net and selftest_code == 0
              and "ledger-census-negative" in rsrc
              and EXPECTED_CRITERIA == 12,
              "AC-CDN8 hygiene, selftest green, wiring label, count 12")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("suite: writer-census negative family (R2151 AC-CDN1..8)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())