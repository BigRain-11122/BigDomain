"""Runner wall-time profile tracker (R1684, P2 tech-queue head item;
AC-RP1..RP7 pre-registered in state/queue/tech.md claim row, before
this file existed).

reconcile_all.py already emits one wall-time line per suite into its
evidence logs ("PASS suite <label> exit=0 ... criteria=N <sec>s") and
a RUNNER PASS summary. This tool is a parse-only face over those
logs: it ranks suites by duration, keeps a machine-generated
baseline, and flags regression drift against a pre-registered
threshold. The runner itself is never modified (AC-RP6).

Pre-registered drift rule (AC-RP4, registered before measurement):

    drift iff cur > base + max(2.0s, 0.5 * base)

per-suite and on the shared-suite seconds sum. The 2.0s absolute
floor exists because wall-clock here is dominated by co-residency
CPU noise (R550 vs R685 verdict: N=100 p95 304.0ms under co-resident
load vs 29.5ms near-idle - small absolute deltas are not
meaningful); slow suites get the 50 percent relative slack. Suite
fan-out growth is the expected face per the seed (25 suites 19.0s ->
37 suites), so NEW-SUITE / REMOVED-SUITE are info lines, never drift
flags, and the total compare runs over the shared-suite set only.

Usage:
    python runner_profile.py                    # profile newest
                                                # eligible evidence
                                                # + drift compare
    python runner_profile.py --daily            # daily variant:
                                                # discovery restricted
                                                # to reconcile-daily-*
                                                # logs, baseline kept
                                                # in a separate
                                                # runner-profile-daily
                                                # -baseline.json
    python runner_profile.py --update-baseline  # (re)write baseline
    python runner_profile.py --check            # stale-baseline
                                                # detector
    python runner_profile.py --selftest         # hygiene + synthetic
                                                # drift demo
    python runner_profile.py --log <path>       # explicit target
    (any mode accepts --out <path> to append a utf-8 evidence copy)

R1715 daily variant (criteria AC-RD1..RD6 pre-registered in
state/queue/tech.md before this change): the daily wrapper
(reconcile_daily.py) tees the same runner sections into its dated
evidence logs plus an appended sentinel section; parse_log is already
inert to those sentinel lines (they match no suite/runner regex), so
the daily face is purely a discovery restriction + a separate baseline
file. Render/compare/threshold family are reused byte-identical
(AC-RD3); without --daily the existing behavior is unchanged.

Discovery default: newest qa/*.log (skipping runner-profile-* self
evidence) that parses as one RUNNER PASS + consistent suite lines.
Daily discovery: same eligibility walk restricted to
reconcile-daily-*.log names.

Exit codes: 0 profile/clean, 2 drift-flagged or stale check, 3
parse/eligibility refusal (fail-closed).
"""

import argparse
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, os.pardir, os.pardir))
QA_DIR = os.path.join(REPO, "qa")
BASELINE_NAME = "runner-profile-baseline.json"
DAILY_BASELINE_NAME = "runner-profile-daily-baseline.json"
DAILY_LOG_PREFIX = "reconcile-daily-"


def baseline_path(daily=False):
    name = DAILY_BASELINE_NAME if daily else BASELINE_NAME
    return os.path.join(QA_DIR, name)

sys.path.insert(0, BASE)
import reconcile_all  # noqa: E402 (single fact source, reuse-not-copy)

SUITE_RE = re.compile(
    r"(?m)^PASS suite (\S+) exit=(\d+) pass-lines=(\d+) "
    r"fail-lines=(\d+) criteria=(\d+) ([0-9.]+)s$")
RUNNER_RE = re.compile(
    r"(?m)^RUNNER PASS \((\d+)/(\d+) suites green, "
    r"reconcile controls (\d+)/(\d+), ([0-9.]+)s\)")
FAIL_SUITE_RE = re.compile(r"(?m)^FAIL suite ")

# R1737 (AC-SN2, pre-registered in tech.md before this change): daily
# evidence logs carry the sentinel subprocess elapsed in their tail
# line ("sentinel exit=N elapsed=X.Xs" - reconcile_daily.py AC-SN1).
# Exactly one such line is expected; the pre-R1737 legacy form
# ("sentinel exit=N", no elapsed) parses as sentinel_seconds=None and
# logs without any sentinel section (the main face) stay inert.
SENTINEL_TAIL_RE = re.compile(
    r"(?m)^sentinel exit=(\d+) elapsed=([0-9.]+)s$")

