"""Battery suite for tools/battery_shard.py - AC-BSH1..AC-BSH8.

AC-BSGB9/AC-BSGB10 (the exact-label selector) were pinned at R2843, before that
face existed, when the three bare legacy labels ledger/member/pay (43 criteria)
turned out to be reachable by NO slice: a prefix test cannot name them without
also dragging in every "ledger-*" suite, and the family slice is drawn by "does
not start with ledger-/member-/pay-", which excludes them by construction.

The eight criteria belong to the tool and were pinned in src/os/backlog.md at
R2797, BEFORE the tool existed. This suite is what finally puts them under a
battery row; AC-BSGB1..AC-BSGB8 (the guard shape) were pinned at R2798, again
before this file existed.

Scope, stated honestly: the suite never runs a real registry family, because a
shard of a real family is seconds of child processes on every battery run and
the tool's own R2797 measurement already stands as that evidence. What is
guarded here is the MACHINERY - registry-by-import, the selector law, the
slice-parity construction and its timeout override, the verdict rule, the
accounting recomputation, the evidence birth site, read-only posture and the
non-battery refusal - each driven through the real functions in a PRIVATE world
of probe suites under the system temp directory, which is removed before the
run ends.

Every check is read-only against the repo: the registry source, the real
sandbox book and the shipped evidence are stat-signed before and after.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "battery_shard.py")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger", "ledger.db")
EVIDENCE = os.path.join(ROOT, "qa", "battery-shard-R2797.log")

FAILS = []
CHECKS = []

PROBE_GOOD = """import os
import sys
print("PROBE cwd=%s" % os.getcwd())
print("PROBE env=%s" % os.environ.get("PYTHONIOENCODING"))
print("PROBE exe=%s" % sys.executable)
print("  | PASS probe-good")
print("SUITE PASS 1/1")
"""

PROBE_BAD = """print("  | FAIL probe-bad")
print("SUITE FAIL 0/1")
raise SystemExit(1)
"""

PROBE_SLOW = """import time
time.sleep(5)
print("  | PASS probe-slow")
print("SUITE PASS 1/1")
"""

PROBE_BARE = """print("SUITE PASS 1/1")
"""

# AC-BSGB14 (R2881): the SAME verdict row counts assertions; only the
# declaration differs. A registry row of 8 criteria beside a bare 21/21 is the
# under-declared unit class this criterion refuses by name.
PROBE_UNIT_BARE = """print("  | PASS probe-unit-bare")
print("SUITE PASS 21/21")
"""

PROBE_UNIT_DECL = """print("  | PASS probe-unit-decl")
print("suite: 21 assertions over 8 criteria")
print("SUITE PASS 21/21")
"""

# R2859: the declared-units pair. Both probes print the SAME verdict row; only
# the declaration differs, so a mismatch can only come from the declaration.
PROBE_DECL_OK = """print("  | PASS probe-decl-ok")
print("suite: 21 assertions over 8 criteria")
print("SUITE PASS 21/21")
"""

PROBE_DECL_BAD = """print("  | PASS probe-decl-bad")
print("suite: 21 assertions over 7 criteria")
print("SUITE PASS 21/21")
"""


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stat_sig(path):
    if not os.path.exists(path):
        return None
    return (os.path.getsize(path), os.path.getmtime(path))


def write_probes(base):
    for name, body in (("probe_good.py", PROBE_GOOD),
                       ("probe_bad.py", PROBE_BAD),
                       ("probe_slow.py", PROBE_SLOW),
                       ("probe_bare.py", PROBE_BARE),
                       ("probe_decl_ok.py", PROBE_DECL_OK),
                       ("probe_decl_bad.py", PROBE_DECL_BAD)):
        with open(os.path.join(base, name), "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(body)


def run_cli(shard, argv):
    """Drive the real main() and keep whatever it printed."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = shard.main(argv)
    return code, buf.getvalue()


def patch_registry(shard, rows, base):
    shard.registry = lambda: (list(rows), base, 600, {})


