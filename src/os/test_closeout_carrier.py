"""closeout carrier suite (R3177; criteria AC-WLG1..AC-WLG6 were pinned in
src/os/backlog.md as the R3177 PIN row BEFORE the code existed).

What this proves: the closeout gate now reads the state carrier's waterline
and canonical layout through the shipped `logs_toolkit` readers (no second
definition of either number); a non-canonical layout and an over-line carrier
with no window to fold both refuse BY NAME; an over-line carrier that is
canonical and foldable stays green and publishes its debt on a CARRIER row
below the verdict, so the pinned PASS token shape never moves; and a root it
cannot read refuses instead of reading clean.

Stdlib only, ASCII source, zero network, read-only on the live tree.
Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, BASE)
sys.path.insert(0, TOOLS)

import logs_toolkit as LT  # noqa: E402
import closeout_gate as CG  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(TOOLS, "closeout_gate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-closeout-carrier"
WIRED_EXPECT = '"test_closeout_carrier.py"), 6),'

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


def write_bytes(path, raw):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "wb") as handle:
        handle.write(raw)


def canonical_state(items, eol="\r\n"):
    """A state.json in the R2246 canonical layout (CRLF, 16-space items)."""
    body = ["{", '  "log": [']
    rows = [' ' * 16 + json.dumps(text, ensure_ascii=False) for text in items]
    body.append(("," + eol).join(rows) if rows else "")
    body.extend(["  ],", '  "tick": 1', "}"])
    return eol.join(body).encode("utf-8")


def make_root(items, eol="\r\n"):
    root = tempfile.mkdtemp(prefix="bigdomain-wlg-w-")
    write_bytes(os.path.join(root, "src", "os", "state.json"),
                canonical_state(items, eol))
    return root


def digest_tree(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            with io.open(path, "rb") as handle:
                out[rel] = hashlib.sha256(handle.read()).hexdigest()
    return out


def big_item(size):
    return "x" * size


def ac_wlg1():
    """The carrier face writes nothing."""
    root = make_root(["alpha", "beta"])
    try:
        before = digest_tree(root)
        CG.check_carrier(root)
        CG.check_carrier(root)
        after = digest_tree(root)
        ok = before == after
        if not ok:
            print("  measured: before=%r after=%r" % (before, after), flush=True)
        check(ok, "AC-WLG1 the carrier face is read-only: every digest in the "
                  "fixture world is unchanged after two readings")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_wlg2():
    """A non-canonical layout refuses by name."""
    lf_root = make_root(["alpha", "beta"], eol="\n")
    indent_root = make_root(["alpha", "beta"])
    path = os.path.join(indent_root, "src", "os", "state.json")
    raw = io.open(path, "rb").read()
    write_bytes(path, raw.replace(b" " * 16, b"    ", 1))
    try:
        lf_ok, lf_line = CG.check_carrier(lf_root)
        in_ok, in_line = CG.check_carrier(indent_root)
        ok = (not lf_ok and "E_CLG_CARRIER_LAYOUT" in lf_line
              and not in_ok and "E_CLG_CARRIER_LAYOUT" in in_line)
        if not ok:
            print("  measured: lf=%r indent=%r"
                  % ((lf_ok, lf_line), (in_ok, in_line)), flush=True)
        check(ok, "AC-WLG2 a bare-LF log and a drifted indent both refuse as "
                  "E_CLG_CARRIER_LAYOUT instead of passing")
    finally:
        shutil.rmtree(lf_root, ignore_errors=True)
        shutil.rmtree(indent_root, ignore_errors=True)


def ac_wlg3():
    """Over the line with no window to fold refuses by name."""
    root = make_root([big_item(LT.GATE + 2000)])
    try:
        width = os.path.getsize(os.path.join(root, "src", "os", "state.json"))
        ok, line = CG.check_carrier(root)
        good = (width > LT.GATE and not ok and "E_CLG_CARRIER_FOLD" in line
                and "fold_needed=true" in line and "log_items=1" in line)
        if not good:
            print("  measured: width=%d ok=%r line=%s"
                  % (width, ok, line), flush=True)
        check(good, "AC-WLG3 an over-line carrier carrying one log item has no "
                    "fold window and refuses as E_CLG_CARRIER_FOLD")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_wlg4():
    """Over the line but canonical and foldable: green, debt visible."""
    root = make_root([big_item(LT.GATE + 2000), "beta", "gamma"])
    try:
        width = os.path.getsize(os.path.join(root, "src", "os", "state.json"))
        ok, line = CG.check_carrier(root)
        good = (width > LT.GATE and ok and line.startswith("CARRIER bytes=")
                and "fold_needed=true" in line and "layout_ok=true" in line
                and "margin=-" in line and "log_items=3" in line)
        if not good:
            print("  measured: width=%d ok=%r line=%s"
                  % (width, ok, line), flush=True)
        check(good, "AC-WLG4 an over-line carrier that is canonical and "
                    "foldable stays green and publishes its debt as "
                    "fold_needed=true on the CARRIER row")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_wlg5():
    """A root it cannot read refuses instead of reading clean."""
    empty = tempfile.mkdtemp(prefix="bigdomain-wlg-e-")
    broken = make_root(["alpha"])
    path = os.path.join(broken, "src", "os", "state.json")
    write_bytes(path, b"{ not json\r\n")
    try:
        miss_ok, miss_line = CG.check_carrier(empty)
        bad_ok, bad_line = CG.check_carrier(broken)
        ok = (not miss_ok and CG.E_CLG_NO_STATE in miss_line
              and not bad_ok and "E_CLG_CARRIER_UNREADABLE" in bad_line)
        if not ok:
            print("  measured: miss=%r bad=%r"
                  % ((miss_ok, miss_line), (bad_ok, bad_line)), flush=True)
        check(ok, "AC-WLG5 a root with no state.json and a root with "
                  "unparsable bytes both refuse by name, never green")
    finally:
        shutil.rmtree(empty, ignore_errors=True)
        shutil.rmtree(broken, ignore_errors=True)


def ac_wlg6():
    """Wired: the live closeout publishes the carrier, the plain face never."""
    target = os.path.join(REPO, "qa")
    baseline = os.path.join(target, CG.CENSUS.BASELINE_NAME)
    name = os.path.basename(baseline) if os.path.isfile(baseline) else None
    plain_lines, plain_rc, plain_v = CG.evaluate(target, baseline)
    deep_lines, deep_rc, deep_v = CG.evaluate(target, baseline, root=REPO)
    rows = [line for line in deep_lines if line.startswith("CARRIER ")]
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        source = raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        source = raw.decode("utf-8", "replace")
        ascii_ok = False
    imports = [ln for ln in source.splitlines()
               if ln.startswith("import ") or ln.startswith("from ")]
    net_ok = not any(("socket" in ln or "urllib" in ln or "http" in ln)
                     for ln in imports)
    with io.open(RUNNER, "r", encoding="utf-8-sig", errors="replace") as fh:
        runner = fh.read()
    wired = WIRED_EXPECT in runner
    files = plain_v.get("files")
    ok = (name is not None
          and plain_rc == 0
          and plain_lines[0] == ("CLOSEOUT-GATE PASS files=%d flags=0 "
                                 "reader_refused=0 gating=flags" % files)
          and "carrier" not in plain_v
          and deep_rc == 0
          and deep_lines[0] == ("CLOSEOUT-GATE PASS files=%d flags=0 "
                                "reader_refused=0 gating=flags round_main=OK "
                                "census=PASS matrix=DOC-CURRENT" % files)
          and deep_v.get("carrier") == "OK"
          and len(rows) == 1
          and "fold_needed=" in rows[0]
          and "layout_ok=" in rows[0]
          and ascii_ok and net_ok and wired
          and EXPECTED_CRITERIA == 6)
    if not ok:
        print("  measured: plain=%r deep=%r rows=%r ascii=%r net=%r wired=%r"
              % (plain_lines[:1], deep_lines[:2], rows, ascii_ok, net_ok, wired),
              flush=True)
    check(ok, "AC-WLG6 the live closeout publishes one CARRIER row and asks "
              "carrier=OK while the root=None face stays byte-identical; the "
              "module is ASCII with no network import and the registry row "
              "carries this suite with its six criteria")


def main():
    ac_wlg1()
    ac_wlg2()
    ac_wlg3()
    ac_wlg4()
    ac_wlg5()
    ac_wlg6()
    print("SUITE %s %d/%d"
          % ("PASS" if FAILS == 0 else "FAIL", PASSES, PASSES + FAILS),
          flush=True)
    if PASSES + FAILS != EXPECTED_CRITERIA or FAILS:
        print("EXPECTED %d criteria" % EXPECTED_CRITERIA, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
