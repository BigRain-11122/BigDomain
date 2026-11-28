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

EXPECTED_CRITERIA = 16
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
        # only inserts the counts block plus the two scope readings.
        # R3087: the allowed-difference set gained 'archive_payload:' when
        # AC-LGA12 published the payload reading - JUDGED CHANGE, not a
        # deletion: the law ("only counts and scope lines may differ, and
        # the verdict line must still be the last one") is unchanged, and
        # the arm now also pins that exactly ONE payload line is printed.
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
        counts = ("lines:", "kinds:", "scope: ", "archive_payload: ")

        def authority(lines):
            return [line for line in lines
                    if not line.startswith(counts)]

        check(out_def.splitlines() == plain.splitlines()
              and "scope" not in LL.audit(live_log)
              and rc_arc == rc_def == 0
              and scoped_lines == expected.splitlines()
              and len([line for line in scoped_lines
                       if line.startswith("scope: ")]) == 1
              and len([line for line in scoped_lines
                       if line.startswith("archive_payload: ")]) == 1
              and authority(scoped_lines) == authority(default_lines)
              and scoped_lines[-1] == default_lines[-1] == "VERDICT CLEAN",
              "AC-LGA7 default face byte-identical, only the counts block "
              "and the two scope lines differ")

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
              and not net and LABEL in runner_src,
              "AC-LGA8 real tree floor met on the union, drift clean, "
              "hygiene")

        # AC-LGA9 (R2914): the fold-carry law is SCOPED to windows opened
        # at or after the pin, and the shape it reddens is the R2905 one -
        # a narrative archived while its ledger line was left behind.
        carry = os.path.join(world, "logs-carry")
        os.makedirs(carry)
        carried = os.path.join(carry, "state-log-archive-2026-11.md")
        write_text(carried, archive_block([5001, 5002]))
        good = LL.audit_fold_carry([carried], 5000)
        write_text(carried, "# fixture header\n"
                            "# --- R5003 fold append (fixture)\n"
                            + narrative(5003) + "\n"
                            + ledger(5004) + "\n")
        bad = LL.audit_fold_carry([carried], 5000)
        # AC-LGA9 arm f (R3090): the red line publishes the archive's own
        # coordinates, and every published position opens to a real marker.
        bad_line = LL.format_fold_carry(bad)
        bad_gap = bad["gaps"][0]
        with io.open(carried, "r", encoding="utf-8") as handle:
            bad_head = handle.read().split("\n")[bad_gap["line"] - 1]
        locator_open = bad_head.startswith("# --- R%d" % bad_gap["window"])
        write_text(carried, archive_block([4998, 4999]))
        pre_pin = LL.audit_fold_carry([carried], 5000)
        write_text(carried, archive_block([5001, 5002]))
        rc_ok, out_ok, _ = run_cli([state_path, "--check", "--archives", carry,
                                    "--fold-carry", "--since", "5000"])
        write_text(carried, "# fixture header\n"
                            "# --- R5003 fold append (fixture)\n"
                            + narrative(5003) + "\n")
        rc_red, out_red, _ = run_cli([state_path, "--check", "--archives",
                                      carry, "--fold-carry", "--since", "5000"])
        rc_noarch, out_noarch, err_noarch = run_cli(
            [state_path, "--check", "--fold-carry", "--since", "5000"])
        real_carry = LL.audit_fold_carry(LL.archive_files(
            LL.default_logs_dir(STATE)),
            live_lines=LL.load_state_log(STATE))
        check(LL.FOLD_CARRY_PIN == 2914
              and good["clean"] is True and good["vacuous"] is False
              and good["windows"] == 1 and good["rounds"] == 2
              and good["gaps"] == [] and good["skipped_windows"] == 0
              and bad["clean"] is False and bad["vacuous"] is False
              and [(item["round"], item["window"])
                   for item in bad["gaps"]] == [(5003, 5003)]
              and pre_pin["clean"] is True and pre_pin["vacuous"] is True
              and pre_pin["windows"] == 0 and pre_pin["skipped_windows"] == 1
              and LL.format_fold_carry(pre_pin) ==
              ("FOLD-CARRY VACUOUS since=5000 windows=0 skipped=1 "
               "(no window opened at or after the pin yet) dup=0 "
               "loc=file@line")
              and LL.format_fold_carry(good) ==
              ("FOLD-CARRY OK since=5000 windows=1 rounds=2 skipped=0 "
               "split=0 same_window=0 dup=0 loc=file@line")
              and "@state-log-archive-2026-11.md:1:2" in bad_line
              and locator_open is True
              and bad_line.isascii()
              and "E_LFC_CARRY" in bad_line
              and rc_ok == 0 and out_ok.startswith("FOLD-CARRY OK")
              and rc_red == 2 and "E_LFC_CARRY" in out_red
              and "R5003" in out_red
              and rc_noarch == 2 and out_noarch == ""
              and "E_LGR_BAD_ARGS" in err_noarch
              and error_code(lambda: LL.audit_fold_carry([carried], 0))
              == "E_LGR_BAD_ARGS"
              and real_carry["clean"] is True
              and real_carry["vacuous"] is False
              and real_carry["windows"] >= 1
              and real_carry["skipped_windows"] >= 1,
              "AC-LGA9 fold-carried ledger pairing is scoped to post-pin "
              "windows, reddens the left-behind shape, and is measured "
              "non-vacuous on the shipped tree")

        # AC-LGA10 (R3084): PRESENCE and SHAPE are two laws. The shape law
        # (LEDGER_PREFIX_RE, parse_ledger_line, the write door) refuses a
        # dated ledger line at birth; the presence law asks only whether a
        # pairing survived a fold, and the history holds 786 dated lines
        # written before that door existed. Reading presence through the
        # shape regex made one of them invisible and reported a pairing
        # that had survived as lost (measured: R2980, window 2987).
        presence_dir = os.path.join(world, "logs-presence")
        os.makedirs(presence_dir)
        dated_path = os.path.join(presence_dir,
                                  "state-log-archive-2026-11.md")
        dated_line = ("2026-11-19 R5003 tokens: local=1k api=0 "
                      "api_reason=dated ledger line written before the door")
        write_text(dated_path,
                   "# fixture header\n"
                   "# --- R5003 fold append (fixture)\n"
                   "2026-11-19 R5003 fixture narrative line\n"
                   + dated_line + "\n")
        closed = LL.audit_fold_carry([dated_path], 5000)
        rc_dat, out_dat, _ = run_cli(
            [state_path, "--check", "--archives", presence_dir,
             "--fold-carry", "--since", "5000"])
        write_text(dated_path,
                   "# fixture header\n"
                   "# --- R5003 fold append (fixture)\n"
                   "2026-11-19 R5003 fixture narrative line\n"
                   "2026-11-19 R5003 a dated narrative with no ledger\n")
        still_red = LL.audit_fold_carry([dated_path], 5000)
        write_text(dated_path, archive_block([5001, 5002]))
        bare_ok = LL.audit_fold_carry([dated_path], 5000)

        import ledger_line_shape_guard as LLSG
        door = LLSG.check_candidate(dated_line)
        with io.open(MODULE, "r", encoding="ascii") as handle:
            presence_src = handle.read()
        wired = ("LEDGER_PRESENCE_RE.match(line)" in presence_src
                 and "archive_rounds.add(int(presence.group(1)))"
                 in presence_src)

        real_paths = LL.archive_files(LL.default_logs_dir(STATE))
        shape_rounds = set()
        windows_n = 0
        rounds_n = 0
        skipped_n = 0
        shape_gaps = []
        for path in real_paths:
            for window in LL.load_archive_windows(path):
                for line in window["lines"]:
                    if LL.classify(line) == "ledger":
                        shape_rounds.add(
                            int(LL.LEDGER_PREFIX_RE.match(line).group(1)))
                if window["round"] < LL.FOLD_CARRY_PIN:
                    skipped_n += 1
                    continue
                windows_n += 1
                for round_no in sorted(set(
                        int(LL.NARRATIVE_RE.match(line).group(1))
                        for line in window["lines"]
                        if LL.classify(line) == "round")):
                    rounds_n += 1
                    if round_no not in shape_rounds:
                        shape_gaps.append((window["round"], round_no))
        real_carry2 = LL.audit_fold_carry(
            real_paths, live_lines=LL.load_state_log(STATE))
        check(closed["clean"] is True and closed["gaps"] == []
              and closed["windows"] == 1 and closed["rounds"] == 1
              and rc_dat == 0 and out_dat.startswith("FOLD-CARRY OK")
              and still_red["clean"] is False
              and [(item["round"], item["window"])
                   for item in still_red["gaps"]] == [(5003, 5003)]
              and bare_ok["clean"] is True and bare_ok["windows"] == 1
              and bare_ok["rounds"] == 2
              and LL.classify(dated_line) == "round"
              and error_code(lambda: LL.parse_ledger_line(dated_line))
              == "E_LGR_NO_ROUND"
              and LL.LEDGER_PREFIX_RE.pattern == r"^R(\d{3,5}) tokens:"
              and door["verdict"] == "REFUSED"
              and door["code"] == "E_LLSG_DATE_PREFIX"
              and wired
              and real_carry2["clean"] is True
              and real_carry2["vacuous"] is False
              and real_carry2["windows"] == windows_n
              and real_carry2["rounds"] == rounds_n
              and real_carry2["skipped_windows"] == skipped_n
              and all(item["round"] != 2980
                      for item in real_carry2["gaps"])
              and (2987, 2980) in shape_gaps,
              "AC-LGA10 presence sees a dated ledger line, shape still "
              "refuses it, and only the round set moved")

        # AC-LGA11 (R3086): the archive COUNT face and the cross-window walk
        # ask the PRESENCE law, while the shape law and classify() stay put.
        # Measured before this block: 786 dated ledger lines over the three
        # archives were counted as round narratives (archive_ledger_lines
        # 1090 where presence reads 1876) and one split round could not be
        # told from a whole one (4 split rounds and 3 same-window gaps over
        # the 29 post-pin windows). Six arms: (a) a dated ledger line is
        # counted as ledger by the archive face and still classified as a
        # round by the shape face; (b) in a world without dated lines the
        # two faces agree exactly; (c) a round whose narrative sits in two
        # post-pin windows is NAMED and still clean; (d) a round whose
        # narrative and ledger sit in different windows is NAMED by
        # same_window_gaps, still clean, and the printed line carries both
        # counts in pure ASCII; (e) every round the real tree names there
        # really has its ledger line somewhere in the archives; (f) the
        # real tree's archive_ledger_lines equals an independent presence
        # count, and the old classify count plus the dated lines equals it.
        mixed = os.path.join(world, "logs-lga11")
        os.makedirs(mixed)
        mixed_file = os.path.join(mixed, "state-log-archive-2026-12.md")
        dated = "2026-11-19 " + ledger(6002)
        write_text(mixed_file, "# fixture header\n"
                          "# --- R6001 fold append (fixture)\n"
                          + narrative(6001) + "\n"
                          + ledger(6001) + "\n"
                          + dated + "\n"
                          + narrative(6002) + "\n"
                          "# --- R6010 fold append (fixture)\n"
                          + narrative(6001) + "\n"
                          + ledger(6010) + "\n"
                          + narrative(6011) + "\n"
                          + narrative(6012) + "\n"
                          "# --- R6020 fold append (fixture)\n"
                          + ledger(6011) + "\n"
                          + ledger(6012) + "\n")
        mixed_lines = LL.load_archive(mixed_file)
        scoped_mixed = LL.audit_scope(mixed_lines, live)
        scoped_plain = LL.audit_scope(LL.load_archive_lines(logs), live)
        mixed_carry = LL.audit_fold_carry(
            [mixed_file], 6000)
        plain_kinds = {"ledger": 0, "round": 0}
        for line in LL.load_archive_lines(logs):
            plain_kinds[LL.classify(line)] += 1
        real_logs = LL.default_logs_dir(STATE)
        real_archives = LL.load_archive_lines(real_logs)
        real_scope = LL.audit_scope(real_archives, live)
        real_carry = LL.audit_fold_carry(
            LL.archive_files(real_logs), live_lines=live)
        presence_rounds = set()
        presence_count = 0
        classify_count = 0
        dated_count = 0
        for line in real_archives:
            if LL.LEDGER_PRESENCE_RE.match(line):
                presence_count += 1
                presence_rounds.add(
                    int(LL.LEDGER_PRESENCE_RE.match(line).group(1)))
                if LL.LEDGER_PREFIX_RE.match(line) is None:
                    dated_count += 1
            if LL.classify(line) == "ledger":
                classify_count += 1
        check(LL.classify(dated) == "round"
              and scoped_mixed["archive_ledger_lines"] == 5
              and scoped_mixed["archive_round_lines"] == 5
              and scoped_plain["archive_ledger_lines"]
              == plain_kinds["ledger"]
              and scoped_plain["archive_round_lines"]
              == plain_kinds["round"]
              and [(item["round"], item["windows"])
                   for item in mixed_carry["split_rounds"]]
              == [(6001, [6001, 6010])]
              and [(item["round"], item["window"])
                   for item in mixed_carry["same_window_gaps"]]
              == [(6001, 6010), (6011, 6010), (6012, 6010)]
              and mixed_carry["clean"] is True
              and mixed_carry["gaps"] == []
              and "split=1" in LL.format_fold_carry(mixed_carry)
              and "same_window=3" in LL.format_fold_carry(mixed_carry)
              and LL.format_fold_carry(mixed_carry).isascii()
              and all(item["round"] in presence_rounds
                      for item in real_carry["same_window_gaps"])
              and real_scope["archive_ledger_lines"] == presence_count
              and classify_count + dated_count == presence_count
              and dated_count > 0,
              "AC-LGA11 archive counts and the cross-window walk read the "
              "presence law; classify(), the shape law and the verdict "
              "stay unchanged")

        # AC-LGA12 (R3087): the cross-window diagnostics are only usable if
        # a reader can LOCATE the window they name, and the archive payload
        # reading the audit never made is published without gating. Measured
        # before this block: 2 of the 3 live same_window gaps carried the
        # same marker twice (2946 and 3085, one fold pair each), so a marker
        # alone could not say which window is short; and 787 archive ledger
        # lines cannot be parsed (785 from the pre-law 'local=unmeasured'
        # era, 2 carrying a doubled prefix), a number no reader could see.
        dup = os.path.join(world, "logs-lga12")
        os.makedirs(dup)
        dup_file = os.path.join(dup, "state-log-archive-2026-12.md")
        write_text(dup_file, "# fixture header\n"
                          "# --- R7001 fold append (fixture)\n"
                          + narrative(7002) + "\n"
                          + ledger(7011) + "\n"
                          "# --- R7001 fold append again (fixture)\n"
                          + ledger(7002) + "\n"
                          + narrative(7005) + "\n"
                          + ledger(7005) + "\n")
        dup_carry = LL.audit_fold_carry([dup_file], 7000)
        dist = os.path.join(world, "logs-lga12-distinct")
        os.makedirs(dist)
        dist_file = os.path.join(dist, "state-log-archive-2026-12.md")
        write_text(dist_file, "# fixture header\n"
                           "# --- R7001 fold append (fixture)\n"
                           + narrative(7004) + "\n"
                           "# --- R7010 fold append (fixture)\n"
                           + ledger(7004) + "\n"
                           + narrative(7004) + "\n")
        dist_carry = LL.audit_fold_carry([dist_file], 7000)
        pay = os.path.join(world, "logs-lga12-payload")
        os.makedirs(pay)
        pay_file = os.path.join(pay, "state-log-archive-2026-12.md")
        healthy = ledger(7021)
        dated_good = "2026-11-19 " + ledger(7022)
        dated_bad = "2026-11-19 R7023 tokens: local=unmeasured api=0 " \
                    "api_reason=pre-law unmeasured era fixture"
        bare_bad = "R7024 tokens: R7024 tokens: local=1k api=0 " \
                   "api_reason=doubled prefix fixture"
        write_text(pay_file, "# fixture header\n"
                          "# --- R7020 fold append (fixture)\n"
                          + healthy + "\n" + dated_good + "\n"
                          + dated_bad + "\n" + bare_bad + "\n")
        pay_report = LL.audit_archive(LL.load_archive(pay_file))
        good_only = os.path.join(pay, "state-log-archive-2026-12b.md")
        write_text(good_only, "# fixture header\n"
                          "# --- R7020 fold append (fixture)\n"
                          + dated_good + "\n")
        good_report = LL.audit_archive(LL.load_archive(good_only))
        real_logs3 = LL.default_logs_dir(STATE)
        real_payload = LL.audit_archive(LL.load_archive_lines(real_logs3))
        real_carry3 = LL.audit_fold_carry(
            LL.archive_files(real_logs3), live_lines=LL.load_state_log(STATE))
        real_scope3 = LL.audit_scope(
            LL.load_archive_lines(real_logs3), live)

        # R3496: an independent recount of the same_window diagnostic, so the
        # published pairs cannot be self-certified. A round's narrative sits
        # in a post-pin window while its presence line is not in THAT window;
        # several rounds may share one window (a fold moves a range), so the
        # reading is a list of pairs, never one entry per window.
        def same_window_recount(paths, live_rounds=None):
            archive_rounds = set()
            for path in paths:
                for window in LL.load_archive_windows(path):
                    for line in window["lines"]:
                        hit = LL.LEDGER_PRESENCE_RE.match(line)
                        if hit is not None:
                            archive_rounds.add(int(hit.group(1)))
            receipts = LL.block_receipts(paths)
            out = []
            seen_narrative = {}
            for path in paths:
                for window in LL.load_archive_windows(path):
                    if window["round"] < LL.FOLD_CARRY_PIN:
                        continue
                    here = set()
                    narratives = {}
                    for line in window["lines"]:
                        hit = LL.LEDGER_PRESENCE_RE.match(line)
                        if hit is not None:
                            here.add(int(hit.group(1)))
                        if LL.classify(line) == "round":
                            round_no = int(
                                LL.NARRATIVE_RE.match(line).group(1))
                            narratives.setdefault(round_no, []).append(line)
                            seen_narrative.setdefault(
                                round_no, []).append(line)
                    for round_no in sorted(narratives):
                        verdict, _why = LL.fold_carry_exemption(
                            round_no, seen_narrative.get(round_no, []),
                            archive_rounds, receipts,
                            live_rounds=live_rounds)
                        if verdict or round_no in here:
                            continue
                        out.append((window["round"], round_no))
            return sorted(out)
        # AC-LGA12 is ONE criterion with six arms, as pinned: a..c the
        # locatable cross-window diagnostics, d..e the published payload
        # reading with its negative control, f the live identities.
        check([item["window_index"] for item
               in dup_carry["same_window_gaps"]] == [1]
              and [item["round"] for item
                   in dup_carry["same_window_gaps"]] == [7002]
              and dup_carry["duplicate_markers"] == [7001]
              and dup_carry["clean"] is True
              and dist_carry["duplicate_markers"] == []
              and [(item["round"], item["windows"],
                    item["window_indices"])
                   for item in dist_carry["split_rounds"]]
              == [(7004, [7001, 7010], [1, 2])]
              and [item["window_index"] for item
                   in dist_carry["same_window_gaps"]] == [1]
              and "dup=1" in LL.format_fold_carry(dup_carry)
              and "dup=0" in LL.format_fold_carry(dist_carry)
              and "dup=" in LL.format_fold_carry(real_carry3)
              and LL.format_fold_carry(dup_carry).isascii()
              and LL.format_fold_carry(real_carry3).isascii()
              and pay_report["ledger_lines"] == 4
              and pay_report["bare_ledger_lines"] == 2
              and pay_report["dated_ledger_lines"] == 2
              and pay_report["unshaped_ledger_lines"] == 2
              and pay_report["unshaped_codes"] == {"E_LGR_BAD_LOCAL": 1,
                                                   "E_LGR_NO_LOCAL": 1}
              and good_report["dated_ledger_lines"] == 1
              and good_report["unshaped_ledger_lines"] == 0
              and good_report["unshaped_codes"] == {}
              and sum(pay_report["unshaped_codes"].values())
              == pay_report["unshaped_ledger_lines"]
              and real_payload["ledger_lines"]
              == real_payload["bare_ledger_lines"]
              + real_payload["dated_ledger_lines"]
              and real_payload["unshaped_ledger_lines"]
              <= real_payload["ledger_lines"]
              and real_payload["dated_ledger_lines"] > 0
              and sum(real_payload["unshaped_codes"].values())
              == real_payload["unshaped_ledger_lines"]
              and real_scope3["archive_dated_ledger_lines"]
              == real_payload["dated_ledger_lines"]
              and real_scope3["archive_unshaped_ledger_lines"]
              == real_payload["unshaped_ledger_lines"]
              # R3496: this arm used to demand one same-window gap per
              # window, which no healthy archive can satisfy - a fold moves a
              # contiguous range, so several rounds whose ledger lines stayed
              # live share one window (measured: 27 entries over 7 shared
              # windows, window R3491 alone hosting 13). The clause is
              # replaced by an independent recount of the published pairs,
              # which is stricter than a count and blind to how many rounds
              # one window holds.
              and sorted((item["window"], item["round"]) for item
                         in real_carry3["same_window_gaps"])
              == same_window_recount(LL.archive_files(real_logs3),
                                     live_rounds=LL.tree_presence_rounds(live)),
              "AC-LGA12 the cross-window diagnostics locate their window, "
              "and the archive payload reading is published without gating")

        # AC-LGA13 (R3089): a published position a reader cannot open is a
        # decoration. window_index starts at the pin, so the live report's
        # 'window 18' is the file's 220th window at line 4511 - a 202-window
        # offset no reader is told about. The archive's own coordinates
        # (file, in-file ordinal, marker line) are measured unique, dense
        # and append-stable, so they are published beside window_index.
        two = os.path.join(world, "logs-lga13")
        os.makedirs(two)
        two_file = os.path.join(two, "state-log-archive-2026-12.md")
        two_text = ("# fixture header\n"
                    "# --- R7031 fold append (fixture)\n"
                    + narrative(7032) + "\n"
                    "# --- R7031 fold append again (fixture)\n"
                    + narrative(7033) + "\n")
        write_text(two_file, two_text)
        two_carry = LL.audit_fold_carry([two_file], 7000)
        two_lines = two_text.split("\n")
        real_files = LL.archive_files(real_logs3)
        real_layout = {}
        raw_lines = {}
        for path in real_files:
            rows = LL.load_archive_windows(path)
            real_layout[path] = rows
            raw_lines[os.path.basename(path)] = io.open(
                path, "r", encoding="utf-8").read().split("\n")
        dense = True
        lines_match = True
        for path, rows in real_layout.items():
            if [r["ordinal"] for r in rows] != list(range(1, len(rows) + 1)):
                dense = False
            raw = io.open(path, "r", encoding="utf-8").read().split("\n")
            for row in rows:
                head = raw[row["line"] - 1]
                if not head.startswith("# --- R%d" % row["round"]):
                    lines_match = False
        opens = True
        for item in real_carry3["same_window_gaps"]:
            head = raw_lines[item["file"]][item["line"] - 1]
            if not head.startswith("# --- R%d" % item["window"]):
                opens = False
        for item in real_carry3["split_rounds"]:
            for loc in item["locators"]:
                head = raw_lines[loc["file"]][loc["line"] - 1]
                if not head.startswith("# --- R"):
                    opens = False
        check([(item["window_index"], item["file_ordinal"], item["line"])
               for item in two_carry["same_window_gaps"]] == [(1, 1, 2),
                                                             (2, 2, 4)]
              and all(two_lines[item["line"] - 1].startswith("# --- R7031")
                      for item in two_carry["same_window_gaps"])
              and two_carry["duplicate_markers"] == [7031]
              and len({item["file_ordinal"] for item
                       in two_carry["same_window_gaps"]}) == 2
              and [(item["file_ordinal"], item["line"])
                   for item in two_carry["gaps"]] == [(1, 2), (2, 4)]
              and all(item["file"] == "state-log-archive-2026-12.md"
                      for item in two_carry["same_window_gaps"]
                      + two_carry["gaps"])
              and [(len(item["locators"]), item["window_indices"])
                   for item in dist_carry["split_rounds"]] == [(2, [1, 2])]
              and [loc["file_ordinal"] for loc
                   in dist_carry["split_rounds"][0]["locators"]] == [1, 2]
              and [loc["line"] for loc
                   in dist_carry["split_rounds"][0]["locators"]] == [2, 4]
              and real_carry3["clean"] is True
              and opens
              and dense
              and lines_match
              and real_carry3["windows"] == sum(
                  len([r for r in rows if r["round"] >= real_carry3["since"]])
                  for rows in real_layout.values())
              and LL.format_fold_carry(two_carry).endswith("loc=file@line")
              and LL.format_fold_carry(dist_carry).endswith("loc=file@line")
              and LL.format_fold_carry(LL.audit_fold_carry([two_file],
                                                           9000)
                                       ).endswith("loc=file@line")
              and LL.format_fold_carry(two_carry).isascii()
              and [item["window_index"] for item
                   in two_carry["same_window_gaps"]] == [1, 2]
              and dist_carry["split_rounds"][0]["windows"] == [7001, 7010],
              "AC-LGA13 every published position is openable - file, in-file "
              "ordinal and marker line - while window_index keeps its "
              "measured meaning")

        # AC-LGA14 (R3092): the positions are openable but the line never
        # said how strong the claim is - three archives are read and only one
        # is git-tracked, so 'loc=file@line' was equally true of a frozen file
        # and of an unbacked one. The CLI now appends the provenance it reads
        # from the repository index, while a report built without provenance
        # renders the pre-R3092 bytes exactly, which is why the five literal
        # pins on the two green shapes did not have to move.
        plain = LL.audit_fold_carry([two_file], 7000)
        ok_shape = LL.format_fold_carry(plain)
        vac_shape = LL.format_fold_carry(LL.audit_fold_carry([two_file], 9999))
        red_dir = os.path.join(world, "logs-lga14-red")
        os.makedirs(red_dir)
        red_file = os.path.join(red_dir, "state-log-archive-2026-12.md")
        write_text(red_file, "# fixture header\n"
                             "# --- R7101 fold append (fixture)\n"
                             + narrative(7102) + "\n")
        fail_shape = LL.format_fold_carry(LL.audit_fold_carry([red_file],
                                                              7000))
        counted = LL.audit_fold_carry([two_file], 7000,
                                      provenance={"tracked": 1, "total": 3})
        refused = LL.audit_fold_carry([two_file], 7000,
                                      provenance={"error": "E_APR_NO_INDEX"})
        counted_line = LL.format_fold_carry(counted)
        refused_line = LL.format_fold_carry(refused)
        # independent count: the reader alone, over exactly the files the CLI
        # hands it, so the published numbers cannot be self-certified
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import archive_provenance as APR
        live_paths = LL.archive_files(real_logs3)
        live_tracked, _stats = APR.read_index(
            os.path.join(REPO, ".git", "index"))
        manual_hits = sum(1 for path in live_paths
                          if os.path.relpath(path, REPO).replace(
                              os.sep, "/") in live_tracked)
        live_prov = LL.provenance_counts(live_paths)
        rc_live, out_live, _ = run_cli(
            [STATE, "--check", "--archives", real_logs3, "--fold-carry",
             "--since", str(LL.FOLD_CARRY_PIN)])
        lonely = os.path.join(world, "logs-lga14")
        os.makedirs(lonely)
        write_text(os.path.join(lonely, "state-log-archive-2026-12.md"),
                   archive_block([6001, 6002]))
        lonely_prov = LL.provenance_counts(
            LL.archive_files(lonely))
        rc_lonely, out_lonely, _ = run_cli(
            [STATE, "--check", "--archives", lonely, "--fold-carry",
             "--since", "6000"])
        with io.open(MODULE, "r", encoding="ascii") as handle:
            ledger_src = handle.read()
        import ast
        module_imports = set()
        for node in ast.parse(ledger_src).body:
            if isinstance(node, ast.Import):
                module_imports.update(alias.name.split(".")[0]
                                      for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_imports.add(node.module.split(".")[0])
        check(
            # a: library shapes are byte-identical to the pre-R3092 line
            ok_shape.endswith("loc=file@line")
            and "prov=" not in ok_shape
            and vac_shape.endswith("loc=file@line")
            and "prov=" not in vac_shape
            and "prov=" not in fail_shape
            and "duplicate_markers" in plain
            # b: a measured count is printed, ASCII, numbers verbatim
            and counted_line.endswith(" prov=tracked=1/3")
            and counted_line.isascii()
            and LL.format_fold_carry(
                LL.audit_fold_carry([two_file], 7000,
                                    provenance={"tracked": 0,
                                                "total": 2})
            ).endswith(" prov=tracked=0/2")
            # c: an unreadable index says so instead of implying 'all backed'
            and refused_line.endswith(" prov=n/a")
            and refused_line.isascii()
            # d: the live numbers agree with an independent index count
            and isinstance(live_prov, dict)
            and live_prov.get("tracked") == manual_hits
            and live_prov.get("total") == len(live_paths)
            and ("prov=tracked=%d/%d" % (manual_hits, len(live_paths)))
            in out_live
            and live_prov.get("total") == 3
            # e: a world with no index returns an error, and the CLI line
            #    still reads OK with prov=n/a at the same rc as before
            and isinstance(lonely_prov, dict)
            and "error" in lonely_prov
            and rc_lonely == 0
            and out_lonely.startswith("FOLD-CARRY OK")
            and "prov=n/a" in out_lonely
            and "prov=tracked=" not in out_lonely
            # f: no child process and no socket on the module import surface,
            #    and the index reader is imported INSIDE the function so a
            #    tree without tools/ can still import this module
            and "subprocess" not in module_imports
            and "socket" not in module_imports
            and "archive_provenance" not in module_imports
            and "archive_provenance.read_index" in ledger_src,
            "AC-LGA14 the FOLD-CARRY line publishes how many of the archives "
            "it just read are git-tracked (prov=tracked=n/m, prov=n/a when "
            "the index is unreadable) while a library report without "
            "provenance keeps the pre-R3092 bytes")

        # AC-LGA15 (R3356): a window whose round can never carry a ledger
        # line may be excused, but only BY NAME and only while BOTH halves
        # of its evidence still hold. Measured before this block: the only
        # such gap on the shipped tree is R3112, a round-alignment closeout
        # whose narrative says 'tick moved 3111 -> 3112' because a replay
        # probe was read as a new append; no budget line exists for it in
        # either the archives or the live log. The table is not a licence:
        # an unnamed round with the same prose, a named entry whose span was
        # removed, an entry that gained a ledger line, and a SECOND gap in
        # the same archive all still red, and the excused round is printed
        # by name on the verdict line.
        span = "tick moved 3111 -> 3112"
        ex_dir = os.path.join(world, "logs-lga15")
        os.makedirs(ex_dir)
        ex_file = os.path.join(ex_dir, "state-log-archive-2026-12.md")

        def ex_window(marker, body):
            write_text(ex_file,
                       "# state-log-archive fixture header\n"
                       "# --- R%d fold append (fixture)\n" % marker
                       + "".join(item + "\n" for item in body))
            return LL.audit_fold_carry([ex_file], 3000)

        plain_gap = ex_window(5003, [narrative(5003)])
        span_other = ex_window(5003, ["R5003 %s" % span])
        excused = ex_window(3130, ["2026-11-21 R3112 PRODUCT: round "
                                   "alignment closeout, %s" % span])
        not_swallowed = ex_window(3130,
                                  ["2026-11-21 R3112 PRODUCT: %s" % span,
                                   narrative(5003)])
        span_gone = ex_window(3130, ["2026-11-21 R3112 PRODUCT: round "
                                     "alignment closeout with no span"])
        has_line = ex_window(3130, ["2026-11-21 R3112 PRODUCT: %s" % span,
                                    ledger(3112)])
        live_rounds = set()
        for item in LL.load_state_log(STATE):
            hit = LL.LEDGER_PRESENCE_RE.match(item)
            if hit is not None:
                live_rounds.add(int(hit.group(1)))
        archive_rounds = set()
        for path in real_paths:
            for window in LL.load_archive_windows(path):
                for item in window["lines"]:
                    hit = LL.LEDGER_PRESENCE_RE.match(item)
                    if hit is not None:
                        archive_rounds.add(int(hit.group(1)))
        real_excused = LL.audit_fold_carry(
            real_paths, live_lines=LL.load_state_log(STATE))
        excused_line = LL.format_fold_carry(excused)
        check(
            # a: an ordinary missing ledger line still reds, unnamed
            plain_gap["clean"] is False
            and [(item["round"], item["window"])
                 for item in plain_gap["gaps"]] == [(5003, 5003)]
            and plain_gap["exemptions"] == []
            # b: the same prose under a round the table does not name is red
            and span_other["clean"] is False
            and [item["round"] for item in span_other["gaps"]] == [5003]
            and span_other["exemptions"] == []
            # c: the named entry with both halves is excused and printed
            and excused["clean"] is True
            and [item["round"] for item in excused["exemptions"]] == [3112]
            and [item["why"] for item in excused["exemptions"]]
            == [LL.FOLD_CARRY_EXEMPT[3112]["why"]]
            and "exempt=1(R3112)" in excused_line
            and excused_line.startswith("FOLD-CARRY OK")
            and excused_line.isascii()
            # d: the exemption cell never swallows a second gap
            and not_swallowed["clean"] is False
            and [item["round"] for item in not_swallowed["gaps"]] == [5003]
            and [item["round"] for item in not_swallowed["exemptions"]]
            == [3112]
            # e: evidence removed or contradicted refuses by name
            and span_gone["clean"] is False
            and [item["round"] for item in span_gone["gaps"]] == [3112]
            and [item["why"] for item in span_gone["exemption_refusals"]]
            == ["narrative-lacks-span"]
            and has_line["clean"] is True
            and has_line["gaps"] == []
            and has_line["exemptions"] == []
            and LL.fold_carry_exemption(3112, [], set())[0] is False
            and LL.fold_carry_exemption(3112, [span], {3112})[0] is False
            and LL.fold_carry_exemption(5003, [span], set())[0] is False
            # f: the shipped tree's own evidence agrees - the excused round
            #    has no budget line anywhere, and it is the table that did it
            and 3112 not in live_rounds
            and 3112 not in archive_rounds
            and real_excused["clean"] is True
            and 3112 in [item["round"]
                         for item in real_excused["exemptions"]]
            and all(item["round"] in LL.FOLD_CARRY_EXEMPT
                    for item in real_excused["exemptions"])
            and real_excused["exemption_refusals"] == [],
            "AC-LGA15 a tick-alignment window with no ledger line anywhere is "
            "excused only by name and only while its own narrative still "
            "carries the recorded span")

        # AC-LGA16 (R3497): the table has three evidence kinds and each one
        # carried a measured negative face that no arm pinned. Registered as
        # ONE criterion with six arms on a fixture archive, never on history:
        #   a: an entry whose receipt records a budget part is refused
        #   b: an entry narrower than the archive's own summary is refused too
        #   c: the same budget-free summary under an UN-NAMED round still reds
        #   d: an entry recording no evidence kind at all is refused by name
        #   e: inline payload prose under an UN-NAMED round still reds, while
        #      the same prose on the NAMED round is excused
        #   f: the shipped table is whole again and the real tree still clean
        arms_dir = os.path.join(world, "logs-lga16")
        os.makedirs(arms_dir)
        arms_file = os.path.join(arms_dir, "state-log-archive-2026-12.md")

        def arms_window(marker, body):
            write_text(arms_file,
                       "# state-log-archive fixture header\n"
                       "# --- R%d fold append (fixture)\n" % marker
                       + "".join(item + "\n" for item in body))
            return LL.audit_fold_carry([arms_file], 3000)

        budget_receipt = ("fold 9001 moved the whole R7002 block "
                          "(product, tokens) verbatim")
        clean_receipt = ("fold 9001 moved the whole R7002 block "
                         "(product, landed) verbatim")
        payload = "tokens: local=~24k api=0 api_reason=no cloud call"
        shipped = dict(LL.FOLD_CARRY_EXEMPT)
        try:
            LL.FOLD_CARRY_EXEMPT[7002] = {
                "why": "fixture: receipt that names the budget part",
                "receipt": {"file": "state-log-archive-2026-12.md",
                            "parts": ["product", "tokens"]}}
            arm_a = arms_window(7001, [narrative(7002), budget_receipt])
            LL.FOLD_CARRY_EXEMPT[7002] = {
                "why": "fixture: part list narrower than the archive summary",
                "receipt": {"file": "state-log-archive-2026-12.md",
                            "parts": ["product", "landed"]}}
            arm_b = arms_window(7001, [narrative(7002), budget_receipt])
            arm_c = arms_window(7001, [narrative(7003), clean_receipt])
            LL.FOLD_CARRY_EXEMPT[7004] = {
                "why": "fixture: no evidence kind recorded"}
            arm_d = arms_window(7001, [narrative(7004)])
            LL.FOLD_CARRY_EXEMPT[7005] = {
                "why": "fixture: inline payload", "inline_payload": payload}
            arm_e = arms_window(7001, ["R7006 fixture %s" % payload])
            # asked while the probe entry is still in the table: the SAME
            # prose on the NAMED round must be admitted.
            named_e = LL.fold_carry_exemption(
                7005, ["R7005 fixture %s" % payload], set())
            # R3632 AC-TAB3: the fourth kind - whole-tree absence - and its
            # refusals. Every arm is a private fixture world, never history,
            # and the live half is handed in explicitly.
            absent = {"why": "fixture: tree absence",
                      "tree_absence": {"presence_lines": 0}}
            LL.FOLD_CARRY_EXEMPT[7105] = dict(absent)
            arm_g = arms_window(7101, [narrative(7105)])
            arm_h = LL.audit_fold_carry(
                [arms_file], 3000,
                live_lines=["R7105 tokens: local=1k api=0 "
                            "api_reason=fixture"])
            LL.FOLD_CARRY_EXEMPT[7105] = {
                "why": "fixture: tree absence recorded as one",
                "tree_absence": {"presence_lines": 1}}
            arm_j = LL.audit_fold_carry([arms_file], 3000, live_lines=[])
            LL.FOLD_CARRY_EXEMPT[7105] = dict(absent)
            arm_i = LL.audit_fold_carry([arms_file], 3000, live_lines=[])
            LL.FOLD_CARRY_EXEMPT[7106] = dict(absent)
            arm_k = arms_window(7101, ["R7106 fixture %s" % payload])
        finally:
            LL.FOLD_CARRY_EXEMPT.clear()
            LL.FOLD_CARRY_EXEMPT.update(shipped)

        check(
            # a: the recorded list matches the archive's byte for byte, but it
            #    names the budget part - the R3421 shape, refused by name
            arm_a["clean"] is False
            and [(item["round"], item["window"]) for item in arm_a["gaps"]]
            == [(7002, 7001)]
            and arm_a["exemptions"] == []
            and [item["why"] for item in arm_a["exemption_refusals"]]
            == ["receipt-has-budget"]
            # b: narrowing the table's list does not help while the summary it
            #    points at still names the budget part
            and arm_b["clean"] is False
            and [item["round"] for item in arm_b["gaps"]] == [7002]
            and [item["why"] for item in arm_b["exemption_refusals"]]
            == ["receipt-has-budget"]
            # c: a receipt is evidence for ONE named round; the same summary
            #    under an unnamed round excuses nothing
            and arm_c["clean"] is False
            and [item["round"] for item in arm_c["gaps"]] == [7003]
            and arm_c["exemptions"] == []
            and 7003 not in LL.FOLD_CARRY_EXEMPT
            # d: no evidence kind is a refusal, not a free pass on prose
            and arm_d["clean"] is False
            and [item["why"] for item in arm_d["exemption_refusals"]]
            == ["no-span-recorded"]
            # e: the payload prose is not the discriminator - unnamed reds
            and arm_e["clean"] is False
            and [item["round"] for item in arm_e["gaps"]] == [7006]
            and arm_e["exemptions"] == []
            # f: ... and the NAMED round carrying the same prose is excused,
            #    the probe entries are gone, and the real tree still reads
            #    clean with exactly its shipped exemptions
            and named_e[0] is True
            # g: without the live half the absence is unprovable - refused
            and arm_g["clean"] is False
            and [item["round"] for item in arm_g["gaps"]] == [7105]
            and [item["why"] for item in arm_g["exemption_refusals"]]
            == ["no-tree-provided"]
            # h: one live presence line for the named round refuses it
            and arm_h["clean"] is False
            and [item["why"] for item in arm_h["exemption_refusals"]]
            == ["tree-has-presence"]
            # j: the recorded count is a measured claim, not prose
            and arm_j["clean"] is False
            and [item["why"] for item in arm_j["exemption_refusals"]]
            == ["receipt-mismatch"]
            # i: both halves absent and no payload - excused and named
            and arm_i["clean"] is True
            and [item["round"] for item in arm_i["exemptions"]] == [7105]
            and "exempt=1(R7105)" in LL.format_fold_carry(arm_i)
            # k: payload prose belongs to the inline kind, never to absence
            and arm_k["clean"] is False
            and [item["why"] for item in arm_k["exemption_refusals"]]
            == ["narrative-has-payload"]
            # v: the same absence shape on an UN-NAMED round still reds
            and plain_gap["clean"] is False and plain_gap["exemptions"] == []
            and set(LL.FOLD_CARRY_EXEMPT) == set(shipped)
            and not [key for key in LL.FOLD_CARRY_EXEMPT if key >= 7000]
            and real_excused["clean"] is True
            and real_excused["exemption_refusals"] == []
            and 3610 in [item["round"] for item in real_excused["exemptions"]],
            "AC-LGA16 an exemption is refused by name when its receipt names "
            "a budget part or when it records no evidence kind, and neither a "
            "budget-free summary nor an inline payload excuses a round the "
            "table does not name")

    finally:
        shutil.rmtree(world, ignore_errors=True)



def main():
    print("suite: archive-aware ledger coverage (R2224 AC-LGA1..AC-LGA16)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())
