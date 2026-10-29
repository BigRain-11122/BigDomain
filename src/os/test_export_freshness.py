"""Export-freshness suite (R2250; criteria AC-EXP1..AC-EXP6 were
pre-registered in state/queue/tech.md as the R2240-d seed BEFORE this
code existed - honesty law).

What this proves: the CEO-visible face is judged on the axis nothing
measured before, time. Shape and derivation belong to
check_export_consistency; this suite holds only the age gate and the
48h milestone window, with an honest unknown when no due stamp is
published rather than a fabricated pass. The clock is injected, so
every reading here is reproducible.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import datetime
import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import export_freshness as EF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_freshness.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-export-freshness"

PASSES = 0
FAILS = 0

NOW = datetime.datetime(2026, 10, 29, 12, 0, 0,
                        tzinfo=datetime.timezone.utc)


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def iso(hours_from_now):
    stamp = NOW + datetime.timedelta(hours=hours_from_now)
    return stamp.isoformat()


def face(export_hours_ago=1.0, due_hours_from_export=20.0, drop_due=False,
         blank=None):
    """Build one export document in a fresh temp dir; return its path."""
    world = tempfile.mkdtemp(prefix="bigdomain-exp-")
    body = {
        "export_ts": iso(-export_hours_ago),
        "ceo_face": {
            "current": "window in flight",
            "latest_artifact": "qa/some-evidence.log",
            "next_milestone": "next window within the gate",
        },
    }
    if not drop_due:
        body["ceo_face"]["next_milestone_due"] = iso(
            -export_hours_ago + due_hours_from_export)
    if blank:
        body["ceo_face"][blank] = "   "
    path = os.path.join(world, "status-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(body, ensure_ascii=False, indent=2))
    return path


def expect_error(call, code):
    try:
        call()
    except EF.ExportFreshnessError as exc:
        return exc.code == code
    return False


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def wiring_ok():
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        text = handle.read()
    needle = '"%s"' % LABEL
    if needle not in text:
        return False
    tail = text[text.find(needle):]
    window = tail[:400]
    return ("test_export_freshness.py" in window) and (", 6)" in window)


def ac1_three_lines():
    good = EF.assess(face(), NOW)
    missing = face(blank="current")
    refused = expect_error(lambda: EF.assess(missing, NOW), "E_EXP_BAD_FACE")
    empty = tempfile.mkdtemp(prefix="bigdomain-exp-")
    path = os.path.join(empty, "status-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"export_ts": iso(0), "ceo_face": {}}))
    bare = expect_error(lambda: EF.assess(path, NOW), "E_EXP_BAD_FACE")
    return (good["three_lines"] == {k: True for k in EF.FACE_KEYS}
            and refused and bare)


def ac2_iso8601():
    good = EF.assess(face(export_hours_ago=3.0), NOW)
    age_ok = good["age_hours"] == 3.0
    zulu = EF.parse_ts("2026-10-29T04:00:00Z", "t")
    zulu_ok = zulu.utcoffset().total_seconds() == 0
    naive = expect_error(lambda: EF.parse_ts("2026-10-29T04:00:00", "t"),
                         "E_EXP_BAD_TS")
    junk = expect_error(lambda: EF.parse_ts("not-a-time", "t"),
                        "E_EXP_BAD_TS")
    world = tempfile.mkdtemp(prefix="bigdomain-exp-")
    path = os.path.join(world, "status-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({
            "export_ts": "2026-10-29T04:00:00",
            "ceo_face": {"current": "c", "latest_artifact": "a",
                         "next_milestone": "m"},
        }))
    naive_file = expect_error(lambda: EF.assess(path, NOW), "E_EXP_BAD_TS")
    return age_ok and zulu_ok and naive and junk and naive_file


def ac3_window():
    inside = EF.assess(face(due_hours_from_export=30.0), NOW)
    far = EF.assess(face(due_hours_from_export=60.0), NOW)
    past = EF.assess(face(due_hours_from_export=0.0), NOW)
    unknown = EF.assess(face(drop_due=True), NOW)
    return (inside["verdict"] == "FRESH"
            and inside["milestone_window_hours"] == 30.0
            and far["verdict"] == "STALE-WINDOW"
            and far["milestone_window_hours"] == 60.0
            and past["verdict"] == "STALE-WINDOW"
            and unknown["verdict"] == "UNVERIFIABLE-WINDOW"
            and unknown["milestone_window_hours"] is None)


def ac4_stale_verdict():
    fresh = EF.assess(face(export_hours_ago=2.0), NOW)
    stale = EF.assess(face(export_hours_ago=30.0), NOW)
    tight = EF.assess(face(export_hours_ago=6.0), NOW, age_gate_hours=4.0)
    verdicts = set(EF.VERDICTS)
    return (fresh["verdict"] == "FRESH"
            and stale["verdict"] == "STALE-FACE"
            and "E_EXP_STALE_FACE" in stale["errors"]
            and tight["verdict"] == "STALE-FACE"
            and fresh["verdict"] in verdicts
            and len(verdicts) == 4)


def ac5_cli():
    good_rc, _ = run_cli(["--check", "--export", face(), "--now", iso(0)])
    stale_rc, _ = run_cli(["--check", "--export", face(export_hours_ago=40.0),
                           "--now", iso(0)])
    missing_rc, _ = run_cli(["--check", "--export",
                             os.path.join(tempfile.mkdtemp(), "nope.json"),
                             "--now", iso(0)])
    unknown_rc, _ = run_cli(["--check", "--export", face(drop_due=True),
                             "--now", iso(0)])
    bad_rc, _ = run_cli(["--check", "--bogus"])
    json_rc, body = run_cli(["--check", "--export", face(), "--now", iso(0),
                             "--json"])
    keys = list(json.loads(body).keys()) if json_rc == 0 else []
    return (good_rc == 0 and stale_rc == 2 and missing_rc == 3
            and unknown_rc == 4 and bad_rc == 5
            and keys == list(EF.REPORT_KEYS))


def ac6_purity():
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = all(byte < 128 for byte in raw)
    with io.open(MODULE, "r", encoding="ascii") as handle:
        text = handle.read()
    no_clock = "datetime.now(" not in text.replace("datetime.datetime.now(", "")
    pure = ("import urllib" not in text and "import socket" not in text
            and "requests" not in text and "open(" not in text.replace(
                'open(path, "rb")', ""))
    live = os.path.join(os.path.dirname(SRC), "docs", "status-export.json")
    report = EF.assess(live, NOW)
    line = EF.one_line(report)
    live_ok = (report["present"] and "verdict=" in line
               and report["verdict"] in EF.VERDICTS)
    return ascii_ok and no_clock and pure and live_ok and wiring_ok()


def run():
    check(ac1_three_lines(), "AC-EXP1 ceo_face publishes three non-empty lines or refuses")
    check(ac2_iso8601(), "AC-EXP2 stamps need an explicit UTC offset and the age is measured")
    check(ac3_window(), "AC-EXP3 the 48h milestone window is judged, absent due reads unknown")
    check(ac4_stale_verdict(), "AC-EXP4 the age gate flips the verdict to STALE-FACE")
    check(ac5_cli(), "AC-EXP5 CLI exits 0/2/3/4/5 and --json keeps the pinned key order")
    check(ac6_purity(), "AC-EXP6 source is ASCII, clock-free, read-only and runner-wired")


if __name__ == "__main__":
    run()
    print("SUITE %s %d/%d" % (
        "PASS" if FAILS == 0 else "FAIL", PASSES + FAILS, EXPECTED_CRITERIA),
        flush=True)
    sys.exit(0 if FAILS == 0 else 2)