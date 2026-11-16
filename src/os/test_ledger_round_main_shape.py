"""round main line shape suite (R2832; criteria AC-RMS1..AC-RMS6 were
pinned in the R2832 row of src/os/backlog.md BEFORE this file existed -
commit of the pin row precedes the commit of this code).

What this proves: the export window hangs on the max ^YYYY-MM-DD prefix of
the live log, and R2828/R2829/R2830 wrote their round main lines as
"R28xx ...". Nothing asked that shape before a line landed, so the only
detector was a ValueError raised at READ time - and it detected by
crashing, which reddened three queue-face suites with a traceback instead
of a verdict (measured at R2831: 14 live lines, zero anchored).

Two laws, both fail-closed, neither of them a crash:
  - the newest round narrative must carry at least one dated main line
    (a round's later lines - disclosures, group scans, notes - carry no
    date of their own and belong to the main line they follow);
  - a window with no round narrative at all cannot anchor anything.

Stdlib only, ASCII source, zero network, no clock, no writes.
Exit 0 = all green.
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "ledger_lines.py")
CONSISTENCY = os.path.join(BASE, "check_export_consistency.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
STATE = os.path.join(BASE, "state.json")
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


def main():
    print("round main line shape suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rms1()
    ac_rms2()
    ac_rms3()
    ac_rms4()
    ac_rms5()
    ac_rms6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
