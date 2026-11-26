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
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import state_append as SA  # noqa: E402
import logs_toolkit as LT  # noqa: E402
import state_io  # noqa: E402

EXPECTED_CRITERIA = 13
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


def ac_rsa11():
    """AC-RSA11: one log item is one line (R3309).

    Measured before the gate: `--line "a\\nsecond."` and a `--tokens` payload
    carrying a break both landed and the stored item carried the break. The
    archive is appended with "\\n".join(window), so such an item cannot come
    back as one line - the R3308 stream proof was the surface that noticed.
    Four refusal arms (embedded, terminal, bare CR, tokens face) each name
    E_RSA_NEWLINE, cost zero bytes, and leave no break-bearing item; a plain
    single line still lands, so this is not a gate that refuses everything.
    """
    cases = [
        ("--line embedded", "2026-11-16 R9001 NOTE first\nsecond.", None),
        ("--line terminal", "2026-11-16 R9001 NOTE ends here.\n", None),
        ("--line bare CR", "2026-11-16 R9001 NOTE ends here.\r", None),
        ("--tokens embedded", None, "local=~1k api=0\napi_reason=one line"),
    ]
    rows = []
    folders = []
    for name, line, tokens in cases:
        folder, path = world(["2026-11-16 R9001 PRODUCT: an older round"])
        folders.append(folder)
        before = fingerprint(path)
        argv = ["--state", path, "--round", "9001"]
        if line is not None:
            argv += ["--line", line]
        if tokens is not None:
            argv += ["--tokens", tokens]
        code, out, _ = run_cli(argv)
        after = fingerprint(path)
        log = json.loads(io.open(path, encoding="utf-8").read())["log"]
        breaks = len([item for item in log if "\n" in item or "\r" in item])
        rows.append((name, code, "E_RSA_NEWLINE" in out, before == after,
                     breaks))
    folder, path = world(["2026-11-16 R9001 PRODUCT: an older round"])
    folders.append(folder)
    code, out, _ = run_cli(["--state", path, "--round", "9001", "--line",
                            "2026-11-16 R9001 PLAIN one single line."])
    log = json.loads(io.open(path, encoding="utf-8").read())["log"]
    plain_ok = (code == 0 and "APPEND" in out and len(log) == 2
                and not any("\n" in item or "\r" in item for item in log))
    ok = (all(rc == 2 and named and same and breaks == 0
              for _, rc, named, same, breaks in rows) and plain_ok)
    if not ok:
        print("  measured: rows=%r plain=%r code=%r out=%r"
              % (rows, plain_ok, code, out), flush=True)
    check(ok, "AC-RSA11 a line break is refused at the write station on both "
          "faces with E_RSA_NEWLINE and zero bytes written, while an ordinary "
          "single line still lands")
    for folder in folders:
        cleanup(folder)


def ac_rsa12():
    """AC-RSA12: the tick station publishes the heartbeat row it did not write.

    R3317..R3319 each opened with heartbeat.txt two ticks behind state.json,
    because a round that advances the tick through this vehicle never reached
    closeout step 1.6. The write stays there (AC-COUT13(d) pins the order),
    so this station reports the distance instead of staying silent: a lagging
    row reads hb=lag=<n>, a fresh one reads hb=tick=<n>, a row stamped past
    this state reads hb=ahead=<n>, a world with no row reads hb=none, and a
    private world reads hb=skipped. None of the arms may
    move a heartbeat byte - reading is the whole change.
    """
    folder = tempfile.mkdtemp(prefix="rsa-live-")
    os.makedirs(os.path.join(folder, "src", "os"))
    path = os.path.join(folder, "src", "os", "state.json")
    hb_path = os.path.join(folder, "heartbeat.txt")
    try:
        data = {"tick": 10, "log": ["2026-11-16 R9001 PRODUCT: an older round"],
                "benchmarks_refreshed": "2026-11-16"}
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(state_io.dump_canon(data))
        with io.open(hb_path, "wb") as handle:
            handle.write(b"tick 8\n")
        hb_before = fingerprint(hb_path)
        code_a, out_a, _ = run_cli(["--state", path, "--round", "9002",
                                    "--tick", "--line",
                                    "2026-11-16 R9002 PRODUCT: lagging row"])
        tick_a = json.loads(io.open(path, encoding="utf-8").read())["tick"]
        a_ok = (code_a == 0 and "hb=lag=%d" % (tick_a - 8) in out_a
                and fingerprint(hb_path) == hb_before)
        state_before = fingerprint(path)
        code_b, out_b, _ = run_cli(["--state", path, "--round", "9003",
                                    "--tick", "--check", "--line",
                                    "2026-11-16 R9003 PRODUCT: dry run"])
        b_ok = (code_b == 0 and "hb=lag=%d" % (tick_a + 1 - 8) in out_b
                and fingerprint(path) == state_before
                and fingerprint(hb_path) == hb_before)
        with io.open(hb_path, "wb") as handle:
            handle.write(("tick %d\n" % (tick_a + 1)).encode("ascii"))
        code_c, out_c, _ = run_cli(["--state", path, "--round", "9004",
                                    "--tick", "--line",
                                    "2026-11-16 R9004 PRODUCT: fresh row"])
        c_ok = code_c == 0 and "hb=tick=%d" % (tick_a + 1) in out_c
        tick_c = json.loads(io.open(path, encoding="utf-8").read())["tick"]
        with io.open(hb_path, "wb") as handle:
            handle.write(("tick %d\n" % (tick_c + 2)).encode("ascii"))
        hb_ahead = fingerprint(hb_path)
        code_e, out_e, _ = run_cli(["--state", path, "--round", "9005",
                                    "--tick", "--line",
                                    "2026-11-16 R9005 PRODUCT: row ahead"])
        # R3321: a row stamped past the state is named, not printed as a
        # negative lag. Measured before this arm: 25 hb= lines in qa/ carried
        # lag=/tick= and none carried a minus sign, so the shape had no name.
        e_ok = (code_e == 0 and "hb=ahead=1" in out_e
                and "lag=-" not in out_e and fingerprint(hb_path) == hb_ahead)
    finally:
        shutil.rmtree(folder, ignore_errors=True)

    flat, flat_path = world(["2026-11-16 R9001 PRODUCT: a private world"])
    try:
        code_d, out_d, _ = run_cli(["--state", flat_path, "--round", "9002",
                                    "--tick", "--line",
                                    "2026-11-16 R9002 PRODUCT: flat world"])
        d_ok = (code_d == 0 and "hb=skipped" in out_d
                and not os.path.exists(os.path.join(flat, "heartbeat.txt")))
    finally:
        cleanup(flat)

    ok = a_ok and b_ok and c_ok and d_ok and e_ok
    if not ok:
        print("  measured: a=%r b=%r c=%r d=%r e=%r out_a=%r out_b=%r "
              "out_c=%r out_d=%r out_e=%r"
              % (a_ok, b_ok, c_ok, d_ok, e_ok, out_a.strip()[:120],
                 out_b.strip()[:120], out_c.strip()[:120],
                 out_d.strip()[:120], out_e.strip()[:120]), flush=True)
    check(ok, "AC-RSA12 the tick station reports the heartbeat row it read "
          "(lag, tick, ahead, skipped) and moves no heartbeat byte")


