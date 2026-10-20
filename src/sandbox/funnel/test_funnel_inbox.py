"""Acceptance suite for the funnel inbox classification law
(FUNNEL-LOOP v0.1, R2057).

Pre-registered criteria AC-FIN1..AC-FIN8 live in state/queue/tech.md
(the R2057 claim row) and were written BEFORE this suite or any
product change existed (honesty law). The gap under test is the one
the R2052 reseed row named: the inbox loader only looked at the .json
suffix, so the boundary between junk (skip) and a bad in-contract file
(reject the whole ring) was never pinned - a directory named
"*.json" escaped as a raw IsADirectoryError, and bad JSON text escaped
as a raw JSONDecodeError instead of the library's E_FN_BAD_ARGS raise
family.

The law now under test: an inbox entry is a REGULAR FILE with the
exact lower-case .json suffix. Everything else is junk - skipped,
never opened, never recursed into. An in-contract file that cannot be
honoured rejects the whole ring with FunnArgError (zero new rows,
validation before writing), and no decoder error escapes the library.

The library is exercised as shipped. Pure ASCII source (coding law).
"""

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402

DAY = "2026-10-20"


def _world(tmp):
    root = tempfile.mkdtemp(prefix="funnel-inbox-", dir=tmp)
    return {
        "root": root,
        "db": os.path.join(root, "funnel.db"),
        "leads": os.path.join(root, "leads"),
        "orders": os.path.join(root, "orders"),
        "flows": os.path.join(root, "flows"),
    }


def _inbox(w, key):
    path = w[key]
    os.makedirs(path, exist_ok=True)
    return path


def _put(path, name, obj):
    with open(os.path.join(path, name), "w", encoding="utf-8") as h:
        json.dump(obj, h, ensure_ascii=False)


def _put_text(path, name, text):
    with open(os.path.join(path, name), "w", encoding="utf-8") as h:
        h.write(text)


def _put_raw(path, name, data):
    with open(os.path.join(path, name), "wb") as h:
        h.write(data)