DRIFT_ABS_FLOOR = 2.0
DRIFT_REL = 0.5


class Refusal(Exception):
    """Eligibility refusal -> exit 3 (fail-closed)."""


def _read_text(path):
    """BOM-tolerant + line-ending-tolerant read (qa logs have two
    writer dialects: runner utf-8 tee without BOM, LF endings vs PS
    redirect UTF-16LE BOM or CRLF - R1683 BOM lesson + this round's
    CRLF finding)."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
    elif raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_log(path):
    text = _read_text(path)
    if "RUNNER FAIL" in text:
        raise Refusal("RUNNER FAIL in %s - refusing to profile a "
                      "failing run" % path)
    runner = RUNNER_RE.findall(text)
    if len(runner) != 1:
        raise Refusal("expected exactly one RUNNER PASS line, found %d"
                      % len(runner))
    if FAIL_SUITE_RE.search(text):
        raise Refusal("FAIL suite lines alongside RUNNER PASS "
                      "(inconsistent evidence)")
    green = int(runner[0][0])
    runner_line = RUNNER_RE.search(text).group(0)
    runner_total = float(runner[0][4])
    suites = []
    for m in SUITE_RE.findall(text):
        suites.append({"label": m[0], "exit": int(m[1]),
                       "pass_lines": int(m[2]), "fail_lines": int(m[3]),
                       "criteria": int(m[4]), "seconds": float(m[5])})
    if not suites:
        raise Refusal("no suite lines parsed")
    labels = [s["label"] for s in suites]
    if len(set(labels)) != len(labels):
        raise Refusal("duplicate suite labels in evidence")
    if len(suites) != green:
        raise Refusal("suite lines %d != RUNNER green %d"
                      % (len(suites), green))
    tails = SENTINEL_TAIL_RE.findall(text)
    if len(tails) > 1:
        raise Refusal("multiple sentinel tail lines (inconsistent "
                      "evidence)")
    sentinel_seconds = float(tails[0][1]) if tails else None
    return {"path": path,
            "runner_line": runner_line,
            "runner_total": runner_total,
            "suites": suites,
            "criteria_total": sum(s["criteria"] for s in suites),
            "seconds_sum": sum(s["seconds"] for s in suites),
            "sentinel_seconds": sentinel_seconds}


def discover_target():
    names = [n for n in os.listdir(QA_DIR)
             if n.endswith(".log") and not n.startswith("runner-profile-")]
    paths = [os.path.join(QA_DIR, n) for n in names]
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    for path in paths:
        try:
            return parse_log(path)
        except (Refusal, OSError):
            continue
    raise Refusal("no eligible RUNNER PASS evidence under qa/")


def discover_daily():
    """AC-RD1: daily-face discovery - same eligibility walk restricted
    to reconcile-daily-*.log names; newer non-daily evidence never
    leaks into the daily population (face isolation)."""
    names = [n for n in os.listdir(QA_DIR)
             if n.startswith(DAILY_LOG_PREFIX) and n.endswith(".log")]
    paths = [os.path.join(QA_DIR, n) for n in names]
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    for path in paths:
        try:
            return parse_log(path)
        except (Refusal, OSError):
            continue
    raise Refusal("no eligible daily RUNNER PASS evidence under qa/")


def registry_note(parsed_count):
    reg = len(reconcile_all.SUITES)
    if parsed_count == reg:
        return "ALIGNED"
    if parsed_count < reg:
        return "REGISTRY-GREW (log predates current fan-out)"
    return "REGISTRY-SHRUNK (registry behind evidence)"


def render_profile(data):
    rel = os.path.relpath(data["path"], REPO).replace(os.sep, "/")
    lines = ["== runner wall-time profile ==",
             "target: %s" % rel,
             "runner: %s" % data["runner_line"],
             "parsed: suites=%d criteria_total=%d suite_seconds_sum=%.1f"
             " runner_total=%.1f"
             % (len(data["suites"]), data["criteria_total"],
                data["seconds_sum"], data["runner_total"]),
             "registry: %s (SUITES has %d entries)"
             % (registry_note(len(data["suites"])),
                len(reconcile_all.SUITES))]
    if data.get("sentinel_seconds") is not None:
        lines.append("sentinel-segment: %.1fs (daily sentinel "
                     "subprocess elapsed)" % data["sentinel_seconds"])
    lines.append("profile (rank label seconds criteria sec-per-criterion):")
    ordered = sorted(data["suites"],
                     key=lambda s: (-s["seconds"], s["label"]))
    for rank, s in enumerate(ordered, 1):
        lines.append("  %d %s %.1f %d %.2f"
                     % (rank, s["label"], s["seconds"], s["criteria"],
                        s["seconds"] / s["criteria"]))
    hot = ordered[:5]
    lines.append("top5-hotspots: "
                 + ", ".join("%s %.1fs" % (s["label"], s["seconds"])
                             for s in hot))
    return "\n".join(lines) + "\n"


def drift_slack(base_seconds):
    return max(DRIFT_ABS_FLOOR, DRIFT_REL * base_seconds)


def render_compare(cur, baseline):
    lines = ["== drift compare vs %s ==" % baseline["source_log"],
             "threshold: drift iff cur > base + max(%.1fs, %.1f*base)"
             % (DRIFT_ABS_FLOOR, DRIFT_REL)]
    base_map = baseline["suite_seconds"]
    cur_map = dict((s["label"], s["seconds"]) for s in cur["suites"])
    flagged = []
    compared = 0
    ordered = sorted(cur["suites"],
                     key=lambda s: (-s["seconds"], s["label"]))
    for s in ordered:
        label = s["label"]
        if label not in base_map:
            lines.append("suite %s NEW-SUITE (no baseline entry)" % label)
            continue
        compared += 1
        base = base_map[label]
        cur_s = s["seconds"]
        slack = drift_slack(base)
        over = cur_s > base + slack
        if over:
            flagged.append(label)
        lines.append("suite %s base=%.1fs cur=%.1fs delta=%+.1fs "
                     "slack=%.2fs %s"
                     % (label, base, cur_s, cur_s - base, slack,
                        "FLAG" if over else "OK"))
    for label in sorted(base_map):
        if label not in cur_map:
            lines.append("suite %s REMOVED-SUITE (absent in current "
                         "run)" % label)
    shared = [l for l in base_map if l in cur_map]
    base_shared = sum(base_map[l] for l in shared)
    cur_shared = sum(cur_map[l] for l in shared)
    slack_t = drift_slack(base_shared)
    over_t = cur_shared > base_shared + slack_t
    if over_t:
        flagged.append("TOTAL-SHARED")
    lines.append("total-shared base=%.1fs cur=%.1fs delta=%+.1fs "
                 "slack=%.2fs %s (shared=%d labels)"
                 % (base_shared, cur_shared, cur_shared - base_shared,
                    slack_t, "FLAG" if over_t else "OK", len(shared)))
    # R1737 AC-SN4 (pre-registered): sentinel-segment drift, same
    # threshold family as suites (drift iff cur > base +
    # max(2.0s, 0.5*base)). Three states: both present -> compare;
    # current-only -> NEW-SEGMENT info (NEW-SUITE family, never a
    # flag); baseline-only -> ABSENT info (pre-R1737 log, never a
    # flag). Both absent -> no line (legacy output byte-identical).
    cur_sent = cur.get("sentinel_seconds")
    base_sent = baseline.get("sentinel_seconds")
    if cur_sent is not None and base_sent is not None:
        slack_s = drift_slack(base_sent)
        over_s = cur_sent > base_sent + slack_s
        if over_s:
            flagged.append("SENTINEL-SEGMENT")
        lines.append("sentinel-segment base=%.1fs cur=%.1fs "
                     "delta=%+.1fs slack=%.2fs %s"
                     % (base_sent, cur_sent, cur_sent - base_sent,
                        slack_s, "FLAG" if over_s else "OK"))
    elif cur_sent is not None:
        lines.append("sentinel-segment %.1fs NEW-SEGMENT (no baseline "
                     "entry)" % cur_sent)
    elif base_sent is not None:
        lines.append("sentinel-segment ABSENT (pre-R1737 log)")
    if flagged:
        lines.append("verdict: DRIFT-FLAG (%d flagged: %s)"
                     % (len(flagged), ", ".join(sorted(flagged))))
    else:
        lines.append("verdict: DRIFT-CLEAN (%d compared, 0 flagged)"
                     % compared)
    return "\n".join(lines) + "\n", flagged


def baseline_dict(data):
    rel = os.path.relpath(data["path"], REPO).replace(os.sep, "/")
    out = {
        "source_log": rel,
        "runner_line": data["runner_line"],
        "suites_count": len(data["suites"]),
        "criteria_total": data["criteria_total"],
        "suite_seconds_sum": data["seconds_sum"],
        "runner_total": data["runner_total"],
        "suite_seconds": dict((s["label"], s["seconds"])
                              for s in data["suites"]),
    }
    # R1737 AC-SN5: key present only when the source log carried the
    # elapsed-form sentinel tail - existing baselines (written from
    # legacy or main-face logs) round-trip byte-identically under
    # --check with zero re-freezing.
    if data.get("sentinel_seconds") is not None:
        out["sentinel_seconds"] = data["sentinel_seconds"]
    return out


def baseline_bytes(data):
    return (json.dumps(baseline_dict(data), indent=2, sort_keys=True)
            + "\n").encode("ascii")


def load_baseline(path=None):
    if path is None:
        path = baseline_path(False)
    if not os.path.exists(path):
        raise Refusal("baseline missing: %s (run --update-baseline)"
                      % path)
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("ascii"))


def _write_fixture(dirpath, name, seconds_map, runner_count):
    """Synthetic evidence fixture for --selftest (temp dir only)."""
    total = sum(seconds_map.values())
    lines = []
    for label in sorted(seconds_map):
        lines.append("PASS suite %s exit=0 pass-lines=0 fail-lines=0 "
                     "criteria=0 %.1fs" % (label, seconds_map[label]))
    lines.append("RUNNER PASS (%d/%d suites green, reconcile controls "
                 "6/6, %.1fs)" % (runner_count, runner_count, total))
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def hygiene_report():
    """ASCII self-scan + real import-line scan (R1678 lesson: scan
    actual import statements, not string literals)."""
    with open(__file__, "rb") as handle:
        raw = handle.read()
    problems = []
    if max(raw) >= 128:
        problems.append("non-ascii byte in source")
    banned = ("urllib", "requests", "socket", "http", "subprocess")
    for line in raw.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for word in banned:
                if word in stripped:
                    problems.append("network/process import: %s"
                                    % stripped)
    return problems


def selftest():
    problems = []
    hyg = hygiene_report()
    print("selftest hygiene: %s"
          % ("PASS" if not hyg else "FAIL %s" % hyg))
    if hyg:
        problems.extend(hyg)
    baseline = load_baseline()
    base_map = dict(baseline["suite_seconds"])
    lobby_base = base_map.get("lobby")
    if lobby_base is None:
        print("selftest drift-demo: FAIL (no lobby entry in baseline)")
        problems.append("no lobby baseline")
    else:
        tmp = tempfile.mkdtemp(prefix="runner-profile-selftest-")
        try:
            slack = drift_slack(lobby_base)
            edge = lobby_base + slack
            # fixture 1: lobby inflated past slack + one new suite
            f1 = dict(base_map)
            f1["lobby"] = edge + 0.05
            f1["selftest-new"] = 1.0
            path1 = _write_fixture(tmp, "drift.log", f1,
                                   len(f1))
            text, flagged = render_compare(parse_log(path1), baseline)
            sys.stdout.write(text)
            if "DRIFT-FLAG" not in text or "lobby" not in flagged \
                    or "selftest-new" not in text \
                    or "NEW-SUITE" not in text:
                problems.append("drift fixture not flagged as expected")
            print("selftest drift-demo (edge+0.05 + new-suite): %s"
                  % ("PASS" if "lobby" in flagged else "FAIL"))
            # fixture 2: lobby exactly at the boundary -> inclusive OK
            f2 = dict(base_map)
            f2["lobby"] = edge
            path2 = _write_fixture(tmp, "edge.log", f2, len(f2))
            text2, flagged2 = render_compare(parse_log(path2),
                                             baseline)
            if flagged2 or "DRIFT-CLEAN" not in text2:
                problems.append("boundary fixture flagged unexpectedly")
            print("selftest boundary (cur==base+slack -> OK): %s"
                  % ("PASS" if not flagged2 else "FAIL"))
            # fixture 3: clean copy -> DRIFT-CLEAN
            path3 = _write_fixture(tmp, "clean.log", base_map,
                                   len(base_map))
            text3, flagged3 = render_compare(parse_log(path3),
                                             baseline)
            if flagged3 or "DRIFT-CLEAN" not in text3:
                problems.append("clean fixture flagged unexpectedly")
            print("selftest clean-demo: %s"
                  % ("PASS" if not flagged3 else "FAIL"))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
    # render determinism: same input -> byte-identical output
    data = discover_target()
    if render_profile(data) != render_profile(data):
        problems.append("render_profile not deterministic")
    if render_compare(data, baseline)[0] != \
            render_compare(data, baseline)[0]:
        problems.append("render_compare not deterministic")
    print("selftest render-determinism: %s"
          % ("PASS" if not problems or "determinism" not in
             ";".join(problems) else "FAIL"))
    if problems:
        print("selftest verdict: FAIL (%d problems)" % len(problems))
        return 1
    print("selftest verdict: PASS")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(
        description="reconcile_all wall-time profile + drift tracker")
    parser.add_argument("--log", help="explicit evidence log target")
    parser.add_argument("--daily", action="store_true",
                        help="daily-variant face: discovery restricted "
                             "to reconcile-daily-*.log evidence; "
                             "baseline kept separately in "
                             "runner-profile-daily-baseline.json")
    parser.add_argument("--update-baseline", action="store_true",
                        help="(re)write the face's baseline file")
    parser.add_argument("--check", action="store_true",
                        help="stale-baseline detector (byte compare vs "
                             "recorded source log)")
    parser.add_argument("--selftest", action="store_true",
                        help="hygiene + synthetic drift demo")
    parser.add_argument("--out", help="append a utf-8 evidence copy "
                        "of stdout to this path")
    args = parser.parse_args(argv[1:])

    tee = None
    if args.out:
        tee = open(args.out, "a", encoding="utf-8", newline="\n")
        real = sys.stdout

        class _Tee(object):
            def write(self, data):
                tee.write(data)
                real.write(data)

            def flush(self):
                tee.flush()
                real.flush()
        sys.stdout = _Tee()

    try:
        bpath = baseline_path(args.daily)
        if args.selftest:
            return selftest()
        if args.check:
            baseline = load_baseline(bpath)
            data = parse_log(os.path.join(REPO, baseline["source_log"]))
            ok = baseline_bytes(data) == open(bpath, "rb").read()
            print("== stale-baseline check ==")
            print("baseline source: %s" % baseline["source_log"])
            print("check: %s"
                  % ("byte-identical PASS" if ok else
                     "STALE/DIVERGED (regenerate with --update-baseline)"))
            return 0 if ok else 2
        if args.daily:
            print("face: daily (population: reconcile-daily-*.log)")
        data = parse_log(args.log) if args.log else (
            discover_daily() if args.daily else discover_target())
        out = render_profile(data)
        sys.stdout.write(out)
        if args.update_baseline:
            with open(bpath, "wb") as handle:
                handle.write(baseline_bytes(data))
            rel = os.path.relpath(bpath, REPO)
            print("baseline written: %s (source: %s, suites=%d)"
                  % (rel.replace(os.sep, "/"),
                     os.path.relpath(data["path"], REPO).replace(os.sep,
                                                                "/"),
                     len(data["suites"])))
            return 0
        if not os.path.exists(bpath):
            print("baseline: ABSENT (init with --update-baseline)")
            return 0
        text, flagged = render_compare(data, load_baseline(bpath))
        sys.stdout.write(text)
        return 2 if flagged else 0
    except Refusal as exc:
        print("REFUSAL: %s" % exc)
        return 3
    finally:
        if tee is not None:
            sys.stdout.flush()
            tee.close()
            sys.stdout = real


if __name__ == "__main__":
    sys.exit(main(sys.argv))
