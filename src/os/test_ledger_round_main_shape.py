"""round main line shape suite (R2832; criteria AC-RMS1..AC-RMS6 were
pinned in the R2832 row of src/os/backlog.md BEFORE this file existed -
commit of the pin row precedes the commit of this code).

What this proves: the export window hangs on the max ^YYYY-MM-DD prefix of
the live log, and R2828/R2829/R2830 wrote their round main lines as
"R28xx ...". Nothing asked that shape before a line landed, so the only
detector was a ValueError raised at READ time - and it detected by
crashing, which reddened three queue-face suites with a traceback instead
of a verdict (measured at R2831: 14 live lines, zero anchored).

Three laws, all fail-closed, none of them a crash:
  - the newest round narrative must carry at least one dated main line
    (a round's later lines - disclosures, group scans, notes - carry no
    date of their own and belong to the main line they follow);
  - that dated main line must carry an UPPERCASE label after the round
    number, because both CEO-face readers require one and a line they skip
    publishes the PREVIOUS round while every check reads PASS (R2864);
  - a window with no round narrative at all cannot anchor anything.

Stdlib only, ASCII source, zero network, no clock, no writes.
Exit 0 = all green.
"""

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

EXPECTED_CRITERIA = 9
MODULE = os.path.join(BASE, "ledger_lines.py")
CONSISTENCY = os.path.join(BASE, "check_export_consistency.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
STATE = os.path.join(BASE, "state.json")
APPEND = os.path.join(BASE, "state_append.py")
TOOLS = os.path.join(os.path.dirname(SRC), "tools")
LABEL = "os-ledger-round-main-shape"

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


def write_state(path, items):
    body = ",\n".join(" " * 8 + json.dumps(i, ensure_ascii=True)
                      for i in items)
    text = '{\n  "tick": 1,\n  "log": [\n' + body + "\n  ]\n}\n"
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


def run_cli(argv):
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with contextlib.redirect_stderr(err):
            code = LL.main(argv)
    return code, buf.getvalue(), err.getvalue()


def _load(name, path):
    """Load one shipped module by path (the readers are not on this sys.path)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sxf():
    return _load("sxf_rms", os.path.join(TOOLS, "status_export_fresh.py"))


def load_export_round():
    return _load("er_rms", os.path.join(BASE, "export_round.py"))


def ac_rms1():
    """AC-RMS1: the library asks the law of the newest round, both ways."""
    dated = [
        "2026-11-16 R2831 PRODUCT: the owed leg is measured green",
        "R2831 tokens: local=~38k api=0 api_reason=a closed round line",
    ]
    ok_report = LL.check_round_main_shape(dated)
    bare = [
        "R2832 PRODUCT: a main line written without its factual date",
        "R2832 tokens: local=~1k api=0 api_reason=an unanchored round",
    ]
    bad_report = LL.check_round_main_shape(bare)
    ok = (ok_report["ok"] is True
          and ok_report["round"] == 2831
          and bad_report["ok"] is False
          and bad_report["code"] == "E_RMS_NO_DATE"
          and bad_report["round"] == 2832
          and bad_report["sample"].startswith("R2832 PRODUCT"))
    if not ok:
        print("  measured: ok_report=%r bad_report=%r"
              % (ok_report, bad_report), flush=True)
    check(ok, "AC-RMS1 dated newest round passes, an undated main line is "
          "refused by name with its round and a sample")


def ac_rms2():
    """AC-RMS2: newest is the highest round number, never the last line.

    A dated older round must not mask an undated newer one; and an undated
    SUB-line of the newest round must not redden a healthy tree, because
    the law asks the round for one dated main line, not for every line.
    """
    ordered = [
        "2026-11-16 R2830 PRODUCT: an old, dated main line",
        "R2831 PRODUCT: the newer round forgot its prefix entirely",
    ]
    masked = LL.check_round_main_shape(ordered)
    healthy = [
        "2026-11-16 R2831 PRODUCT: the round main line carries its date",
        "R2831 honest disclosures: a sub-line of the same round, no date",
        "R2831 tokens: local=~38k api=0 api_reason=a closed round line",
    ]
    fine = LL.check_round_main_shape(healthy)
    ok = (masked["ok"] is False
          and masked["code"] == "E_RMS_NO_DATE"
          and masked["round"] == 2831
          and fine["ok"] is True
          and fine["round"] == 2831)
    if not ok:
        print("  measured: masked=%r fine=%r" % (masked, fine), flush=True)
    check(ok, "AC-RMS2 highest round wins over position, and an undated "
          "sub-line of that round does not redden a healthy tree")


def ac_rms3():
    """AC-RMS3: ledger lines and every fold-summary form are never mains."""
    forms = [
        "R2831 tokens: local=~1k api=0 api_reason=a ledger line",
        "R2568 fold of log lines 1..20 into the month archive",
        "2026-11-08 R2568 fold of log lines 1..20 into the archive",
        "R2568 folded the block into the archive",
        "R2568 folds the block into the archive",
        "R2568 Fold of log lines 1..20 into the archive",
    ]
    reports = [LL.check_round_main_shape([line]) for line in forms]
    all_no_round = all(r["code"] == "E_RMS_NO_ROUND" and not r["ok"]
                       for r in reports)
    kinds = dict((line[:20], LL.classify(line)) for line in forms)
    no_round_kind = all(kind != "round" for kind in kinds.values())
    empty = LL.check_round_main_shape([])
    ok = (all_no_round and no_round_kind
          and empty["code"] == "E_RMS_NO_ROUND"
          and empty["round"] is None)
    if not ok:
        print("  measured: reports=%r kinds=%r empty=%r"
              % ([r["code"] for r in reports], kinds, empty), flush=True)
    check(ok, "AC-RMS3 ledger lines and four fold-summary forms never count "
          "as a round main, and an empty window fails closed")


def ac_rms4():
    """AC-RMS4: the shipped CLI gate, on the real tree and in a private world."""
    code_ok, out_ok, _ = run_cli(["--round-main", "--check"])
    lines_ok = [ln for ln in out_ok.splitlines() if ln.strip()]
    parsed = None
    try:
        parsed = LL.parse_round_main_line(lines_ok[0]) if lines_ok else None
    except LL.LedgerLineError:
        parsed = None
    tick = json.loads(io.open(STATE, encoding="utf-8").read())["tick"]
    private_dir = tempfile.mkdtemp(prefix="rms4-")
    try:
        target = write_state(os.path.join(private_dir, "state.json"), [
            "2026-11-15 R9001 PRODUCT: a dated older round",
            "R9002 PRODUCT: the newest main line lost its prefix",
            "R9002 tokens: local=~1k api=0 api_reason=a closed round line",
        ])
        code_bad, out_bad, err_bad = run_cli(["--round-main", "--check",
                                              target])
        lines_bad = [ln for ln in out_bad.splitlines() if ln.strip()]
        parsed_bad = None
        try:
            parsed_bad = (LL.parse_round_main_line(lines_bad[0])
                          if lines_bad else None)
        except LL.LedgerLineError:
            parsed_bad = None
        missing = os.path.join(private_dir, "absent.json")
        code_missing, _, _ = run_cli(["--round-main", "--check", missing])
    finally:
        for name in os.listdir(private_dir):
            os.remove(os.path.join(private_dir, name))
        os.rmdir(private_dir)
    ok = (code_ok == 0 and len(lines_ok) == 1
          and parsed is not None and parsed["ok"] is True
          and parsed["round"] == int(tick)
          and code_bad == 2 and len(lines_bad) == 1
          and parsed_bad is not None and parsed_bad["ok"] is False
          and parsed_bad["code"] == "E_RMS_NO_DATE"
          and parsed_bad["round"] == 9002
          and "E_RMS_NO_DATE" in err_bad
          and code_missing == 3)
    if not ok:
        print("  measured: ok=%r/%r/%r bad=%r/%r missing=%r"
              % (code_ok, lines_ok, parsed, code_bad, lines_bad,
                 code_missing), flush=True)
    check(ok, "AC-RMS4 CLI reads exactly one line on the real tree (rc=0), "
          "names E_RMS_NO_DATE in a private world (rc=2), rc=3 when absent")


def ac_rms5():
    """AC-RMS5: an unanchored log is a stated code, not a bare ValueError."""
    typed = issubclass(CEC.AnchorError, ValueError)
    sample_round, sample_text = CEC._newest_round_sample([
        "2026-11-15 R9001 PRODUCT: a dated older round",
        "R9002 PRODUCT: the newest main line lost its prefix",
        "R9002 tokens: local=~1k api=0 api_reason=a closed round line",
    ])
    source = io.open(CONSISTENCY, encoding="utf-8").read()
    bare_gone = 'raise ValueError("no date prefixes' not in source
    original = CEC.recompute

    def boom():
        raise CEC.AnchorError("E_EC_NO_DATE_ANCHOR",
                              "the live log holds 2 line(s) and none carries "
                              "a YYYY-MM-DD prefix")

    CEC.recompute = boom
    try:
        lines, n_pass, n_fail = CEC.check()
    finally:
        CEC.recompute = original
    fail_row = [ln for ln in lines if ln.startswith("FAIL anchor ")]
    ok = (typed and sample_round == 9002
          and sample_text.startswith("R9002 PRODUCT")
          and bare_gone
          and n_fail == 1 and fail_row
          and "E_EC_NO_DATE_ANCHOR" in fail_row[0])
    if not ok:
        print("  measured: typed=%r sample=%r/%r bare_gone=%r fail=%r/%r"
              % (typed, sample_round, sample_text, bare_gone, n_fail,
                 fail_row), flush=True)
    check(ok, "AC-RMS5 AnchorError is typed and carries a code, the newest "
          "round is sampled, and check() turns it into one FAIL row")


def ac_rms6():
    """AC-RMS6: read-only, stdlib only, and registered with this count."""
    with io.open(STATE, "rb") as handle:
        before = handle.read()
    stat_before = os.stat(STATE)
    run_cli(["--round-main", "--check"])
    with io.open(STATE, "rb") as handle:
        after = handle.read()
    stat_after = os.stat(STATE)
    untouched = (before == after
                 and stat_before.st_size == stat_after.st_size
                 and stat_before.st_mtime_ns == stat_after.st_mtime_ns)
    source = io.open(MODULE, "rb").read()
    ascii_only = all(byte < 128 for byte in source)
    roots = set()
    for line in source.decode("ascii", "replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            roots.add(stripped[len("import "):].split(",")[0].split(" ")[0]
                      .split(".")[0])
        elif stripped.startswith("from ") and " import " in stripped:
            roots.add(stripped[len("from "):].split(" ")[0].split(".")[0])
    no_net = not (roots & set(NET_IMPORTS))
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    registered = match is not None
    declared = int(match.group(1)) if registered else -1
    ok = (untouched and ascii_only and no_net
          and registered and declared == EXPECTED_CRITERIA)
    if not ok:
        print("  measured: untouched=%r ascii=%r net=%r registered=%r "
              "declared=%r expected=%r"
              % (untouched, ascii_only, sorted(roots), registered, declared,
                 EXPECTED_CRITERIA), flush=True)
    check(ok, "AC-RMS6 the gate writes zero bytes, the library is ASCII with "
          "no net, and the registry declares this suite at %d criteria"
          % EXPECTED_CRITERIA)


def ac_rms7():
    """AC-RMS7: the write/read disagreement is MEASURED, and the gate is the fix.

    The R2864 defect, reproduced in one private fixture: the gate used to accept
    a dated main line whose label is lowercase, while the CEO-face reader that
    publishes the headline skipped it and returned the PREVIOUS round - a face
    naming last window with every check green. Both sides are read in the same
    assertion so the coupling is proved rather than described.
    """
    log = [
        "2026-11-17 R9001 PRODUCT: an older round whose label is accepted",
        "2026-11-17 R9002 law_status: the newest round lost its label",
        "R9002 tokens: local=~1k api=0 api_reason=a closed round line",
    ]
    report = LL.check_round_main_shape(log)
    sxf = load_sxf()
    seen_round, seen_line = sxf.newest_round({"log": log})
    fixed = list(log)
    fixed[1] = ("2026-11-17 R9002 PRODUCT+ENGINEERING: the newest round "
                "declares its kind")
    fixed_report = LL.check_round_main_shape(fixed)
    fixed_round, _ = sxf.newest_round({"log": fixed})
    ok = (report["ok"] is False
          and report["code"] == "E_RMS_NO_LABEL"
          and report["round"] == 9002
          and report["sample"].startswith("2026-11-17 R9002 law_status")
          and seen_round == 9001
          and seen_line.startswith("2026-11-17 R9001 PRODUCT")
          and fixed_report["ok"] is True
          and fixed_round == 9002)
    if not ok:
        print("  measured: report=%r seen=%r/%r fixed=%r/%r"
              % (report, seen_round, seen_line, fixed_report["ok"],
                 fixed_round), flush=True)
    check(ok, "AC-RMS7 a lowercase-label newest round is refused by name "
          "E_RMS_NO_LABEL while the reader behind it would have published the "
          "OLDER round 9001, and the same line with a label passes both")


def ac_rms8():
    """AC-RMS8: one law, three readers, six label shapes."""
    er = load_export_round()
    sxf = load_sxf()
    src = LL.ROUND_LABEL_SRC
    in_er = src in er.ROUND_HEAD_RE.pattern
    in_sxf = src in sxf.HEADLINE_RE.pattern
    shapes = [
        ("2026-11-17 R9002 PRODUCT: x", True),
        ("2026-11-17 R9002 law_status: x", False),
        ("2026-11-17 R9002 Product: x", False),
        ("2026-11-17 R9002 A1: x", False),
        ("2026-11-17 R9002 ABC: x", True),
        ("2026-11-17 R9002 PRODUCT+ENGINEERING: x", True),
    ]
    rows = []
    agree = True
    for line, want in shapes:
        gate = bool(LL.ROUND_LABEL_RE.match(line))
        head = bool(er.ROUND_HEAD_RE.match(line))
        face = bool(sxf.HEADLINE_RE.match(line))
        rows.append((line[24:], gate, head, face, want))
        agree = agree and gate == head == face == want
    ok = in_er and in_sxf and agree
    if not ok:
        print("  measured: in_er=%r in_sxf=%r rows=%r"
              % (in_er, in_sxf, rows), flush=True)
    check(ok, "AC-RMS8 ROUND_LABEL_SRC is the only definition - both readers "
          "carry it verbatim and all three agree on six label shapes")


def ac_rms9():
    """AC-RMS9: the live tree still passes, the vehicle refuses at birth, and
    the registry declares this suite at nine criteria."""
    live = json.loads(io.open(STATE, encoding="utf-8").read())
    report = LL.check_round_main_shape(live.get("log") or [])
    private_dir = tempfile.mkdtemp(prefix="rms9-")
    copy = os.path.join(private_dir, "state.json")
    shutil.copyfile(STATE, copy)
    try:
        bad = subprocess.run(
            [sys.executable, APPEND, "--state", copy, "--check",
             "--round", "9002",
             "--line", "2026-11-17 R9002 law_status: born with no label"],
            capture_output=True, text=True, timeout=120)
        # the same bytes, one label added: the vehicle accepts it unread
        good = subprocess.run(
            [sys.executable, APPEND, "--state", copy, "--check",
             "--round", "9003",
             "--line", "2026-11-17 R9003 PRODUCT: born with its label"],
            capture_output=True, text=True, timeout=120)
        untouched = io.open(copy, "rb").read() == io.open(STATE, "rb").read()
    finally:
        shutil.rmtree(private_dir, ignore_errors=True)
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    declared = int(match.group(1)) if match else -1
    ok = (report["ok"] is True
          and bad.returncode == 2
          and "E_RMS_NO_LABEL" in (bad.stdout + bad.stderr)
          and good.returncode == 0
          and untouched
          and declared == EXPECTED_CRITERIA)
    if not ok:
        print("  measured: live=%r bad=%r/%r good=%r untouched=%r declared=%r"
              % (report, bad.returncode, (bad.stdout + bad.stderr)[:160],
                 good.returncode, untouched, declared), flush=True)
    check(ok, "AC-RMS9 the live tree passes, the shipped vehicle refuses a "
          "label-less line at rc=2 with E_RMS_NO_LABEL and accepts the "
          "labelled one without writing, registry declares %d"
          % EXPECTED_CRITERIA)


def main():
    print("round main line shape suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rms1()
    ac_rms2()
    ac_rms3()
    ac_rms4()
    ac_rms5()
    ac_rms6()
    ac_rms7()
    ac_rms8()
    ac_rms9()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