def _count(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            "SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    finally:
        con.close()


def _expect_funarg(fn):
    """Every bad in-contract face must raise exactly FunnArgError."""
    try:
        fn()
    except fd.FunnArgError:
        return
    except Exception as exc:  # noqa: BLE001 - the leak is the failure
        raise AssertionError(
            "raw %s escaped the library boundary" % type(exc).__name__)
    raise AssertionError("bad inbox face was accepted")


def case_fin1(tmp):
    """AC-FIN1: junk files are skipped without ever being opened -
    their bytes are invalid UTF-8, so opening them would blow up."""
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.json", {"lead_id": "L1", "text": "game level demo"})
    _put_raw(d, "readme.txt", b"\xff\xfe\x00junk")
    _put_raw(d, "notes.md", b"\xff\xfe\x00junk")
    _put_raw(d, "data.json.bak", b"\xff\xfe\x00junk")
    _put_raw(d, "noext", b"\xff\xfe\x00junk")
    f = fd.FunnelDaily(w["db"])
    try:
        out = f.scan_leads(d, DAY)
    finally:
        f.close()
    assert out["files_leads"] == 1, "AC-FIN1 junk counted as inbox files"
    assert out["leads_seen"] == 1, "AC-FIN1 junk reached the seen count"
    assert out["leads_new"] == 1, "AC-FIN1 valid lead not booked"
    assert _count(w["db"], "leads") == 1, "AC-FIN1 leads row count"


def case_fin2(tmp):
    """AC-FIN2: directories are never inbox entries - including one
    whose name literally ends in .json - and nesting is never walked."""
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.json", {"lead_id": "L1", "text": "video clip script"})
    nested = os.path.join(d, "nested")
    os.makedirs(nested)
    _put(nested, "evil.json", {"lead_id": "L99", "text": "hidden"})
    os.makedirs(os.path.join(d, "fake.json"))
    f = fd.FunnelDaily(w["db"])
    try:
        out = f.scan_leads(d, DAY)
    finally:
        f.close()
    assert out["files_leads"] == 1, "AC-FIN2 directory treated as an entry"
    assert _count(w["db"], "leads") == 1, "AC-FIN2 nested file was read"


def case_fin3(tmp):
    """AC-FIN3: bad JSON text rejects the whole ring, zero rows."""
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.json", {"lead_id": "L1", "text": "valid"})
    _put_text(d, "002.json", "{not json")
    f = fd.FunnelDaily(w["db"])
    try:
        _expect_funarg(lambda: f.scan_leads(d, DAY))
        assert _count(w["db"], "leads") == 0, \
            "AC-FIN3 partial write before the rejection"
    finally:
        f.close()


def case_fin4(tmp):
    """AC-FIN4: a decoded JSON value that is not an object rejects."""
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.json", {"lead_id": "L1"})
    _put(d, "002.json", [1, 2])
    _put(d, "003.json", "bare string")
    f = fd.FunnelDaily(w["db"])
    try:
        _expect_funarg(lambda: f.scan_leads(d, DAY))
        assert _count(w["db"], "leads") == 0, \
            "AC-FIN4 rows booked despite a non-object face"
    finally:
        f.close()


def case_fin5(tmp):
    """AC-FIN5: an empty .json file is a bad in-contract face."""
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.json", {"lead_id": "L1"})
    _put_raw(d, "002.json", b"")
    f = fd.FunnelDaily(w["db"])
    try:
        _expect_funarg(lambda: f.scan_leads(d, DAY))
        assert _count(w["db"], "leads") == 0, "AC-FIN5 empty file booked rows"
    finally:
        f.close()


def case_fin6(tmp):
    """AC-FIN6: suffix matching is byte-exact - .JSON is junk."""
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.JSON", {"lead_id": "L1"})
    _put(d, "002.Json", {"lead_id": "L2"})
    f = fd.FunnelDaily(w["db"])
    try:
        out = f.scan_leads(d, DAY)
    finally:
        f.close()
    assert out["files_leads"] == 0, "AC-FIN6 upper-case suffix accepted"
    assert out["leads_new"] == 0, "AC-FIN6 upper-case file booked a row"


def case_fin7(tmp):
    """AC-FIN7: orders and flows share the very same law."""
    w = _world(tmp)
    junk_only = _inbox(w, "orders")
    _put_raw(junk_only, "readme.txt", b"\xff\xfe\x00junk")
    f = fd.FunnelDaily(w["db"])
    try:
        zero = f.book_orders(junk_only, DAY)
        assert zero["orders_seen"] == 0 and zero["orders_new"] == 0, \
            "AC-FIN7 junk-only orders inbox not an honest zero"

        bad_orders = _inbox(w, "orders")
        _put(bad_orders, "001.json",
             {"order_id": "O1", "sku": "pack", "amount_cent": 100})
        _put_text(bad_orders, "002.json", "{broken")
        _expect_funarg(lambda: f.book_orders(bad_orders, DAY))
        assert _count(w["db"], "orders") == 0, \
            "AC-FIN7 orders booked before the rejection"

        bad_flows = _inbox(w, "flows")
        _put(bad_flows, "001.json",
             {"flow_id": "F1", "account": "a", "kind": "grant",
              "amount": 10})
        os.makedirs(os.path.join(bad_flows, "fake.json"))
        _put_text(bad_flows, "002.json", "[]")
        _expect_funarg(lambda: f.book_token_flows(bad_flows, DAY))
        assert _count(w["db"], "flows") == 0, \
            "AC-FIN7 flows booked before the rejection"
    finally:
        f.close()


def case_fin8(tmp):
    """AC-FIN8: hygiene - pure ASCII suite source, AST-clean imports
    and clock face, shipped config bytes unchanged."""
    own = os.path.join(BASE, "test_funnel_inbox.py")
    text = open(own, "rb").read().decode("ascii")

    tree = ast.parse(text)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    for name in ("socket", "urllib", "http", "requests", "ssl"):
        assert name not in modules, "AC-FIN8 network import %s" % name

    clock_attrs = ("now", "today", "utcnow")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in clock_attrs, \
                "AC-FIN8 wall clock .%s" % node.attr

    cfg = os.path.join(BASE, "config.json")

    def sha(path):
        return hashlib.sha256(open(path, "rb").read()).hexdigest()

    cfg_sha = sha(cfg)
    w = _world(tmp)
    d = _inbox(w, "leads")
    _put(d, "001.json", {"lead_id": "L1", "text": "platform billing"})
    f = fd.FunnelDaily(w["db"])
    try:
        f.run_daily(d, _inbox(w, "orders"), _inbox(w, "flows"), DAY)
    finally:
        f.close()
    assert sha(cfg) == cfg_sha, "AC-FIN8 shipped config mutated"


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-inbox-suite-")
    cases = [
        ("AC-FIN1 junk files skipped unopened", case_fin1),
        ("AC-FIN2 directories skipped, no recursion", case_fin2),
        ("AC-FIN3 bad JSON rejects the ring", case_fin3),
        ("AC-FIN4 non-object JSON rejects", case_fin4),
        ("AC-FIN5 empty file rejects", case_fin5),
        ("AC-FIN6 suffix is byte-exact", case_fin6),
        ("AC-FIN7 orders and flows share the law", case_fin7),
        ("AC-FIN8 hygiene", case_fin8),
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