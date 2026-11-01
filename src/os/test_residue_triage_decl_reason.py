"""residue_triage_decl_reason suite (R2350; criteria AC-RTD1..AC-RTD6 were
pre-registered inside the R2335 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the triage declaration HEAD claim ("declared_by R2331 ...
until R2350") is finally measured against the entries it claims to speak for.
The declaration and the status vocabulary are imported from residue_triage
(patching either moves the reading, and this module carries no second
declaration reader), an entry whose declared_by is LATER than the head's reads
HEAD-STALE naming both rounds and the entry with the FIRST break in entry
order, an entry whose until differs from the head's window reads HEAD-STALE
naming both windows, a head that matches every entry reads HEAD-CURRENT with
zero breaks while a missing declaration reads UNPINNED rather than a
fabricated pass, the CLI codes are pinned with a byte-stable --json, and the
module is pure ASCII, stdlib only, reads no clock, writes nothing and touches
no network.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import residue_triage_decl_reason as DR  # noqa: E402
import residue_triage as RT  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_decl_reason.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-decl-reason"

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


def entry(round_no, status="DELIVERED", declared_by="R2331", until=2350,
          reason="reviewed at R2331 at its live status"):
    return {
        "round": round_no,
        "status": status,
        "declared_by": declared_by,
        "reason": reason,
        "until": until,
    }


def make_world(entries=None, head="R2331", reason="renewed at R2331",
               raw=None):
    """A throwaway root holding one declaration file."""
    root = tempfile.mkdtemp(prefix="rtd-world-")
    os.makedirs(os.path.join(root, "state"))
    path = os.path.join(root, "state", "residue_triage.json")
    if raw is not None:
        with open(path, "wb") as handle:
            handle.write(raw.encode("utf-8"))
        return root
    if entries is None:
        return root
    document = {"declared_by": head, "reason": reason, "entries": entries}
    with open(path, "wb") as handle:
        handle.write(json.dumps(document, ensure_ascii=True,
                                sort_keys=False).encode("utf-8"))
    return root


def file_map(root):
    """Relative path -> bytes, so 'writes nothing' is measurable."""
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for name in sorted(names):
            path = os.path.join(folder, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = \
                open(path, "rb").read()
    return out


def run_cli(args, world=None):
    argv = [sys.executable, MODULE] + list(args)
    if world is not None:
        argv += ["--root", world]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def refuse(callable_, *args, **kwargs):
    """Run a refusing call and hand back its code, or None if it did not."""
    try:
        callable_(*args, **kwargs)
    except DR.DeclReasonError as exc:
        return exc.code
    except Exception as exc:  # noqa: BLE001 - a wrong error is not a refusal
        return "WRONG:" + type(exc).__name__
    return None


def ac_rtd1():
    """The declaration and the status vocabulary are imported, not re-derived."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    code = code_only(source)
    no_second_reader = ("import residue_triage" in code
                        and "json.loads" not in code
                        and "residue_triage.json" not in code
                        and "def load_declaration" not in code
                        and DR.DECLARATION_PATH == RT.DECLARATION_PATH)
    # a patched loader flows straight through this reading
    world = make_world([entry(2300)])
    synthetic = {"declared_by": 2400,
                 "reason": "synthetic head",
                 "entries": [
                     {"round": 2300, "status": "DELIVERED",
                      "declared_by": 2410, "reason": "later append",
                      "until": 2400},
                 ]}
    saved_loader = RT.load_declaration
    RT.load_declaration = lambda root: synthetic
    try:
        patched = DR.read(world)
    finally:
        RT.load_declaration = saved_loader
    # a patched status tuple refuses an entry it no longer knows
    saved_statuses = RT.SR.STATUSES
    RT.SR.STATUSES = ("STAMP-ONLY-OPEN", "NO-HIT")
    try:
        moved_tuple = refuse(DR.load, world)
    finally:
        RT.SR.STATUSES = saved_statuses
    live = DR.read(make_world([entry(2300)]))
    check(no_second_reader
          and patched["declared_by"] == "R2400"
          and patched["verdict"] == "HEAD-STALE"
          and patched["first_break"] == "R2300"
          and moved_tuple in ("E_RTD_BAD_STATUS", "E_RTR_BAD_STATUS")
          and live["verdict"] == "HEAD-CURRENT",
          "AC-RTD1 imports")


def ac_rtd2():
    """An entry declared_by LATER than the head names both rounds."""
    # The live shape: 195 entries at R2331 with later appends behind them, in
    # entry order so the FIRST break is the earliest append.
    entries = [entry(2300),
               entry(2301),
               entry(2333, declared_by="R2333"),
               entry(2342, declared_by="R2342")]
    report = DR.read(make_world(entries, head="R2331"))
    first = report["breaks"][0] if report["breaks"] else {}
    by_kind = [row for row in report["breaks"]
               if row["kind"] == "DECLARED_BY"]
    check(report["verdict"] == "HEAD-STALE"
          and len(by_kind) == 2
          and first.get("kind") == "DECLARED_BY"
          and first.get("round") == "R2333"
          and first.get("entry_declared_by") == "R2333"
          and first.get("head_declared_by") == "R2331"
          and report["first_break"] == "R2333"
          and by_kind[-1]["round"] == "R2342",
          "AC-RTD2 declared_by later")


