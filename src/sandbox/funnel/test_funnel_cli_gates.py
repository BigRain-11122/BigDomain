"""Acceptance suite for the funnel CLI bad-args gate family
(AC-FCG1..AC-FCG7, R2048 tech-queue FIFO head claim).

The criteria were pre-registered in state/queue/tech.md (R2048 claim
row) BEFORE the funnel_daily.py main() fix and BEFORE this suite
existed (honesty law). This suite runs the CLI face IN-PROCESS
(fd.main(argv) returns the exit code; argparse boundary raises
SystemExit) - every world is a fresh tmp carrier with explicit
--db/--inbox paths, so the real state/funnel face is never touched.
Pure ASCII source: the injected banned word uses a unicode escape
(coding law, test_funnel_daily.py case_fn6 pattern).
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w", encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _empty_inbox(root, name):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    return d


def _cli(argv):
    """Run fd.main() in-process; return (exit_code, stdout_text)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = fd.main(list(argv))
    return rc, out.getvalue()


def _cli_sysexit(argv):
    """Run fd.main() expecting the argparse SystemExit boundary."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            fd.main(list(argv))
        except SystemExit as exc:
            return exc.code, out.getvalue(), err.getvalue()
    raise AssertionError("parser boundary must raise SystemExit")


def _paths(root):
    return (
        os.path.join(root, "dbdir", "funnel.db"),
        os.path.join(root, "inbox", "leads"),
        os.path.join(root, "inbox", "orders"),
        os.path.join(root, "inbox", "flows"),
    )


def _assert_single_clean_line(out):
    assert out.strip() == fd.E_FN_BAD_ARGS, (
        "reject must be ONE clean line, got %r" % (out,))
    assert "Traceback" not in out, "no traceback may reach the CLI face"


def case_fcg1(tmp):
    """AC-FCG1: the bad-day family exits 2 with one clean
    E_FN_BAD_ARGS line and leaves ZERO disk artifacts."""
    root = os.path.join(tmp, "fcg1")
    os.makedirs(root)
    db, li, oi, fi = _paths(root)
    ev = os.path.join(root, "ev", "evidence.log")
    for day in ("2026-99-99", "2026-13-01", "not-a-date", ""):
        rc, out = _cli(["--day", day, "--db", db, "--leads-inbox", li,
                        "--orders-inbox", oi, "--flows-inbox", fi,
                        "--config", fd.DEFAULT_CONFIG, "--evidence", ev])
        assert rc == 2, "AC-FCG1 bad day %r must exit 2 (got %r)" % (day, rc)
        _assert_single_clean_line(out)
        assert not os.path.exists(db), "AC-FCG1 no db file for %r" % (day,)
        assert not os.path.exists(li), "AC-FCG1 no leads inbox for %r" % (day,)
        assert not os.path.exists(oi), "AC-FCG1 no orders inbox for %r" % (day,)
        assert not os.path.exists(fi), "AC-FCG1 no flows inbox for %r" % (day,)
        assert not os.path.exists(ev), "AC-FCG1 no evidence file for %r" % (day,)


def case_fcg2(tmp):
    """AC-FCG2: the argparse required-arg boundary - missing --day
    exits 2 with the usage face and zero disk artifacts."""
    root = os.path.join(tmp, "fcg2")
    os.makedirs(root)
    db, li, oi, fi = _paths(root)
    code, out, err = _cli_sysexit(["--db", db, "--leads-inbox", li,
                                   "--orders-inbox", oi, "--flows-inbox", fi])
    assert code == 2, "AC-FCG2 parser boundary must exit 2 (got %r)" % (code,)
    assert "usage:" in err, "AC-FCG2 usage face must print to stderr"
    assert not os.path.exists(db), "AC-FCG2 zero disk artifacts"


def case_fcg3(tmp):
    """AC-FCG3: the --evidence path pre-gate - an uncreatable evidence
    dirname (parent is an existing regular file) rejects cleanly with
    zero db rows and no evidence file."""
    root = os.path.join(tmp, "fcg3")
    os.makedirs(root)
    plain = os.path.join(root, "plainfile")
    with open(plain, "wb") as h:
        h.write(b"x")
    ev = os.path.join(plain, "ev.log")  # dirname == a regular file
    db, li, oi, fi = _paths(root)
    rc, out = _cli(["--day", "2026-10-20", "--db", db, "--leads-inbox", li,
                    "--orders-inbox", oi, "--flows-inbox", fi,
                    "--config", fd.DEFAULT_CONFIG, "--evidence", ev])
    assert rc == 2, "AC-FCG3 uncreatable evidence dir must exit 2"
    _assert_single_clean_line(out)
    assert not os.path.exists(db), "AC-FCG3 zero db file (rings never ran)"
    assert not os.path.exists(ev), "AC-FCG3 no evidence file"


def case_fcg4(tmp):
    """AC-FCG4: the inbox path pre-gate - an inbox argument pointing
    at an existing regular file rejects cleanly before the carrier
    opens (no db file)."""
    root = os.path.join(tmp, "fcg4")
    os.makedirs(root)
    plain = os.path.join(root, "regularfile")
    with open(plain, "wb") as h:
        h.write(b"x")
    db, _li, oi, fi = _paths(root)
    rc, out = _cli(["--day", "2026-10-20", "--db", db, "--leads-inbox", plain,
                    "--orders-inbox", oi, "--flows-inbox", fi,
                    "--config", fd.DEFAULT_CONFIG])
    assert rc == 2, "AC-FCG4 inbox-as-file must exit 2"
    _assert_single_clean_line(out)
    assert not os.path.exists(db), "AC-FCG4 zero db file"


def case_fcg5(tmp):
    """AC-FCG5: good-path control - a valid day on a one-lead /
    one-order / two-flow world exits 0; the evidence file is
    byte-identical to the stdout block (self-tee law), LF utf-8
    single dialect, gate=PASS with the four-ring counts booked."""
    root = os.path.join(tmp, "fcg5")
    os.makedirs(root)
    li = _mk_inbox(root, "leads",
                   [{"lead_id": "L1", "source": "s",
                     "text": "I want a game demo level"}])
    oi = _mk_inbox(root, "orders",
                   [{"order_id": "O1", "sku": "compute-pack-19.9",
                     "amount_cent": 1990}])
    fi = _mk_inbox(root, "flows",
                   [{"flow_id": "F1", "account": "u1", "kind": "grant",
                     "amount": 100},
                    {"flow_id": "F2", "account": "u1", "kind": "spend",
                     "amount": 30}])
    ev = os.path.join(root, "ev", "ok.log")
    rc, out = _cli(["--day", "2026-10-20", "--db",
                    os.path.join(root, "funnel.db"), "--leads-inbox", li,
                    "--orders-inbox", oi, "--flows-inbox", fi,
                    "--config", fd.DEFAULT_CONFIG, "--evidence", ev])
    assert rc == 0, "AC-FCG5 good path must exit 0 (got %r)" % (rc,)
    raw = open(ev, "rb").read()
    assert b"\r" not in raw, "AC-FCG5 evidence must be LF single dialect"
    assert raw.decode("utf-8") == out, "AC-FCG5 self-tee: evidence == stdout"
    env_line = [ln for ln in out.splitlines() if ln.startswith("envelope ")]
    assert env_line, "AC-FCG5 envelope line must print"
    env = json.loads(env_line[0][len("envelope "):])
    assert env["gate"] == "PASS", "AC-FCG5 clean world must gate PASS"
    c = env["counts"]
    assert (c["leads_day"], c["dispatches_day"], c["orders_day"],
            c["token_granted_day"], c["token_spent_day"],
            c["token_outstanding_total"]) == (1, 1, 1, 100, 30, 70), (
        "AC-FCG5 four-ring counts mismatch: %r" % (c,))


def case_fcg6(tmp):
    """AC-FCG6: the gate-FAIL exit law survives the fix - a banned
    word in the presented envelope (suite-built config; the shipped
    config is never touched) exits 2 with the FULL envelope printed
    and the evidence file still written."""
    root = os.path.join(tmp, "fcg6")
    os.makedirs(root)
    li = _empty_inbox(root, "leads")
    oi = _empty_inbox(root, "orders")
    fi = _empty_inbox(root, "flows")
    bad_cfg = os.path.join(root, "bad-config.json")
    # "\u5347\u503c" = the banned word, unicode escape keeps ASCII.
    with open(bad_cfg, "w", encoding="utf-8") as h:
        json.dump({"banned_words": ["\u5347\u503c"],
                   "standing_lines": {"aigc": "x \u5347\u503c y"}}, h)
    ev = os.path.join(root, "ev", "fail.log")
    rc, out = _cli(["--day", "2026-10-20", "--db",
                    os.path.join(root, "funnel.db"), "--leads-inbox", li,
                    "--orders-inbox", oi, "--flows-inbox", fi,
                    "--config", bad_cfg, "--evidence", ev])
    assert rc == 2, "AC-FCG6 gate FAIL must stay exit 2 (got %r)" % (rc,)
    assert out.startswith("FUNNEL-DAILY day="), (
        "AC-FCG6 full envelope face must print, not a clean reject")
    assert "E_FN_BAD_ARGS" not in out, "AC-FCG6 FAIL is not a bad-args reject"
    assert "gate=FAIL" in out, "AC-FCG6 gate=FAIL line required"
    evtext = open(ev, "rb").read().decode("utf-8")
    assert "gate=FAIL" in evtext, "AC-FCG6 evidence must be written on FAIL"


def case_fcg7(tmp):
    """AC-FCG7: wiring confinement + zero-regression invariants - the
    library raise law is intact, the product source stays pure ASCII
    with zero wall-clock reads, the shipped config stays clean, and
    the library path still books through the untouched rings."""
    root = os.path.join(tmp, "fcg7")
    os.makedirs(root)
    try:
        fd._assert_day("not-a-date")
        raise AssertionError("AC-FCG7 library raise law broken")
    except fd.FunnArgError:
        pass
    fd._assert_day("2026-10-20")  # good day: no raise
    src = open(os.path.join(BASE, "funnel_daily.py"), "rb").read()
    assert all(b < 128 for b in src), "AC-FCG7 product source must stay ASCII"
    text = src.decode("ascii")
    for tok in ("time.time(", "datetime.now(", "utcnow("):
        assert tok not in text, "AC-FCG7 zero wall-clock law: %s" % tok
    li = _mk_inbox(root, "leads", [{"lead_id": "L1", "text": "game demo"}])
    oi = _empty_inbox(root, "orders")
    fi = _empty_inbox(root, "flows")
    f = fd.FunnelDaily(os.path.join(root, "funnel.db"),
                       config_path=fd.DEFAULT_CONFIG)
    out = f.run_daily(li, oi, fi, "2026-10-20")
    f.close()
    assert out["ring1"]["leads_new"] == 1, "AC-FCG7 library ring still books"
    assert out["envelope"]["gate"] == "PASS", "AC-FCG7 shipped config clean"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-cligates-")
    cases = [
        ("AC-FCG1 bad-day family clean fail-closed", case_fcg1),
        ("AC-FCG2 parser boundary SystemExit 2", case_fcg2),
        ("AC-FCG3 evidence-path pre-gate", case_fcg3),
        ("AC-FCG4 inbox-path pre-gate", case_fcg4),
        ("AC-FCG5 good-path control + self-tee", case_fcg5),
        ("AC-FCG6 gate-FAIL exit law preserved", case_fcg6),
        ("AC-FCG7 wiring confinement + zero regression", case_fcg7),
    ]
    failed = 0
    for name, fn in cases:
        try:
            fn(tmp)
            print("PASS %s" % name)
        except AssertionError as exc:
            failed += 1
            print("FAIL %s :: %s" % (name, exc))
    shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases)
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