def main():
    sig_registry = stat_sig(REGISTRY)
    sig_ledger = stat_sig(LEDGER)
    sig_evidence = stat_sig(EVIDENCE)

    shard = load(TOOL, "bsh_under_test")
    source = read_bytes(TOOL).decode("utf-8", "replace")

    # --- independent registry re-derivation (never the tool's own report) ---
    reg = load(REGISTRY, "bsh_registry_independent")
    rows = [(r[0], r[1], int(r[2])) for r in reg.SUITES]
    suites_n = len(rows)
    crit_n = sum(r[2] for r in rows)
    labels = [r[0] for r in rows]

    # AC-BSGB1 - registry-by-import: the tool must quote the SAME numbers, and
    # must not carry either total or any individual suite path as a literal.
    code, out = run_cli(shard, ["--dry"])
    header = [l for l in out.splitlines() if l.startswith("SHARD scope=SHARD")]
    quoted_suites = quoted_crit = -1
    if header:
        for piece in header[0].split():
            if piece.startswith("registry_suites="):
                quoted_suites = int(piece.split("=", 1)[1])
            if piece.startswith("registry_criteria="):
                quoted_crit = int(piece.split("=", 1)[1])
    suite_paths = [r[1].replace("\\", "/").split("/")[-1] for r in rows]
    leaked = [p for p in suite_paths if p in source]
    ok("AC-BSGB1",
       code == 0 and quoted_suites == suites_n and quoted_crit == crit_n
       and str(suites_n) not in source and str(crit_n) not in source
       and not leaked,
       "suites=%d crit=%d quoted=%d/%d leaked=%d"
       % (suites_n, crit_n, quoted_suites, quoted_crit, len(leaked)))

    # AC-BSGB2 - the selector law, measured against an independent derivation.
    prefix = "os-ledger"
    expected = [l for l in labels if l.startswith(prefix)]
    picked = [r[0] for r in shard.select(rows, [prefix], 0)]
    code_no, out_no = run_cli(shard, ["--match", "zzz-no-such-family"])
    dry_code, dry_out = run_cli(shard, ["--dry", "--match", prefix])
    dry_selected = -1
    dry_executed = -1
    for line in dry_out.splitlines():
        if line.startswith("SHARD rc=0 scope=SHARD dry=True"):
            for piece in line.split():
                if piece.startswith("executed="):
                    dry_executed = int(piece.split("=", 1)[1])
                if piece.startswith("selected="):
                    dry_selected = int(piece.split("=", 1)[1])
    ok("AC-BSGB2",
       picked == expected and bool(expected)
       and code_no == 2 and "E_NO_MATCH" in out_no
       and dry_code == 0 and dry_selected == len(expected)
       and dry_executed == 0,
       "expected=%d picked=%d nomatch_rc=%d dry_exec=%d"
       % (len(expected), len(picked), code_no, dry_executed))

    # AC-BSGB9 (R2843) - exact names are a union with the prefixes, kept in
    # registry order with no duplicate row, and they are the only way to reach
    # a bare legacy label: a prefix test for "ledger" drags in every
    # "ledger-*" suite, so foo = 336 rows instead of 3 (measured R2843).
    bare = ("ledger", "member", "pay")
    bare_expected = [l for l in labels if l in bare]
    bare_crit = sum(r[2] for r in rows if r[0] in bare)
    exact_picked = [r[0] for r in shard.select(rows, [], 0, list(bare))]
    union = [r[0] for r in shard.select(rows, [prefix], 0, ["ledger"])]
    union_expected = [l for l in labels if l == "ledger" or l.startswith(prefix)]
    no_dup = len(union) == len(set(union))
    code_x, out_x = run_cli(shard, ["--dry", "--exact", "ledger",
                                    "--exact", "member", "--exact", "pay"])
    x_selected = x_crit = -1
    for line in out_x.splitlines():
        if line.startswith("SHARD scope=SHARD"):
            for piece in line.split():
                if piece.startswith("selected_criteria="):
                    x_crit = int(piece.split("=", 1)[1])
        if line.startswith("SHARD rc=0 scope=SHARD dry=True"):
            for piece in line.split():
                if piece.startswith("selected="):
                    x_selected = int(piece.split("=", 1)[1])
    ok("AC-BSGB9",
       len(bare_expected) == 3 and exact_picked == bare_expected
       and union == union_expected and no_dup
       and code_x == 0 and x_selected == 3 and x_crit == bare_crit,
       "bare=%d exact=%d crit=%d union=%d dup=%s dry_sel=%d dry_crit=%d"
       % (len(bare_expected), len(exact_picked), bare_crit, len(union),
          not no_dup, x_selected, x_crit))

    # AC-BSGB10 (R2843) - an exact name the registry does not carry refuses BY
    # NAME instead of selecting nothing, both at the function and at the CLI.
    code_nm, out_nm = run_cli(shard, ["--dry", "--exact", "zzz-no-such"])
    named_cli = "E_NO_MATCH" in out_nm and "zzz-no-such" in out_nm
    try:
        shard.select(rows, [], 0, ["zzz-no-such"])
        named_fn = False
    except shard.Refuse as exc:
        named_fn = "E_NO_MATCH" in str(exc) and "zzz-no-such" in str(exc)
    ok("AC-BSGB10", code_nm == 2 and named_cli and named_fn,
       "cli_rc=%d named_cli=%s named_fn=%s" % (code_nm, named_cli, named_fn))

    # AC-SK1 (R2851) - the two rows the law already read are unchanged: an
    # explicit word wins, a numbers-only row derives, and "green" is still not
    # the law's vocabulary.
    read = shard.parse_suite_row
    sk1 = (read("SUITE PASS 6/6\n") == ("PASS", 6, 6)
           and read("SUITE FAIL 5/6\n") == ("FAIL", 5, 6)
           and read("SUITE 8/8\n") == ("PASS", 8, 8)
           and read("SUITE 7/8\n") == ("FAIL", 7, 8)
           and read("SUITE 6/6 green\n") is None)
    ok("AC-SK1", sk1, "canonical+numeric unchanged")

    # AC-SK2 (R2851) - a verdict word joined to the pair by other punctuation is
    # the same row; the numbers are the row's own, never a default.
    sk2 = (read("SUITE PASS (7/7)\n") == ("PASS", 7, 7)
           and read("SUITE PASS (6/6 criteria green)\n") == ("PASS", 6, 6)
           and read("SUITE PASS: 7/7\n") == ("PASS", 7, 7)
           and read("SUITE PASS - 19/19 green\n") == ("PASS", 19, 19)
           and read("SUITE PASS (8/8 criteria green)\n") == ("PASS", 8, 8))
    ok("AC-SK2", sk2, "punct pair skin read")

    # AC-SK3 (R2851) - a labelled pair names the suite, so the verdict is
    # derived from p==t exactly as the numbers-only row: never invented.
    sk3 = (read("SUITE apidev: 7/7 criteria pass\n") == ("PASS", 7, 7)
           and read("SUITE foo: 5/6\n") == ("FAIL", 5, 6))
    ok("AC-SK3", sk3, "label pair derives from p==t")

    # AC-SK4 (R2851) - a counter row states the verdict as counts. passes may be
    # assertions rather than criteria, so 8 passes over 6 criteria with 0 fails
    # is a PASS; the fail count, not p==t, decides.
    sk4 = (read("SUITE RESULT passes=6 fails=0 criteria=6\n") == ("PASS", 6, 6)
           and read("SUITE PASS criteria=6 passes=8 fails=0\n") == ("PASS", 8, 6)
           and read("SUITE os-x expected-criteria=6 pass=6 fail=0\n") == ("PASS", 6, 6)
           and read("SUITE PASS exit=0 pass-lines=6 fail-lines=0 criteria=6\n")
           == ("PASS", 6, 6)
           and read("SUITE PASS: 6 criteria, 6 pass, 0 fail\n") == ("PASS", 6, 6))
    ok("AC-SK4", sk4, "counter skin bound to fails")

    # AC-SK5 (R2851) - red controls: every contradiction reads FAIL or refuses.
    # A row that cannot say its verdict from a fail count is not guessed.
    sk5 = (read("SUITE FAIL (7/7 criteria green)\n") == ("FAIL", 7, 7)
           and read("SUITE PASS (7/8 criteria green)\n") == ("FAIL", 7, 8)
           and read("SUITE foo: 5/6\n") == ("FAIL", 5, 6)
           and read("SUITE PASS criteria=6 passes=5 fails=1\n") == ("FAIL", 5, 6)
           and read("SUITE RESULT passes=6 fails=1 criteria=6\n") == ("FAIL", 6, 6)
           and read("SUITE PASS exit=1 pass-lines=6 fail-lines=1 criteria=6\n")
           == ("FAIL", 6, 6)
           and read("SUITE PASS 7 checks\n") is None
           and read("SUITE PASS\n") is None)
    ok("AC-SK5", sk5, "8 red controls")

    # AC-SK6 (R2851) - order: a canonical row anywhere wins over a legacy row,
    # and among the new skins the LAST row is the reading (numeric's rule).
    sk6 = (read("SUITE FAIL 1/2\nSUITE PASS (2/2)\n") == ("FAIL", 1, 2)
           and read("SUITE PASS (5/5)\nSUITE PASS (7/7 criteria green)\n")
           == ("PASS", 7, 7))
    ok("AC-SK6", sk6, "canonical wins, new skins take the last row")

    # AC-BSGB3 - slice parity: the probe sees the battery's own construction,
    # and a one-second per-label override caps a sleeping probe at 124.
    world = tempfile.mkdtemp(prefix="bsh-probe-")
    try:
        write_probes(world)
        good_path = os.path.join(world, "probe_good.py")
        code_g, out_g, _ = shard.run_one(world, "probe-good", "probe_good.py",
                                        600, {})
        facts = {}
        for line in out_g.splitlines():
            if line.startswith("PROBE "):
                key, _, value = line[6:].partition("=")
                facts[key] = value
        parity = (code_g == 0
                  and facts.get("cwd", "").lower() == os.path.dirname(good_path).lower()
                  and facts.get("env") == "utf-8"
                  and os.path.normcase(facts.get("exe", "")) == os.path.normcase(
                      sys.executable))
        code_t, out_t, _ = shard.run_one(world, "probe-slow", "probe_slow.py",
                                         600, {"probe-slow": 1})
        capped = code_t == 124 and "TIMEOUT suite exceeded the 1s per-suite cap" in out_t
        ok("AC-BSGB3", parity and capped,
           "parity=%s cwd=%s env=%s timeout_rc=%d"
           % (parity, facts.get("cwd", "")[-14:], facts.get("env"), code_t))

        # AC-BSGB4 - the verdict rule, end to end through the real main().
        mixed = [("probe-good", "probe_good.py", 1), ("probe-bad", "probe_bad.py", 1)]
        patch_registry(shard, mixed, world)
        code_m, out_m = run_cli(shard, ["--match", "probe"])
        executed_m = out_m.count("SHARD row ")
        named = "probe-bad:rc=1" in out_m
        only_good = [("probe-good", "probe_good.py", 1)]
        patch_registry(shard, only_good, world)
        code_o, out_o = run_cli(shard, ["--match", "probe"])
        executed_o = out_o.count("SHARD row ")
        ok("AC-BSGB4",
           code_m == 2 and named and executed_m == len(mixed)
           and code_o == 0 and executed_o == len(only_good),
           "mixed_rc=%d named=%s exec=%d green_rc=%d exec_g=%d"
           % (code_m, named, executed_m, code_o, executed_o))

        # AC-BSGB11 (R2853) - the detail counter reads the corpus convention
        # (indented line, optional "| " separator), and absent detail is
        # declared rather than implied by a zero count.
        both = [("probe-good", "probe_good.py", 1),
                ("probe-bare", "probe_bare.py", 1)]
        patch_registry(shard, both, world)
        code_d, out_d = run_cli(shard, ["--match", "probe"])
        rows_d = [l for l in out_d.splitlines() if l.startswith("SHARD row ")]
        good_d = [l for l in rows_d if " probe-good " in l]
        bare_d = [l for l in rows_d if " probe-bare " in l]
        good_ok = bool(good_d) and "pass=1 fail=0 detail=yes" in good_d[0]
        bare_ok = (bool(bare_d) and "pass=0 fail=0 detail=none" in bare_d[0]
                   and "suite=PASS 1/1" in bare_d[0])
        ok("AC-BSGB11", code_d == 0 and good_ok and bare_ok,
           "indented_detail=%s bare_detail=%s rc=%d"
           % (good_ok, bare_ok, code_d))

        # AC-BSGB12 (R2859) - a suite that declares its own criteria count is
        # compared in the registry's unit, and the declaration may not move a
        # verdict: the agreeing probe reads no mismatch, the disagreeing probe
        # reads a NAMED one, and both keep suite=PASS 21/21 and rc=0.
        decl = [("probe-decl-ok", "probe_decl_ok.py", 8),
                ("probe-decl-bad", "probe_decl_bad.py", 8)]
        patch_registry(shard, decl, world)
        code_u, out_u = run_cli(shard, ["--match", "probe-decl"])
        rows_u = [l for l in out_u.splitlines() if l.startswith("SHARD row ")]
        ok_row = [l for l in rows_u if " probe-decl-ok " in l]
        bad_row = [l for l in rows_u if " probe-decl-bad " in l]
        unit_ok = (code_u == 0
                   and bool(ok_row) and "suite=PASS 21/21" in ok_row[0]
                   and "rc=0" in ok_row[0]
                   and bool(bad_row) and "suite=PASS 21/21" in bad_row[0]
                   and "rc=0" in bad_row[0]
                   and "probe-decl-bad:7!=8" in out_u
                   and "probe-decl-ok:8!=8" not in out_u)
        ok("AC-BSGB12", unit_ok,
           "agree_row=%s red_named=%s rc=%d"
           % (bool(ok_row), "probe-decl-bad:7!=8" in out_u, code_u))

        # AC-BSGB5 - accounting is recomputed from the same file's own rows.
        qa_dir = os.path.join(world, "qa")
        os.makedirs(qa_dir)
        shard.QA_DIR = qa_dir
        name = "shard-probe-evidence.log"
        patch_registry(shard, only_good, world)
        code_e, out_e = run_cli(shard, ["--match", "probe", "--evidence", name])
        path = os.path.join(qa_dir, name)
        text = read_bytes(path).decode("utf-8") if os.path.exists(path) else ""
        lines = text.splitlines()
        row_lines = [l for l in lines if l.startswith("SHARD row ")]
        closing = [l for l in lines if l.startswith("SHARD rc=")]
        green_rows = [l for l in row_lines if "rc=0" in l]
        announced_exec = announced_green = -1
        if closing:
            for piece in closing[0].split():
                if piece.startswith("executed="):
                    announced_exec = int(piece.split("=", 1)[1])
                if piece.startswith("green="):
                    announced_green = int(piece.split("=", 1)[1])
        derived = (announced_exec == len(row_lines) and announced_green == len(green_rows)
                   and len(row_lines) == 1)
        check_clean = shard.do_check(name)
        tampered = text.replace("executed=1", "executed=7")
        with open(path, "wb") as handle:
            handle.write(tampered.encode("utf-8"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_bad = shard.do_check(name)
        mismatch_named = "E_EXECUTED_MISMATCH" in buf.getvalue()
        ok("AC-BSGB5",
           code_e == 0 and derived and check_clean == 0
           and check_bad == 2 and mismatch_named,
           "exec=%d rows=%d green=%d clean=%d bad=%d named=%s"
           % (announced_exec, len(row_lines), announced_green, check_clean,
              check_bad, mismatch_named))

        # AC-BSGB8 - the slice must never read as a battery.
        code_claim, out_claim = run_cli(shard, ["--claim", "full"])
        with open(path, "wb") as handle:
            handle.write((text + "BATTERY rc=0 injected\n").encode("utf-8"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_batt = shard.do_check(name)
        batt_named = "E_BATTERY_LINE" in buf.getvalue()
        shipped_no_batt = False
        if os.path.exists(EVIDENCE):
            shipped_no_batt = not any(
                l.startswith("BATTERY")
                for l in read_bytes(EVIDENCE).decode("utf-8", "replace").splitlines())
        ok("AC-BSGB8",
           code_claim == 2 and "E_NOT_FULL" in out_claim
           and batt_named and shipped_no_batt,
           "claim_rc=%d named=%s shipped_clean=%s"
           % (code_claim, batt_named, shipped_no_batt))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # AC-BSGB6 - evidence lives under qa/ and nowhere else, checked before any
    # suite runs; the shipped evidence still verifies through the same writer.
    shard.QA_DIR = os.path.join(ROOT, "qa")
    refusals = 0
    for bad in ("../escape.log", "sub/nested.log",
                os.path.join(ROOT, "qa", "abs.log")):
        try:
            shard.evidence_name(bad)
        except shard.Refuse as exc:
            if "E_EVIDENCE_PATH" in str(exc):
                refusals += 1
    code_path, _ = run_cli(shard, ["--dry", "--evidence", "../escape.log"])
    with contextlib.redirect_stdout(io.StringIO()):
        check_shipped = shard.do_check(os.path.basename(EVIDENCE))
    ok("AC-BSGB6",
       refusals == 3 and code_path == 2 and check_shipped == 0
       and os.path.exists(EVIDENCE),
       "refusals=%d dry_rc=%d shipped_check=%d" % (refusals, code_path, check_shipped))

    # AC-BSGB7 - the repo is untouched and the tool reaches no network or shell.
    after_registry = stat_sig(REGISTRY)
    after_ledger = stat_sig(LEDGER)
    after_evidence = stat_sig(EVIDENCE)
    untouched = (sig_registry == after_registry and sig_ledger == after_ledger
                 and sig_evidence == after_evidence)
    banned = [n for n in ("import socket", "import urllib", "urllib.request",
                          "http.client", "import requests", "os.system",
                          "shell=True") if n in source]
    ok("AC-BSGB7", untouched and not banned,
       "untouched=%s banned=%d" % (untouched, len(banned)))

    # AC-BSGB13 - a declaration is graded OUTSIDE a leg: the sweep runs only the
    # suites that carry the declaration printer, so one that declares a count
    # the registry disagrees with is named without paying for a battery. Both
    # directions run here in a private world, and a suite with no printer is
    # proved absent from the selection rather than counted as agreeing.
    world = tempfile.mkdtemp(prefix="battery_shard_decl_")
    try:
        write_probes(world)
        saved = shard.registry
        patch_registry(shard, [("probe-decl-ok", "probe_decl_ok.py", 8),
                               ("probe-decl-bad", "probe_decl_bad.py", 8),
                               ("probe-bare", "probe_bare.py", 1)], world)
        try:
            code_decl, out_decl = run_cli(shard, ["--declared-only"])
        finally:
            shard.registry = saved
        carriers = re.search(r"carriers=(\d+)", out_decl)
        decl_rows = [l for l in out_decl.splitlines() if l.startswith("DECL row")]
        by_label = dict((l.split()[2], l) for l in decl_rows)
        ok("AC-BSGB13",
           code_decl == 1 and carriers and int(carriers.group(1)) == 2
           and "declared=8 registry=8 ok" in by_label.get("probe-decl-ok", "")
           and ("declared=7 registry=8 mismatch"
                in by_label.get("probe-decl-bad", ""))
           and "probe-bare" not in by_label,
           "rc=%d carriers=%s rows=%d"
           % (code_decl, carriers.group(1) if carriers else "-",
              len(decl_rows)))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # AC-BTG1..AC-BTG4 (R2865) - the LEG-LEVEL cap. Measured fact this exists
    # for: the deep os-probe-seam rows cost 160.1s and 257.3s INSIDE a 600s cap
    # (R2864), so a leg over them cannot fit a window while every row is allowed
    # the full battery budget. A leg cap may only LOWER the effective duration;
    # a slow row then reads as a NAMED timeout (rc=124) instead of leaving its
    # family unmeasured.
    world = tempfile.mkdtemp(prefix="battery_shard_cap_")
    try:
        write_probes(world)
        # AC-BTG1 - the cap bounds wall clock, and the marker names the cap in
        # force, not the battery's default.
        code_lc, out_lc, secs_lc = shard.run_one(
            world, "probe-slow", "probe_slow.py", 600, {}, 1)
        lc_named = "TIMEOUT suite exceeded the 1s per-suite cap" in out_lc
        ok("AC-BTG1", code_lc == 124 and lc_named and secs_lc < 5.0,
           "rc=%d named=%s elapsed=%.1fs" % (code_lc, lc_named, secs_lc))
        # AC-BTG2 - no raise: a leg cap above the registry cap leaves the
        # registry number in force, read off the header rather than asserted.
        dry_code, dry_out = run_cli(shard, ["--dry", "--match", "probe",
                                            "--cap", "3600"])
        header = [l for l in dry_out.splitlines()
                  if l.startswith("SHARD scope=SHARD")]
        effective = -1
        if header:
            for piece in header[0].split():
                if piece.startswith("leg_cap="):
                    effective = int(piece.split("=", 1)[1].rstrip("s"))
        raised = dry_out.count("leg_cap=3600")
        ok("AC-BTG2", dry_code == 0 and effective == 600 and raised == 0,
           "effective=%d raised=%d" % (effective, raised))
        # AC-BTG3 - a per-label override is clamped by the leg cap, never
        # allowed to spend more than the leg means to spend.
        code_ov, out_ov, _ = shard.run_one(
            world, "probe-slow", "probe_slow.py", 600, {"probe-slow": 900}, 1)
        ov_clamped = ("TIMEOUT suite exceeded the 1s per-suite cap" in out_ov
                      and "900s" not in out_ov)
        ok("AC-BTG3", code_ov == 124 and ov_clamped,
           "rc=%d clamp_kept=%s" % (code_ov, ov_clamped))
        # AC-BTG4 - a timeout is RED in the leg and named, and it is never
        # counted green: one good row + one timed-out row reads green=1 of 2.
        patch_registry(shard, [("probe-good", "probe_good.py", 1),
                               ("probe-slow", "probe_slow.py", 1)], world)
        code_cap, out_cap = run_cli(shard, ["--match", "probe", "--cap", "1"])
        slow_row = [l for l in out_cap.splitlines()
                    if l.startswith("SHARD row ") and " probe-slow " in l]
        closing_cap = [l for l in out_cap.splitlines()
                       if l.startswith("SHARD rc=")]
        red_named = "probe-slow:rc=124" in out_cap
        cap_ok = (code_cap == 2 and red_named
                  and bool(slow_row) and "timeout=yes" in slow_row[0]
                  and bool(closing_cap) and "green=1" in closing_cap[0]
                  and "executed=2" in closing_cap[0])
        ok("AC-BTG4", cap_ok,
           "rc=%d named=%s row=%s" % (code_cap, red_named,
                                      "timeout=yes" in slow_row[0]
                                      if slow_row else "-"))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # AC-BSGB14 (R2881) - a unit disagreement is a RED in every mode. Measured
    # fact this exists for: the shard left rc untouched when a suite printed 21
    # assertions beside a registry row of 8 criteria, so the same thirteen
    # labels read as "carried debt" for twenty-three windows while every one of
    # them already declared the right number (R2881 measured all thirteen green
    # in qa/critunits-measure-R2881.log, and the pre-fix tool read the defect as
    # rc=0 in qa/red-first-unitlaw-R2881.log). --declared-only already reddened
    # the condition; the shard now asks it the same way. Both directions run
    # here in ONE private world, so the gate is proved to bite and proved not to
    # bite the lawful case instead of being assumed either way.
    world = tempfile.mkdtemp(prefix="battery_shard_unit_")
    try:
        for name, body in (("probe_unit_bare.py", PROBE_UNIT_BARE),
                           ("probe_unit_decl.py", PROBE_UNIT_DECL)):
            with open(os.path.join(world, name), "w", encoding="utf-8",
                      newline="\n") as handle:
                handle.write(body)
        saved = shard.registry
        try:
            patch_registry(shard, [("probe-unit-bare", "probe_unit_bare.py", 8),
                                   ("probe-unit-decl", "probe_unit_decl.py", 8)],
                           world)
            code_all, out_all = run_cli(shard, ["--match", "probe"])
            patch_registry(shard, [("probe-unit-decl", "probe_unit_decl.py", 8)],
                           world)
            code_decl, out_declared = run_cli(shard, ["--match", "probe"])
        finally:
            shard.registry = saved
        bare_named = ("SHARD red-unit undeclared=probe-unit-bare:21!=8"
                      in out_all)
        lawful_kept = code_decl == 0 and "crit_mismatch=0" in out_declared
        ok("AC-BSGB14", code_all == 2 and bare_named and lawful_kept,
           "rc=%d bare_named=%s declared_rc=%d" % (code_all, bare_named,
                                                   code_decl))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    acs = sorted({m.group(0) for m in
                  (re.match(r"AC-[A-Z]+[0-9]*", str(c)) for c in CHECKS) if m})
    print("suite: %d assertions over %d criteria" % (total, len(acs)))
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
