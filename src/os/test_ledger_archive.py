"""Archive-aware ledger coverage suite (R2224; criteria AC-LGA1..AC-LGA8
were pre-registered in state/queue/tech.md BEFORE this code existed -
honesty law).

What this proves: R2223 measured that the 78500B waterline gate and the
"at least 30 ledger and 30 round lines in the LIVE state.json log" law
are mutually unsatisfiable at current line sizes, so a fold can never
land. The fix is the audit scope, not a bigger window: counts come from
the union of the live window and the folded archive sections, while the
actionable drift set stays LIVE-only because an archive is frozen
history no later round may rewrite.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "ledger_lines.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
STATE = os.path.join(BASE, "state.json")
LABEL = "os-ledger-archive"

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


def ledger(round_no, reason="fixture round reason text"):
    return "R%d tokens: local=1k api=0 api_reason=%s" % (round_no, reason)


def narrative(round_no):
    return "R%d fixture narrative line for the round" % round_no


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_bytes(path, data):
    with io.open(path, "wb") as handle:
        handle.write(data)


def run_cli(args):
    proc = subprocess.Popen(
        [sys.executable, MODULE] + args,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode,
            out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def error_code(call):
    """Return the LedgerLineError code a callable raises, or 'NONE'."""
    try:
        call()
    except LL.LedgerLineError as exc:
        return exc.code
    return "NONE"


def archive_block(rounds):
    """A fold section: header comments, a window marker, then pairs."""
    out = ["# state-log-archive fixture header line",
           "# --- R%d fold append (fixture window marker)" % rounds[0],
           ""]
    for round_no in rounds:
        out.append(narrative(round_no))
        out.append(ledger(round_no))
    return "\n".join(out) + "\n"


def build_world(root):
    """Two archive sections plus the live log, on a temp logs dir."""
    logs = os.path.join(root, "logs")
    os.makedirs(logs)
    early = os.path.join(logs, "state-log-archive-2026-08.md")
    late = os.path.join(logs, "state-log-archive-2026-09.md")
    write_text(early, archive_block([1001, 1002, 1003]))
    write_text(late, archive_block([1004, 1005]))
    live = [narrative(1006), ledger(1006)]
    return logs, early, late, live


def run():
    world = tempfile.mkdtemp(prefix="ledger-archive-")
    try:
        logs, early, late, live = build_world(world)

        # AC-LGA1: archive reading keeps log lines only, in order, and
        # never rewrites the file it read.
        before = [(os.path.getsize(early), os.path.getmtime(early)),
                  (os.path.getsize(late), os.path.getmtime(late))]
        files = LL.archive_files(logs)
        lines = LL.load_archive(early)
        all_lines = LL.load_archive_lines(logs)
        after = [(os.path.getsize(early), os.path.getmtime(early)),
                 (os.path.getsize(late), os.path.getmtime(late))]
        check([os.path.basename(p) for p in files]
              == ["state-log-archive-2026-08.md",
                  "state-log-archive-2026-09.md"]
              and lines == [narrative(1001), ledger(1001),
                            narrative(1002), ledger(1002),
                            narrative(1003), ledger(1003)]
              and all_lines == lines + LL.load_archive(late)
              and all(not item.startswith("#") for item in all_lines)
              and all(item.strip() for item in all_lines)
              and before == after,
              "AC-LGA1 archive loader keeps log lines in order, drops "
              "markers, rewrites nothing")

        # AC-LGA2: the union satisfies the floor the live array cannot.
        big = os.path.join(world, "logs-big")
        os.makedirs(big)
        blocker = os.path.join(big, "state-log-archive-2026-10.md")
        rounds = list(range(3001, 3041))
        write_text(blocker, archive_block(rounds))
        small_live = [narrative(4001), ledger(4001)]
        live_only = LL.audit(small_live)
        scoped = LL.audit_scope(LL.load_archive_lines(big), small_live)
        check(LL.coverage_floor(live_only) is False
              and LL.coverage_floor(scoped) is True
              and scoped["scope"] == "live+archive"
              and scoped["archive_ledger_lines"] == 40
              and scoped["archive_round_lines"] == 40
              and scoped["ledger_lines"] == 41
              and scoped["round_lines"] == 41
              and scoped["live_ledger_lines"] == 1
              and scoped["total_lines"] == 82
              and scoped["clean"] is True,
              "AC-LGA2 union floor passes where the live-only floor fails")

        # AC-LGA3: live drift stays authoritative - an archive never
        # masks a bad form or a new gap that the live window carries.
        drifted = [narrative(5001), "R5001 token: local=1k api=0 "
                                     "api_reason=typo prefix round",
                   narrative(5002)]
        drifted_report = LL.audit_scope(LL.load_archive_lines(big), drifted)
        gated = LL.apply_baseline(drifted_report, {"missing": [], "orphan": []})
        clean_gate = LL.apply_baseline(scoped, {"missing": [], "orphan": []})
        check(drifted_report["errors"] == []
              and drifted_report["rounds_without_ledger"] == [5001, 5002]
              and gated["new_missing"] == [5001, 5002]
              and gated["clean"] is False
              and clean_gate["clean"] is True
              and LL.coverage_floor(drifted_report) is True,
              "AC-LGA3 live drift still gates even with a full archive")

        # AC-LGA4: an archived gap is a frozen fact, reported but never
        # actionable and never needing a baseline entry.
        gap = os.path.join(world, "logs-gap")
        os.makedirs(gap)
        write_text(os.path.join(gap, "state-log-archive-2026-07.md"),
                   "# header\n" + narrative(2002) + "\n"
                   + ledger(2003) + "\n" + narrative(2004) + "\n"
                   + ledger(2004) + "\n")
        gap_report = LL.audit_scope(LL.load_archive_lines(gap), small_live)
        gap_gated = LL.apply_baseline(gap_report,
                                     {"missing": [], "orphan": []})
        check(gap_report["archived_missing"] == [2002]
              and gap_report["archived_orphan"] == [2003]
              and gap_report["rounds_without_ledger"] == []
              and gap_report["ledger_without_round"] == []
              and gap_report["clean"] is True
              and gap_gated["new_missing"] == []
              and gap_gated["stale_missing"] == []
              and gap_gated["clean"] is True,
              "AC-LGA4 archived gaps are informational, never gated")

        # AC-LGA5: tail cuts the live window and never the union counts.
        long_live = []
        for round_no in range(6001, 6011):
            long_live.append(narrative(round_no))
            long_live.append(ledger(round_no))
        archive_lines = LL.load_archive_lines(big)
        full = LL.audit_scope(archive_lines, long_live)
        tailed = LL.audit_scope(archive_lines, long_live, tail=2)
        check(tailed["tail"] == 2
              and tailed["window_lines"] == 2
              and tailed["live_lines"] == 20
              and tailed["ledger_lines"] == full["ledger_lines"] == 50
              and tailed["round_lines"] == full["round_lines"] == 50
              and tailed["archive_lines"] == full["archive_lines"] == 80
              and full["window_lines"] == 20,
              "AC-LGA5 tail scopes the live window only")

        # AC-LGA6: bad archive inputs fail closed instead of reading as
        # an empty scope, and the CLI refuses a missing argument.
        missing_dir = os.path.join(world, "no-such-dir")
        bad = os.path.join(world, "logs-bad")
        os.makedirs(bad)
        write_bytes(os.path.join(bad, "state-log-archive-2026-06.md"),
                    b"# header\n\xff\xfe not utf-8\n")
        state_path = os.path.join(world, "state.json")
        write_text(state_path, json.dumps({"log": small_live}))
        rc_noarg, out_noarg, _ = run_cli([state_path, "--archives"])
        rc_missing, out_missing, err_missing = run_cli(
            [state_path, "--archives", missing_dir])
        rc_bad, out_bad, _ = run_cli([state_path, "--archives", bad])
        check(error_code(lambda: LL.archive_files(missing_dir))
              == "E_LGR_BAD_ARCHIVE"
              and error_code(lambda: LL.load_archive(
                  os.path.join(bad, "state-log-archive-2026-06.md")))
              == "E_LGR_BAD_ARCHIVE"
              and rc_noarg == 2 and out_noarg == ""
              and rc_missing == 3 and out_missing == ""
              and "E_LGR_BAD_ARCHIVE" in err_missing
              and rc_bad == 3 and out_bad == "",
              "AC-LGA6 bad archive input fails closed with zero stdout")

        # AC-LGA7: the default face stays byte-identical, and --archives
        # only inserts one scope line into the existing report.
        rc_def, out_def, _ = run_cli(["--check", STATE])
        rc_arc, out_arc, _ = run_cli(["--check", STATE, "--archives",
                                      LL.default_logs_dir(STATE)])
        live_log = LL.load_state_log(STATE)
        plain = "\n".join(LL.format_report(
            LL.apply_baseline(LL.audit(live_log),
                              LL.load_baseline(LL.default_baseline_path()))))
        scoped_real = LL.apply_baseline(
            LL.audit_scope(LL.load_archive_lines(None, STATE), live_log),
            LL.load_baseline(LL.default_baseline_path()))
        expected = "\n".join(LL.format_report(scoped_real))
        default_lines = out_def.splitlines()
        scoped_lines = out_arc.splitlines()
        counts = ("lines:", "kinds:", "scope: ")

        def authority(lines):
            return [line for line in lines
                    if not line.startswith(counts)]

        check(out_def.splitlines() == plain.splitlines()
              and "scope" not in LL.audit(live_log)
              and rc_arc == rc_def == 0
              and scoped_lines == expected.splitlines()
              and len([line for line in scoped_lines
                       if line.startswith("scope: ")]) == 1
              and authority(scoped_lines) == authority(default_lines)
              and scoped_lines[-1] == default_lines[-1] == "VERDICT CLEAN",
              "AC-LGA7 default face byte-identical, only the counts block "
              "and one scope line differ")

        # AC-LGA8: the real tree gate plus hygiene.
        with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
            source = handle.read()
        net = LL.network_imports(source)
        with io.open(RUNNER, "r", encoding="utf-8") as handle:
            runner_src = handle.read()
        real = LL.apply_baseline(scoped_real,
                                 LL.load_baseline(
                                     LL.default_baseline_path()))
        check(real["errors"] == []
              and LL.coverage_floor(real) is True
              and real["ledger_lines"] >= 30 and real["round_lines"] >= 30
              and real["live_lines"] > 0 and real["archive_lines"] > 0
              and real["archived_missing"] != []
              and real["new_missing"] == [] and real["new_orphan"] == []
              and real["clean"] is True
              and not net and LABEL in runner_src
              and EXPECTED_CRITERIA == 8,
              "AC-LGA8 real tree floor met on the union, drift clean, "
              "hygiene")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("suite: archive-aware ledger coverage (R2224 AC-LGA1..AC-LGA8)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())