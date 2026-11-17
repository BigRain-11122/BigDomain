"""tree_snapshot suite (R2875).

Criteria AC-TSNAP1..AC-TSNAP6 were pinned in src/os/backlog.md at R2875 BEFORE
the module existed.

What this proves: docs/status-export.json's latest_artifact follows the NEWEST
preview pair by mtime, so a fixture that re-renders a tracked pair moves the
world another suite measures. Measured at R2875 in the real tree: setting one
tracked pair's mtime forward flips `export_round.py --check` to
"VERDICT FAIL 1 / AC-EXPW1", and restoring it flips it back. tree_snapshot
exists so that class of side effect is one context manager away from gone.

AC-TSNAP3 is the load-bearing one: the coupling is EXECUTED here in a private
world, not described, so the law's justification is a passing assertion.

Stdlib only, ASCII source, zero network, no wall clock. Exit 0 = all green.
"""

import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
sys.path.insert(0, BASE)

import export_round as ER  # noqa: E402
import tree_snapshot as TS  # noqa: E402

MODULE = os.path.join(BASE, "tree_snapshot.py")
LABEL = "os-tree-snapshot"
WIRED_EXPECT = '"test_tree_snapshot.py"), 6),'
EXPECTED_CRITERIA = 6

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


def write_bytes(path, data):
    with open(path, "wb") as handle:
        handle.write(data)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def sig(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns, st.st_atime_ns)