def ac_rsa13():
    """AC-RSA13: a dated budget line is refused at birth (R3517).

    Three arms, in this order:
      (a) 'YYYY-MM-DD R<n> tokens: ...' reads E_RSA_LEDGER_DATE with rc=2,
          zero bytes moved and no temp file, because that shape classifies
          as a round narrative and its round then reads as having no budget
          line at all (measured on the shipped tree at R3514);
      (b) the same payload in the shape the law reads (bare 'R<n> tokens:')
          and the --tokens/--round vehicle both still land;
      (c) narrowness: a DATED NON-ledger line ('2026-11-26 R9001 PRODUCT:')
          is not caught by this gate - the guard is about the ledger shape,
          not about date prefixes in general.
    """
    folder, path = world(["2026-11-16 R9001 PRODUCT: a dated older round"])
    ok = False
    try:
        before = fingerprint(path)
        names_before = sorted(os.listdir(folder))
        dated = "2026-11-16 R9002 tokens: local=1 api=0 api_reason=spent"
        code_a, out_a, _ = run_cli(["--state", path, "--round", "9002",
                                    "--line", dated])
        after = fingerprint(path)
        arm_a = (code_a == 2 and "E_RSA_LEDGER_DATE" in out_a
                 and before == after and names_before == sorted(os.listdir(folder))
                 and "repair_tokens_prefix_R2597" in out_a)
        code_b1, out_b1, _ = run_cli(["--state", path, "--round", "9002",
                                      "--line", "R9002 tokens: local=1 api=0",
                                      "--tick"])
        code_b2, out_b2, _ = run_cli(["--state", path, "--round", "9003",
                                      "--tokens", "local=2 api=0", "--tick"])
        payload = state_io.parse(read_text(path))
        arm_b = (code_b1 == 0 and code_b2 == 0
                 and "R9002 tokens: local=1 api=0" in payload["log"]
                 and "R9003 tokens: local=2 api=0" in payload["log"])
        code_c, out_c, _ = run_cli(["--state", path, "--round", "9004",
                                    "--line",
                                    "2026-11-16 R9004 PRODUCT: dated but not "
                                    "a budget line", "--tick"])
        arm_c = code_c == 0 and "E_RSA_LEDGER_DATE" not in out_c
        ok = arm_a and arm_b and arm_c
        if not ok:
            print("  measured: a=%r b=%r c=%r out_a=%r out_c=%r"
                  % (arm_a, arm_b, arm_c, out_a.strip()[:120],
                     out_c.strip()[:120]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-RSA13 a dated budget line reads E_RSA_LEDGER_DATE with "
          "rc=2 and zero bytes moved, the two lawful shapes still land, and "
          "a dated non-ledger line is not caught by the gate")


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
    ac_rsa11()
    ac_rsa12()
    ac_rsa13()
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
