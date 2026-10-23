"""Acceptance suite for the funnel evidence overwrite / rotation law
(FUNNEL-LOOP v0.1, R2062).

Pre-registered criteria AC-FCR1..AC-FCR8 live in state/queue/tech.md
(the R2062 claim row) and were written BEFORE this suite or any
product change existed (honesty law). The gap under test is the one
the R2056 reseed row named: the CLI --evidence face opened its target
with mode "w", so a caller reusing the same path across days silently
lost the earlier day's bytes, and there was no way to ask for one file
per day. Nothing was pinned about that overwrite semantics.

The law now under test: a path WITHOUT braces keeps the historical
single-file face (each run rewrites that one file; never an
accumulating log). A path carrying the literal {day} token exactly
once is the rotating per-day face (the token expands to the
caller-injected --day, so a multi-day chain keeps one file per day).
Any other brace form rejects as E_FN_BAD_ARGS before the wiring layer
creates any directory (zero disk artifacts).

The library is exercised as shipped. Pure ASCII source (coding law).
"""

import ast
import contextlib
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402

DAY_A = "2026-10-23"
DAY_B = "2026-10-24"


def _world(root):
    return {
        "root": root,
        "db": os.path.join(root, "dbdir", "funnel.db"),
        "leads": os.path.join(root, "inbox", "leads"),
        "orders": os.path.join(root, "inbox", "orders"),
        "flows": os.path.join(root, "inbox", "flows"),
    }


def _put(d, rows):
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w",
                  encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _seed(w):
    _put(w["leads"], [{"lead_id": "L1", "source": "s",
                       "text": "I want a game demo level"}])
    _put(w["orders"], [{"order_id": "O1", "sku": "compute-pack-19.9",
                        "amount_cent": 1990}])
    _put(w["flows"], [{"flow_id": "F1", "account": "u1", "kind": "grant",
                       "amount": 100},
                      {"flow_id": "F2", "account": "u1", "kind": "spend",
                       "amount": 30}])


