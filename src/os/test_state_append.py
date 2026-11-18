"""state_append suite (R2833; criteria AC-RSA1..AC-RSA7 were pinned in the
R2833 row of src/os/backlog.md BEFORE this file existed - the pin row was
committed ahead of the code).

What this proves: 223 one-off state_append_R*.py scripts had accumulated,
each with its own serialisation and write path, which is why the round-main
shape law (R2832) had no production call site and a forgotten date prefix
could only be found later, by a crash or by a battery leg. state_append.py
is now the single vehicle and this suite pins its laws:

  - the shape gate runs BEFORE the write and costs zero bytes on refusal;
  - a duplicate line is refused, not doubled;
  - the payload moves exactly one log line and the tick, nothing else;
  - the tick never goes backwards;
  - a refusal leaves no temp file behind;
  - a document the FOLD reader cannot read is refused before the write, and
    the question is asked of that reader rather than of a constant (R2915).

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import state_append as SA  # noqa: E402
import logs_toolkit as LT  # noqa: E402
import state_io  # noqa: E402

EXPECTED_CRITERIA = 10
MODULE = os.path.join(BASE, "state_append.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-append"

PASSES = 0
FAILS = 0

NET_IMPORTS = ("urllib", "http.client", "requests", "socket", "httpx")


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def world(lines, tick=10):
    folder = tempfile.mkdtemp(prefix="rsa-")
    path = os.path.join(folder, "state.json")
    data = {"tick": tick, "log": list(lines),
            "benchmarks_refreshed": "2026-11-16"}
    text = state_io.dump_canon(data)
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return folder, path


def cleanup(folder):
    for name in os.listdir(folder):
        os.remove(os.path.join(folder, name))
    os.rmdir(folder)


def fingerprint(path):
    with io.open(path, "rb") as handle:
        raw = handle.read()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def run_cli(argv):
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with contextlib.redirect_stderr(err):
            try:
                code = SA.main(argv)
            except SystemExit as exc:
                code = exc.code
    return code, buf.getvalue(), err.getvalue()


def ac_rsa1():
    """AC-RSA1: one vehicle, built on the two existing libraries."""
    source = io.open(MODULE, encoding="utf-8").read()
    uses_libs = ("import state_io" in source
                 and "import ledger_lines" in source
                 and "read_raw(" in source
                 and "dump_canon(" in source
                 and "check_round_main_shape(" in source)
    roots = set()
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            roots.add(stripped[len("import "):].split(",")[0].split(" ")[0]
                      .split(".")[0])
        elif stripped.startswith("from ") and " import " in stripped:
            roots.add(stripped[len("from "):].split(" ")[0].split(".")[0])
    no_net = not (roots & set(NET_IMPORTS))
    with io.open(MODULE, "rb") as handle:
        ascii_only = all(byte < 128 for byte in handle.read())
    code, out, _ = run_cli(["--help"])
    ok = (uses_libs and no_net and ascii_only and code == 0
          and "state_append.py" in out)
    if not ok:
        print("  measured: uses_libs=%r roots=%r ascii=%r help=%r"
              % (uses_libs, sorted(roots), ascii_only, code), flush=True)
    check(ok, "AC-RSA1 the one vehicle reads through state_io, gates through "
          "ledger_lines, is ASCII with no net, and answers --help")


def ac_rsa2():
    """AC-RSA2: an undated round line is refused BEFORE the write."""
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
    try:
        before = fingerprint(path)
        code, out, _ = run_cli(["--state", path, "--round", "9002",
                                "--line",
                                "R9002 PRODUCT: the prefix was forgotten"])
        after = fingerprint(path)
        ok = (code == 2 and "E_RSA_NO_DATE" in out and before == after)
        if not ok:
            print("  measured: code=%r out=%r before=%r after=%r"
                  % (code, out.strip()[:120], before, after), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA2 an undated round line is refused by name with rc=2 "
          "and the state file keeps its exact bytes")


def ac_rsa3():
    """AC-RSA3: the same line twice is refused, never doubled."""
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
    line = "2026-11-16 R9002 PRODUCT: written once"
    try:
        code1, out1, _ = run_cli(["--state", path, "--round", "9002",
                                  "--tick", "--line", line])
        mid = fingerprint(path)
        code2, out2, _ = run_cli(["--state", path, "--round", "9002",
                                  "--tick", "--line", line])
        end = fingerprint(path)
        log = state_io.parse(io.open(path, encoding="utf-8").read())["log"]
        ok = (code1 == 0 and code2 == 0 and mid == end
              and "E_RSA_DUPLICATE" in out2 and log.count(line) == 1)
        if not ok:
            print("  measured: code=%r/%r dup=%r count=%r"
                  % (code1, code2, "E_RSA_DUPLICATE" in out2,
                     log.count(line)), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA3 a repeated line reads E_RSA_DUPLICATE with rc=0, "
          "keeps the bytes, and appears exactly once")


def ac_rsa4():
    """AC-RSA4: exactly one log line and the tick move, nothing else."""
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"],
                         tick=41)
    try:
        before = state_io.parse(io.open(path, encoding="utf-8").read())
        code, out, _ = run_cli(["--state", path, "--round", "9002",
                                "--tick", "--line",
                                "2026-11-16 R9002 PRODUCT: appended once"])
        after = state_io.parse(io.open(path, encoding="utf-8").read())
        rest_same = all(after.get(key) == before.get(key)
                        for key in before
                        if key not in ("log", "tick"))
        ok = (code == 0
              and len(after["log"]) == len(before["log"]) + 1
              and after["tick"] == before["tick"] + 1
              and after["log"][-1] == "2026-11-16 R9002 PRODUCT: appended once"
              and rest_same
              and "fold_margin=" in out)
        if not ok:
            print("  measured: code=%r log=%r tick=%r rest=%r out=%r"
                  % (code, len(after["log"]), after["tick"], rest_same,
                     out.strip()[:120]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA4 the write adds exactly one log line and one tick, "
          "leaves every other key equal, and reports the fold margin")


def ac_rsa5():
    """AC-RSA5: the tick may not go backwards."""
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"],
                         tick=10)
    try:
        before = fingerprint(path)
        code, out, _ = run_cli(["--state", path, "--round", "9002",
                                "--tick", "5", "--line",
                                "2026-11-16 R9002 PRODUCT: forward only"])
        after = fingerprint(path)
        ok = (code == 2 and "E_RSA_TICK_BACK" in out and before == after)
        if not ok:
            print("  measured: code=%r out=%r same=%r"
                  % (code, out.strip()[:120], before == after), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA5 a tick that would go backwards is refused with "
          "E_RSA_TICK_BACK and zero bytes written")


def ac_rsa6():
    """AC-RSA6: every refusal leaves no temp file and no half write."""
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
    try:
        run_cli(["--state", path, "--round", "9002", "--line",
                 "R9002 PRODUCT: undated refusal"])
        run_cli(["--state", path, "--round", "9002", "--tick", "1",
                 "--line", "2026-11-16 R9002 PRODUCT: backwards tick"])
        run_cli(["--state", path, "--round", "9002", "--tick",
                 "--line", "2026-11-16 R9002 PRODUCT: never empty"])
        run_cli(["--state", path, "--round", "9002", "--line",
                 "2026-11-16 R9002 PRODUCT: never empty"])
        leftovers = sorted(os.listdir(folder))
        ok = leftovers == ["state.json"]
        if not ok:
            print("  measured: leftovers=%r" % (leftovers,), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA6 four refusals in a row leave the folder holding only "
          "state.json, with no .state_append_ temp file")


def append_at_indent(path, round_no, line, indent):
    """Append while the canonical writer is driven to another item indent."""
    saved = state_io.ITEM_INDENT
    state_io.ITEM_INDENT = indent
    try:
        return run_cli(["--state", path, "--round", str(round_no),
                        "--tick", "--line", line])
    finally:
        state_io.ITEM_INDENT = saved


def read_text(path):
    with io.open(path, "rb") as handle:
        return handle.read().decode("utf-8")


def caliber_of(text):
    """Return the log-item caliber the FOLD reader derives, or None."""
    log = state_io.parse(text)["log"]
    layout = LT.split_ps_layout(text, len(log))
    return None if layout is None else layout[4]


def would_be_text(path, extra_line, indent):
    """The document the writer would emit at this indent, rebuilt its way."""
    saved = state_io.ITEM_INDENT
    state_io.ITEM_INDENT = indent
    try:
        data = state_io.parse(read_text(path))
        data["log"] = list(data["log"]) + [extra_line]
        return state_io.dump_canon(data)
    finally:
        state_io.ITEM_INDENT = saved


def ac_rsa8():
    """AC-RSA8: the fold-unreadable shape is refused BEFORE the write."""
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
    line = "2026-11-16 R9002 PRODUCT: the four-space shape"
    try:
        before = fingerprint(path)
        names_before = sorted(os.listdir(folder))
        code, out, _ = append_at_indent(path, 9002, line, 4)
        after = fingerprint(path)
        names_after = sorted(os.listdir(folder))
        ok = (code == 2 and "E_RSA_LAYOUT" in out and before == after
              and names_before == names_after and "fix-indent" in out)
        if not ok:
            print("  measured: code=%r out=%r same=%r leftovers=%r"
                  % (code, out.strip()[:160], before == after, names_after),
                  flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA8 an append that would write 4-space log items reads "
          "E_RSA_LAYOUT with rc=2, zero bytes moved, no temp file, and the "
          "hint names the shipped repair")


def ac_rsa9():
    """AC-RSA9: both healthy calibers are written AND labelled right."""
    rows = []
    for indent in (2, 16):
        folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
        try:
            code, out, _ = append_at_indent(
                path, 9002,
                "2026-11-16 R9002 PRODUCT: written at %d" % indent, indent)
            text = read_text(path)
            profile = LT.eol_profile(text.encode("utf-8"))
            rows.append((indent, code, caliber_of(text),
                         profile["indent_ok"]))
        finally:
            cleanup(folder)
    ok = all(code == 0 and caliber == indent and indent_ok
             for indent, code, caliber, indent_ok in rows)
    if not ok:
        print("  measured: rows=%r" % (rows,), flush=True)
    check(ok, "AC-RSA9 the shipped 2-space and a 16-space write both land, "
          "each labelled by the fold reader at its own caliber and read "
          "indent_ok by eol_profile")


def ac_rsa10():
    """AC-RSA10: the refusal is the fold's verdict, not a second opinion."""
    rows = []
    for indent in (4, 8):
        folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
        line = "2026-11-16 R9002 PRODUCT: probe at %d" % indent
        try:
            code, out, _ = append_at_indent(path, 9002, line, indent)
            probe = would_be_text(path, line, indent)
            profile = LT.eol_profile(probe.encode("utf-8"))
            rows.append((indent, code, "E_RSA_LAYOUT" in out,
                         profile["indent_ok"], caliber_of(probe)))
        finally:
            cleanup(folder)
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
    try:
        code, out, _ = run_cli(["--state", path, "--round", "9002", "--tick",
                                "--line", "2026-11-16 R9002 PRODUCT: canon"])
        health = (code, LT.eol_profile(read_text(path).encode("utf-8"))
                  ["indent_ok"])
    finally:
        cleanup(folder)
    refused = all(code == 2 and named and not indent_ok and caliber is None
                  for _, code, named, indent_ok, caliber in rows)
    ok = refused and health == (0, True)
    if not ok:
        print("  measured: rows=%r health=%r" % (rows, health), flush=True)
    check(ok, "AC-RSA10 eol_profile reads indent_ok=False with no caliber on "
          "the very 4-space and 8-space documents state_append refuses, and "
          "indent_ok=True on the canonical one it writes")


def ac_rsa7():
    """AC-RSA7: registered with this exact criteria count."""
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    registered = match is not None
    declared = int(match.group(1)) if registered else -1
    ok = registered and declared == EXPECTED_CRITERIA
    if not ok:
        print("  measured: registered=%r declared=%r expected=%r"
              % (registered, declared, EXPECTED_CRITERIA), flush=True)
    check(ok, "AC-RSA7 the registry declares this suite at %d criteria"
          % EXPECTED_CRITERIA)


def main():
    print("state append suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_rsa1()
    ac_rsa2()
    ac_rsa3()
    ac_rsa4()
    ac_rsa5()
    ac_rsa6()
    ac_rsa8()
    ac_rsa9()
    ac_rsa10()
    ac_rsa7()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