def ac_tsnap1_round_trip():
    """AC-TSNAP1 bytes AND mtime_ns come back exactly."""
    d = tempfile.mkdtemp(prefix="tsnap1-")
    try:
        path = os.path.join(d, "pair.html")
        write_bytes(path, b"original\n")
        os.utime(path, ns=(111000000000, 222000000000))
        before = sig(path)
        with TS.restored([path]) as snap:
            write_bytes(path, b"re-rendered\n")
            os.utime(path, ns=(333000000000, 444000000000))
            mid = read_bytes(path)
        after = sig(path)
        check(mid == b"re-rendered\n"
              and read_bytes(path) == b"original\n"
              and after == before and snap.changed == [path],
              "AC-TSNAP1 body changed bytes+mtime, exit restored both exactly")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def ac_tsnap2_exception_path():
    """AC-TSNAP2 the exception path restores and re-raises the body's own error."""
    d = tempfile.mkdtemp(prefix="tsnap2-")
    try:
        path = os.path.join(d, "pair.json")
        write_bytes(path, b"{}\n")
        os.utime(path, ns=(555000000000, 666000000000))
        before = sig(path)
        raised = None
        try:
            with TS.restored([path]) as snap:  # noqa: F841
                write_bytes(path, b'{"changed": 1}\n')
                os.utime(path, ns=(777000000000, 888000000000))
                raise RuntimeError("body failed")
        except RuntimeError as exc:
            raised = str(exc)
        # the signature is captured BEFORE the read below: on this platform a
        # read moves atime, and the law under test is what the guard left behind.
        after = sig(path)
        payload = read_bytes(path)
        check(raised == "body failed"
              and payload == b"{}\n" and after == before,
              "AC-TSNAP2 restore ran on the exception path and the body error "
              "re-raised unchanged")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def build_world():
    """A private world with two preview pairs and a face naming the newest."""
    d = tempfile.mkdtemp(prefix="tsnap3-")
    os.makedirs(os.path.join(d, "preview"))
    os.makedirs(os.path.join(d, "src", "os"))
    os.makedirs(os.path.join(d, "docs"))
    alpha_html = os.path.join(d, "preview", "alpha.html")
    alpha_json = os.path.join(d, "preview", "alpha.json")
    beta_html = os.path.join(d, "preview", "beta.html")
    beta_json = os.path.join(d, "preview", "beta.json")
    write_bytes(alpha_html, b"<html>alpha face</html>\n")
    write_bytes(alpha_json, b"{}\n")
    write_bytes(beta_html, b"<html>beta face, the newer one</html>\n")
    write_bytes(beta_json, b'{"b": 1}\n')
    os.utime(alpha_html, ns=(1000000000000, 1000000000000))
    os.utime(alpha_json, ns=(1000000000000, 1000000000000))
    os.utime(beta_html, ns=(2000000000000, 2000000000000))
    os.utime(beta_json, ns=(2000000000000, 2000000000000))
    state = {"tick": 9100,
             "log": ["2026-11-17 R9100 PRODUCT: a fixture round body",
                     "R9100 tokens: local=1k api=0 api_reason=fixture"]}
    write_bytes(os.path.join(d, "src", "os", "state.json"),
                json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8"))
    pair = (os.path.getsize(beta_html), os.path.getsize(beta_json))
    derived = ER.derive(d, state, "TS")
    face = {"ceo_face": {
        "current": "R9100 a fixture round",
        # R2897: the pair line is asked of the shipped derivation instead of
        # being hand-assembled. The hand-built tuple was already one field short
        # of the row `fmt_pair` reads, and the R2895 evidence fields were never
        # added at all, so this fixture graded an OLDER face than the shipped one
        # and only stayed silent because it never ran in a slice; a fixture must
        # satisfy the law it is graded under.
        "latest_artifact": derived["latest"],
        "next_milestone": "next fixture milestone",
        "next_milestone_due": "2026-11-18",
        "latest_evidence": derived["evidence"],
        "latest_artifact_note": derived["note"]}}
    write_bytes(os.path.join(d, "docs", "status-export.json"),
                json.dumps(face, ensure_ascii=False, indent=2).encode("utf-8"))
    return d, alpha_html, alpha_json


def ac_tsnap3_coupling_executed():
    """AC-TSNAP3 without the helper the face reddens; with it the world is intact."""
    world, alpha_html, alpha_json = build_world()
    try:
        clean = ER.check(world)
        check(clean == [], "AC-TSNAP3 baseline world reads no verdict failure")
        # (i) the same touch WITHOUT the helper: the face reddens.
        os.utime(alpha_html, ns=(3000000000000, 3000000000000))
        os.utime(alpha_json, ns=(3000000000000, 3000000000000))
        red = ER.check(world)
        check(any(text.startswith("AC-EXPW1 latest_artifact is not the newest")
                  for text in red),
              "AC-TSNAP3 an unguarded touch moves latest_artifact (AC-EXPW1 red)")
        # put the world back so the guarded half starts from the same bytes.
        os.utime(alpha_html, ns=(1000000000000, 1000000000000))
        os.utime(alpha_json, ns=(1000000000000, 1000000000000))
        with TS.restored([alpha_html, alpha_json]):
            os.utime(alpha_html, ns=(4000000000000, 4000000000000))
            os.utime(alpha_json, ns=(4000000000000, 4000000000000))
            inside = ER.check(world)
        after = ER.check(world)
        check(any(text.startswith("AC-EXPW1") for text in inside)
              and after == [],
              "AC-TSNAP3 the same touch inside the helper is undone on exit "
              "(green again)")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_tsnap4_absent_not_created():
    """AC-TSNAP4 a path absent at snapshot time is never created by restore."""
    d = tempfile.mkdtemp(prefix="tsnap4-")
    try:
        there = os.path.join(d, "there.txt")
        gone = os.path.join(d, "gone.txt")
        write_bytes(there, b"kept\n")
        os.utime(there, ns=(900000000000, 900000000000))
        before = sorted(os.listdir(d))
        with TS.restored([there, gone]) as snap:
            write_bytes(there, b"moved\n")
            write_bytes(gone, b"smuggled\n")
        check(not os.path.exists(gone)
              and sorted(os.listdir(d)) == before
              and read_bytes(there) == b"kept\n"
              and snap.absent == [gone] and snap.removed == [gone],
              "AC-TSNAP4 absent path recorded, deleted by restore, listing intact")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def ac_tsnap5_no_clock_no_side_effect():
    """AC-TSNAP5 no clock, no network; entering the guard changes nothing."""
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        src = handle.read()
    imports = set()
    for line in src.splitlines():
        text = line.strip()
        if text.startswith("import "):
            imports.add(text.split()[1].split(".")[0])
        elif text.startswith("from ") and " import " in text:
            imports.add(text.split()[1].split(".")[0])
    banned = {"time", "datetime", "socket", "urllib", "requests", "random"}
    d = tempfile.mkdtemp(prefix="tsnap5-")
    try:
        path = os.path.join(d, "steady.txt")
        write_bytes(path, b"steady\n")
        os.utime(path, ns=(1200000000000, 1200000000000))
        # read FIRST, then snapshot the signature: the law is "restore the state
        # the guard found at entry", and a read moves atime on this platform.
        before_data = read_bytes(path)
        before_sig = sig(path)
        snap = TS.restored([path])
        with snap:
            pass
        after_sig = sig(path)
        after_data = read_bytes(path)
        check(not (imports & banned)
              and (after_data, after_sig) == (before_data, before_sig)
              and snap.changed == [],
              "AC-TSNAP5 no clock/network import; an untouched guard is a no-op")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def ac_tsnap6_hygiene():
    """AC-TSNAP6 ASCII, stdlib only, exactly one registry row with six criteria."""
    raw = read_bytes(MODULE)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    stdlib = {"io", "os", "sys", "tempfile"}
    imports = set()
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        for line in handle.read().splitlines():
            text = line.strip()
            if text.startswith("import "):
                imports.add(text.split()[1].split(".")[0])
            elif text.startswith("from ") and " import " in text:
                imports.add(text.split()[1].split(".")[0])
    check(all(byte < 128 for byte in raw) and imports <= stdlib,
          "AC-TSNAP6 module source is pure ASCII and stdlib only")
    check(runner.count('"%s"' % LABEL) == 1
          and runner.count(WIRED_EXPECT) == 1
          and EXPECTED_CRITERIA == 6,
          "AC-TSNAP6 exactly one registry row wires this suite with 6 criteria")


def main():
    ac_tsnap1_round_trip()
    ac_tsnap2_exception_path()
    ac_tsnap3_coupling_executed()
    ac_tsnap4_absent_not_created()
    ac_tsnap5_no_clock_no_side_effect()
    ac_tsnap6_hygiene()
    ok_run = FAILS == 0 and PASSES >= EXPECTED_CRITERIA
    law_verdict = "SUITE PASS" if ok_run else "SUITE FAIL"
    print("%s %d/%d" % (law_verdict,
                        EXPECTED_CRITERIA if ok_run else 0,
                        EXPECTED_CRITERIA), flush=True)
    print("SUMMARY pass=%d fail=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