def _cli(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = fd.main(list(argv))
    return rc, out.getvalue()


def _argv(w, day, evidence=None):
    argv = ["--day", day, "--db", w["db"],
            "--leads-inbox", w["leads"],
            "--orders-inbox", w["orders"],
            "--flows-inbox", w["flows"],
            "--config", fd.DEFAULT_CONFIG]
    if evidence is not None:
        argv += ["--evidence", evidence]
    return argv


def _bytes(path):
    with open(path, "rb") as h:
        return h.read()


def _tmp(tmp, name):
    root = os.path.join(tmp, name)
    os.makedirs(root)
    return _world(root)


def case_fcr1(tmp):
    """AC-FCR1: the overwrite first-proof - the same --evidence path
    reused across two days ends up holding exactly the second run's
    bytes (the first day's marker is gone, no append, one trailing
    newline)."""
    w = _tmp(tmp, "fcr1")
    _seed(w)
    ev = os.path.join(w["root"], "ev", "evidence.log")
    rc_a, out_a = _cli(_argv(w, DAY_A, ev))
    assert rc_a == 0, "AC-FCR1 day A must exit 0 (got %r)" % (rc_a,)
    first = _bytes(ev)
    assert first == out_a.encode("utf-8"), "AC-FCR1 run A self-tee"
    rc_b, out_b = _cli(_argv(w, DAY_B, ev))
    assert rc_b == 0, "AC-FCR1 day B must exit 0 (got %r)" % (rc_b,)
    second = _bytes(ev)
    assert second == out_b.encode("utf-8"), (
        "AC-FCR1 same path must hold the second run's bytes")
    assert ("day=%s" % DAY_A).encode() not in second, (
        "AC-FCR1 day-A marker must be gone (overwrite, not append)")
    assert second.count(b"FUNNEL-DAILY day=") == 1, (
        "AC-FCR1 exactly one run payload may remain")
    assert second.endswith(b"\n") and not second.endswith(b"\n\n"), (
        "AC-FCR1 exactly one trailing newline")


def case_fcr2(tmp):
    """AC-FCR2: the per-day rotation face - a {day} template writes
    two files whose bytes are each run's stdout, and the second day
    never touches the first day's file."""
    w = _tmp(tmp, "fcr2")
    _seed(w)
    tmpl = os.path.join(w["root"], "ev", "funnel-{day}.log")
    rc_a, out_a = _cli(_argv(w, DAY_A, tmpl))
    assert rc_a == 0, "AC-FCR2 day A must exit 0 (got %r)" % (rc_a,)
    ev_a = tmpl.replace("{day}", DAY_A)
    ev_b = tmpl.replace("{day}", DAY_B)
    assert os.path.exists(ev_a), "AC-FCR2 day-A file must exist"
    before = _bytes(ev_a)
    assert before == out_a.encode("utf-8"), "AC-FCR2 day-A self-tee"
    rc_b, out_b = _cli(_argv(w, DAY_B, tmpl))
    assert rc_b == 0, "AC-FCR2 day B must exit 0 (got %r)" % (rc_b,)
    assert os.path.exists(ev_b), "AC-FCR2 day-B file must exist"
    assert _bytes(ev_b) == out_b.encode("utf-8"), "AC-FCR2 day-B self-tee"
    assert _bytes(ev_a) == before, (
        "AC-FCR2 rotation must preserve the earlier day's bytes")
    assert os.path.exists(tmpl) is False, (
        "AC-FCR2 the raw template path must never be created")


def case_fcr3(tmp):
    """AC-FCR3: the no-brace path keeps the historical single-file
    face and the stdout face is byte-identical with or without
    --evidence (same world paths, both runs from a fresh carrier)."""
    w = _tmp(tmp, "fcr3")
    _seed(w)
    rc_plain, out_plain = _cli(_argv(w, DAY_A))
    assert rc_plain == 0, "AC-FCR3 plain run must exit 0"
    # Reset the carrier only (same paths, same day, same seeds) so the
    # two stdout faces are comparable byte for byte.
    os.remove(w["db"])
    for d in (w["leads"], w["orders"], w["flows"]):
        for name in os.listdir(d):
            os.remove(os.path.join(d, name))
    _seed(w)
    ev = os.path.join(w["root"], "ev", "plain.log")
    rc_ev, out_ev = _cli(_argv(w, DAY_A, ev))
    assert rc_ev == 0, "AC-FCR3 evidenced run must exit 0"
    assert out_ev == out_plain, (
        "AC-FCR3 stdout must not gain or lose bytes with --evidence")
    assert _bytes(ev) == out_ev.encode("utf-8"), "AC-FCR3 self-tee"
    assert os.listdir(os.path.dirname(ev)) == ["plain.log"], (
        "AC-FCR3 no-brace path makes exactly one file")


def case_fcr4(tmp):
    """AC-FCR4: bad placeholder forms reject as one clean
    E_FN_BAD_ARGS line with exit 2 and zero disk artifacts (the
    reject is ordered before the wiring layer creates directories)."""
    forms = ["ev-{date}.log", "ev-{DAY}.log", "ev-{day}{day}.log",
             "ev-{day.log", "ev-day}.log"]
    for i, form in enumerate(forms):
        w = _tmp(tmp, "fcr4-%d" % i)
        ev = os.path.join(w["root"], "ev", form)
        rc, out = _cli(_argv(w, DAY_A, ev))
        assert rc == 2, "AC-FCR4 %r must exit 2 (got %r)" % (form, rc)
        assert out.strip() == fd.E_FN_BAD_ARGS, (
            "AC-FCR4 %r must be ONE clean reject line, got %r" % (form, out))
        assert "Traceback" not in out, "AC-FCR4 no traceback may escape"
        assert not os.path.exists(w["db"]), (
            "AC-FCR4 %r zero db file" % (form,))
        assert not os.path.exists(w["leads"]), (
            "AC-FCR4 %r zero inbox creation" % (form,))
        assert not os.path.exists(os.path.join(w["root"], "ev")), (
            "AC-FCR4 %r zero evidence dir" % (form,))


def case_fcr5(tmp):
    """AC-FCR5: an empty --evidence string means "no evidence" - the
    run follows the gate law and no artifact appears."""
    w = _tmp(tmp, "fcr5")
    _seed(w)
    rc, out = _cli(_argv(w, DAY_A, ""))
    assert rc == 0, "AC-FCR5 empty string must not disturb the gate"
    assert "FUNNEL-DAILY day=" in out, "AC-FCR5 normal face must print"
    assert not os.path.exists(os.path.join(w["root"], "ev")), (
        "AC-FCR5 empty evidence string creates nothing")


def case_fcr6(tmp):
    """AC-FCR6: the zero-append machine check - the module has no
    append-mode open() at all, the evidence write is mode "w", and a
    same-path second run does not double the file size."""
    source = open(os.path.join(BASE, "funnel_daily.py"),
                  encoding="utf-8").read()
    tree = ast.parse(source)
    modes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            fn = node.func
            name = getattr(fn, "id", getattr(fn, "attr", ""))
            if name != "open":
                continue
            consts = [a.value for a in node.args
                      if isinstance(a, ast.Constant)
                      and isinstance(a.value, str)]
            modes.extend(consts)
    assert "a" not in modes and "a+" not in modes and "ab" not in modes, (
        "AC-FCR6 no append-mode open() may exist: %r" % (modes,))
    assert "w" in modes, "AC-FCR6 the evidence write must use mode w"
    w = _tmp(tmp, "fcr6")
    _seed(w)
    ev = os.path.join(w["root"], "ev", "same.log")
    rc1, out1 = _cli(_argv(w, DAY_A, ev))
    assert rc1 == 0, "AC-FCR6 first run must exit 0"
    size1 = os.path.getsize(ev)
    assert size1 == len(out1.encode("utf-8")), (
        "AC-FCR6 file size == payload bytes")
    rc2, out2 = _cli(_argv(w, DAY_B, ev))
    assert rc2 == 0, "AC-FCR6 second run must exit 0"
    size2 = os.path.getsize(ev)
    assert size2 == len(out2.encode("utf-8")), (
        "AC-FCR6 second run size == its own payload (never doubled)")


def case_fcr7(tmp):
    """AC-FCR7: the evidence bytes are utf-8, BOM-free, LF-only and
    carry exactly one trailing newline."""
    w = _tmp(tmp, "fcr7")
    _seed(w)
    ev = os.path.join(w["root"], "ev", "dialect.log")
    rc, out = _cli(_argv(w, DAY_A, ev))
    assert rc == 0, "AC-FCR7 run must exit 0"
    raw = _bytes(ev)
    assert not raw.startswith(b"\xef\xbb\xbf"), "AC-FCR7 no BOM"
    assert b"\r" not in raw, "AC-FCR7 no CR bytes"
    text = raw.decode("utf-8")
    assert text == out, "AC-FCR7 self-tee byte equality"
    assert text.endswith("\n") and not text.endswith("\n\n"), (
        "AC-FCR7 exactly one trailing newline")


def case_fcr8(tmp):
    """AC-FCR8: hygiene - the source stays pure ASCII and the shipped
    config is not written by this suite."""
    src = _bytes(os.path.join(BASE, "funnel_daily.py"))
    assert all(b < 128 for b in src), "AC-FCR8 source must stay ASCII"
    cfg = _bytes(os.path.join(BASE, "config.json"))
    assert cfg, "AC-FCR8 shipped config must exist"
    w = _tmp(tmp, "fcr8")
    _seed(w)
    ev = os.path.join(w["root"], "ev", "hygiene.log")
    rc, _out = _cli(_argv(w, DAY_A, ev))
    assert rc == 0, "AC-FCR8 run must exit 0"
    assert _bytes(os.path.join(BASE, "config.json")) == cfg, (
        "AC-FCR8 shipped config bytes must not change")


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-evidence-rotate-")
    cases = [
        ("AC-FCR1 same-path overwrite first-proof", case_fcr1),
        ("AC-FCR2 {day} per-day rotation", case_fcr2),
        ("AC-FCR3 no-brace face zero drift", case_fcr3),
        ("AC-FCR4 bad placeholder fail-closed", case_fcr4),
        ("AC-FCR5 empty evidence means absent", case_fcr5),
        ("AC-FCR6 zero-append machine check", case_fcr6),
        ("AC-FCR7 evidence dialect", case_fcr7),
        ("AC-FCR8 hygiene", case_fcr8),
    ]
    failed = 0
    for name, fn in cases:
        try:
            fn(tmp)
        except AssertionError as exc:
            failed += 1
            print("FAIL %s: %s" % (name, exc))
        else:
            print("PASS %s" % name)
    print("SUITE %s %d/%d" % ("FAIL" if failed else "PASS",
                              len(cases) - failed, len(cases)))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())