def ac_rtd3():
    """An entry whose until differs from the head window names both windows."""
    entries = [entry(2300, until=2350),
               entry(2301, until=2350),
               entry(2302, until=2360, declared_by="R2348")]
    report = DR.read(make_world(entries, head="R2348"))
    row = report["breaks"][0] if report["breaks"] else {}
    check(report["verdict"] == "HEAD-STALE"
          and len(report["breaks"]) == 1
          and row.get("kind") == "UNTIL"
          and row.get("round") == "R2302"
          and row.get("entry_until") == "R2360"
          and row.get("head_until") == "R2350"
          and report["head_until"] == "R2350",
          "AC-RTD3 window mismatch")


def ac_rtd4():
    """A matching head is HEAD-CURRENT; a missing declaration is UNPINNED."""
    matching = DR.read(make_world([entry(2300), entry(2301)], head="R2331"))
    empty = DR.read(make_world(entries=[]))
    missing = DR.read(make_world(entries=None))
    # a matching set whose FIRST break does not exist names the honest dash
    check(matching["verdict"] == "HEAD-CURRENT"
          and matching["breaks"] == []
          and matching["first_break"] == "-"
          and matching["entries"] == 2
          and empty["verdict"] == "HEAD-CURRENT"
          and empty["entries"] == 0
          and missing["verdict"] == "UNPINNED"
          and missing["declared_by"] == "-"
          and missing["entries"] == 0
          and missing["first_break"] == "-",
          "AC-RTD4 current and unpinned")


def ac_rtd5():
    """CLI codes are pinned, --json is byte-stable, and nothing is written."""
    stale = make_world([entry(2300),
                        entry(2333, declared_by="R2333")], head="R2331")
    current = make_world([entry(2300)], head="R2331")
    unpinned = make_world(entries=None)
    unreadable = make_world(raw="{not json")
    before = file_map(stale)
    code0, out0, _ = run_cli(["--check"], world=current)
    code0_json, out_json, _ = run_cli(["--check", "--json"], world=current)
    code2_json, out_stale, _ = run_cli(["--check", "--json"], world=stale)
    again, out_again, _ = run_cli(["--check", "--json"], world=stale)
    code2, out2, _ = run_cli(["--check"], world=stale)
    code2_unp, out_unp, _ = run_cli(["--check"], world=unpinned)
    code3, out3, _ = run_cli(["--check"], world=unreadable)
    code5, out5, err5 = run_cli(["--nope"])
    after = file_map(stale)
    body = json.loads(out_json) if out_json.strip() else {}
    stale_body = json.loads(out_stale) if out_stale.strip() else {}
    check(code0 == 0 and "HEAD-CURRENT" in out0
          and code0_json == 0 and tuple(body.keys()) == DR.REPORT_KEYS
          and body.get("verdict") == "HEAD-CURRENT"
          and code2_json == 2 and stale_body.get("verdict") == "HEAD-STALE"
          and again == 2 and out_again == out_stale
          and code2 == 2 and "HEAD-STALE" in out2
          and code2_unp == 2 and "UNPINNED" in out_unp
          and code3 == 3 and "E_RTR_UNREADABLE" in out3
          and code5 == 5 and "E_RTD_BAD_ARGS" in out5
          and before == after,
          "AC-RTD5 CLI codes")


def code_only(text):
    """The source with comments and docstrings removed.

    A docstring that NAMES a forbidden call is not a call (the R2346 AC-SEG6
    lesson): the assertion reads executable text only.
    """
    without_docstrings = re.sub(r'"""(?:.|\n)*?"""', '', text)
    without_docstrings = re.sub(r"'''(?:.|\n)*?'''", '', without_docstrings)
    return re.sub(r"#[^\n]*", "", without_docstrings)


def ac_rtd6():
    """Pure ASCII, stdlib only, no clock, no network, no write path, wired."""
    raw = io.open(MODULE, "rb").read()
    try:
        text = raw.decode("ascii")
        ascii_ok = True
    except (UnicodeDecodeError, ValueError):
        text = raw.decode("utf-8", "replace")
        ascii_ok = False
    code = code_only(text)
    imports = set(re.findall(r"^import (\w+)", code, re.M))
    forbidden = ("open(", "socket", "urllib", "http.client", "requests",
                 "import time", "datetime", "time.time",
                 "os.replace", "os.remove", "unlink", "rmtree")
    clean = [token for token in forbidden if token in code]
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('("%s"' % LABEL) in runner and \
        "test_residue_triage_decl_reason.py" in runner
    check(ascii_ok
          and imports <= {"json", "os", "sys", "residue_triage"}
          and not clean
          and wired,
          "AC-RTD6 purity and wiring")


def main():
    for name in ("ac_rtd1", "ac_rtd2", "ac_rtd3", "ac_rtd4", "ac_rtd5",
                 "ac_rtd6"):
        globals()[name]()
    total = PASSES + FAILS
    verdict = "PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, total))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())