"""Cross-restart persistence window for the developer
revenue-share settlement face (BigDomain R1945; the devshare
seat of the R1886 persist-family lineage - the R1940-seeded
row, criteria AC-DSVP1..AC-DSVP7 pre-registered in the R1945
tech.md claim row before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Five-piece full-chain restart world on the real product path:
anchor world (two registered developers with metered usage,
two devshare windows - one explicit, one usage-derived - plus
one cross-face UGC window under the same caller id) -> close
all five pieces (ds/inc/dk/metered/led) -> reopen the same
db/config -> byte-identical read replay -> restart-surviving
gate probes -> post-restart real-path continuation (the
persisted api_key keeps metering, a new devshare window and a
new same-id UGC window settle independently = the namespace
law survives the restart) -> frozen history rows + dup gates
across the restart -> pure-read law -> third instance
stability. devshare_windows / dev_board read faces carry
persisted clock strings (settled_utc, registered/purchased/
consumed utc, minute_window, the month window), time-derived
api_key values and time-derived spend_tx hex ids, so the
evidence digests mask all three families (banded projection,
R1902 law) while the in-run battery keeps full dumps.

Usage: python test_devshare_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import metered as M         # noqa: E402  (R626 product)
import apidev as D          # noqa: E402  (R1700 face)
import incentive as IN      # noqa: E402  (R600 gradient)
import devshare as DS      # noqa: E402  (R1759 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: revenue-share settlement"
              " is a platform accounting face, not investment advice")

_UTC_RE = re.compile(
    r'"([a-z_]*(?:utc|window|ts|stamp)[a-z_]*)":'
    r' "(?:\d{4}-\d{2}[^"]*)"')
_KEY_RE = re.compile(r'"api_key": "[^"]*"')
_TXS_RE = re.compile(r'"spend_txs": \[[^\]]*\]')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except Exception as exc:                     # noqa: BLE001
        code = getattr(exc, "code", type(exc).__name__)
        return code in codes, code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    text = _TXS_RE.sub('"spend_txs": ["<tx>"]', text)
    text = _UTC_RE.sub(lambda m: '"%s": "<ts>"' % m.group(1), text)
    return _KEY_RE.sub('"api_key": "<key>"', text)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    out["windows"] = int(conn.execute(
        "SELECT COUNT(*) FROM incentive_windows").fetchone()[0])
    out["share_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'share'"
    ).fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    conn.close()
    return out


def read_battery(ds, dk, led):
    return {
        "hist": dump(ds.devshare_windows()),
        "board_ada": dump(dk.dev_board("usr:ada")),
        "board_lin": dump(dk.dev_board("usr:lin")),
        "bal_ada": led.balance("usr:ada")["balance"],
        "bal_lin": led.balance("usr:lin")["balance"],
        "bal_ghost": led.balance("usr:ghost")["balance"],
        "bal_share": led.balance("pool:share")["balance"],
        "bal_reserve": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def hist_rows(ds):
    return dict((w["window_id"], w) for w in
                ds.devshare_windows()["windows"])


def make_probes(face, ugc):
    return (
        ("not-dev", lambda: face.settle_window(
            "w-gate", [("usr:ghost", 5)]), DS.E_DS_NOT_DEV),
        ("dup-devshare", lambda: face.settle_window(
            "w1", [("usr:ada", 12), ("usr:lin", 5)]),
         IN.E_INC_WINDOW_DUP),
        ("dup-ugc", lambda: ugc.settle_window(
            "w1", [("usr:ada", 3)]), IN.E_INC_WINDOW_DUP),
        ("empty", lambda: face.settle_window(
            "w-empty", []), IN.E_INC_EMPTY),
        ("no-usage", lambda: face.settle_from_usage(
            "w-none", ["usr:ghost"]), DS.E_DS_NO_USAGE),
    )


def run_probes(probe_specs):
    lines = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_error(fn, code)
        lines.append("%s=%s" % (label, got) if ok_one else
                     "%s NOT-RAISED(%s)" % (label, got))
    return lines, all("NOT-RAISED" not in p for p in lines)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="devshare-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    mod_sha_before = dict(
        (name, sha16(io_read(os.path.join(BASE, name + ".py"))))
        for name in ("devshare", "incentive", "apidev", "metered",
                     "ledger"))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path -----
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ds = DS.DevShareFace(led, dk, DISCLAIMER)
    inc = IN.IncentiveFace(led)        # UGC cross-face (namespace)

    led.mint_to_pool("pool:share", 4000, "SETTLE-DSVP-SHARE",
                     "settlement")
    led.mint_to_pool("pool:reserve", 5000, "SETTLE-DSVP-RES",
                     "settlement")
    for who in ("ada", "lin", "ghost"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 600),
                ("usr:ada", "credit", 600)],
               "manual:dsvp-fund-ada", "persist window funding ada")
    led.adjust([("pool:reserve", "debit", 600),
                ("usr:lin", "credit", 600)],
               "manual:dsvp-fund-lin", "persist window funding lin")

    k1 = dk.issue_key("usr:ada", "alpha", 50, ["backtest"], True)
    k2 = dk.issue_key("usr:lin", "beta", 50, ["visualize"], True)
    dk.buy_credits(k1["api_key"], 40, 5, "PACK-DSVP-A")
    dk.buy_credits(k2["api_key"], 20, 5, "PACK-DSVP-B")
    for i in range(12):
        dk.call(k1["api_key"], "backtest",
                "dsvp-call-a-%d" % i, "eng-dsvp-a-%d" % i)
    for i in range(5):
        dk.call(k2["api_key"], "visualize",
                "dsvp-call-b-%d" % i, "eng-dsvp-b-%d" % i)

    # two devshare windows + one cross-face UGC window (same id)
    r1 = ds.settle_window("w1", [("usr:ada", 12), ("usr:lin", 5)])
    r2 = ds.settle_from_usage("w2", ["usr:lin", "usr:ada"])
    inc.settle_window("w1", [("usr:ada", 3)])

    # -- AC-DSVP1 control anchor: world pinned + gate probes -----
    bat1 = read_battery(ds, dk, led)
    cnt1 = table_counts(db_path)
    hist1 = hist_rows(ds)
    quota_ada = sum(int(k["quota_used"])
                    for k in dk.dev_board("usr:ada")["keys"])
    quota_lin = sum(int(k["quota_used"])
                    for k in dk.dev_board("usr:lin")["keys"])
    ok_world = (
        r1["paid"] == [("usr:ada", 34), ("usr:lin", 15)]
        and r2["paid"] == [("usr:lin", 15), ("usr:ada", 34)]
        and quota_ada == 12 and quota_lin == 5
        and sorted(hist1.keys()) == ["w1", "w2"]
        and hist1["w1"]["total_paid"] == 49
        and hist1["w2"]["total_paid"] == 49
        and cnt1["windows"] == 3 and cnt1["share_tx"] == 5
        and bat1["bal_ada"] == 498 and bat1["bal_lin"] == 530
        and bat1["bal_ghost"] == 0
        and bat1["bal_share"] == 3872
        and bat1["bal_reserve"] == 4100)
    probe_specs1 = make_probes(ds, inc)
    probes1, ok_probes1 = run_probes(probe_specs1)
    ok_drift1 = (table_counts(db_path) == cnt1
                 and read_battery(ds, dk, led) == bat1)
    ok1 = ok_world and ok_probes1 and ok_drift1
    record("AC-DSVP1", ok1, "anchor world pinned (registered devs"
          " ada quota 12 + lin quota 5; devshare w1 explicit paid"
          " [(ada,34),(lin,15)] total 49; w2 usage-derived paid"
          " [(lin,15),(ada,34)] total 49; cross-face UGC w1 same"
          " caller id settles 30 independently = namespace anchor;"
          " balances 498/530/0 (funded 600/600 minus the credit"
          " packs 200/100 which land in pool:reserve), pool:share"
          " 3872, pool:reserve 4100;"
          " incentive_windows=3 share-tx=5); five gate probes"
          " rejected (%s); counts and battery frozen across the"
          " probe batch; digest=%s" % (
              "; ".join(probes1), evidence_digest(bat1)))

    # -- AC-DSVP2 cross-restart byte-identical replay ------------
    ds.close()
    inc.close()
    dk.close()
    metered.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    metered2 = M.MeteredFace(led2)
    dk2 = D.DevKeyFace(metered2, DISCLAIMER)
    ds2 = DS.DevShareFace(led2, dk2, DISCLAIMER)
    inc2 = IN.IncentiveFace(led2)
    bat2 = read_battery(ds2, dk2, led2)
    diffs2 = battery_diffs(bat1, bat2)
    ok2 = not diffs2
    record("AC-DSVP2", ok2, "five-piece close->reopen (ds.close ->"
          " inc.close -> dk.close -> metered.close -> led.close ->"
          " Ledger same db/cfg + MeteredFace + DevKeyFace +"
          " DevShareFace + IncentiveFace fresh): read battery"
          " byte-identical to the pre-close snapshot (windows"
          " history with persisted settled_utc rows + both"
          " dev boards with registered/purchased/consumed utc"
          " values + five balances), diffs=%s; the read-only dock"
          " rebuilds over the same incentive_windows values with"
          " zero in-memory drift; digest=%s" % (
              diffs2 or "none", evidence_digest(bat2)))

    # -- AC-DSVP3 gates survive the restart, zero drift ----------
    probe_specs2 = make_probes(ds2, inc2)
    probes2, ok_probes2 = run_probes(probe_specs2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(ds2, dk2, led2) == bat2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-DSVP3", ok3, "restart-surviving gates: five probes"
          " all rejected with identical codes on instance 2 (%s);"
          " the window idempotence lives in the shared"
          " incentive_windows table so both dup gates (devshare"
          " namespace and UGC namespace) survive the restart;"
          " counts and battery frozen across the probe batch"
          " (windows=%d share-tx=%d unchanged, zero movement)" % (
              "; ".join(probes2), cnt1["windows"],
              cnt1["share_tx"]))

    # -- AC-DSVP4 post-restart real-path continuation -------------
    for i in range(3):
        dk2.call(k1["api_key"], "backtest",
                 "dsvp-p2-a-%d" % i, "eng-dsvp-p2-a-%d" % i)
    quota_ada2 = sum(int(k["quota_used"])
                     for k in dk2.dev_board("usr:ada")["keys"])
    r3 = ds2.settle_from_usage("w3", ["usr:ada"])
    ugc_paid = inc2.settle_window("w3", [("usr:lin", 1)])
    bat4 = read_battery(ds2, dk2, led2)
    cnt4 = table_counts(db_path)
    hist4 = hist_rows(ds2)
    share_conn = sqlite3.connect(db_path)
    share_rows = share_conn.execute(
        "SELECT COUNT(*) FROM ledger_entries WHERE account_id ="
        " 'pool:share' AND direction = 'debit'").fetchone()[0]
    share_conn.close()
    ok4 = (
        quota_ada2 == 15
        and r3["paid"] == [("usr:ada", 40)]
        and ugc_paid == [("usr:lin", 10)]
        and sorted(hist4.keys()) == ["w1", "w2", "w3"]
        and hist4["w3"]["total_paid"] == 40
        and cnt4["windows"] == 5 and cnt4["share_tx"] == 7
        and int(share_rows) == 7
        and bat4["bal_ada"] == 538 and bat4["bal_lin"] == 540
        and bat4["bal_share"] == 3822
        and bat4["bal_reserve"] == 4100)
    record("AC-DSVP4", ok4, "post-restart continuation: the"
          " persisted api_key keeps metering on instance 2 (3"
          " new backtest calls -> ada quota 12->15, board"
          " recompute reflects the new usage); settle_from_usage"
          " w3 pays [(ada,40)] (gradient 10*3+5*2 on 15 units);"
          " the same caller id settles independently in the UGC"
          " namespace (w3 -> [(lin,10)] = the namespace law"
          " survives the restart); history grows w1/w2 -> w1/w2/"
          " w3 with the old rows preserved; windows 3->5,"
          " share-tx 5->7 with seven pool:share debit legs (SQL"
          " cross); balances 538/540, pool:share 3822;"
          " digest=%s" % evidence_digest(bat4))

    # -- AC-DSVP5 frozen rows + dup gates across the restart -----
    fields = ("window_id", "total_paid", "settled_utc")
    frozen_ok = all(all(hist1[key][f] == hist4[key][f]
                        for f in fields)
                    for key in hist1)
    dup3, code_dup3 = expect_error(
        lambda: ds2.settle_window("w3", [("usr:ada", 15)]),
        IN.E_INC_WINDOW_DUP)
    dup3_ugc, code_dup3u = expect_error(
        lambda: inc2.settle_window("w3", [("usr:lin", 1)]),
        IN.E_INC_WINDOW_DUP)
    gate_ghost, code_ghost = expect_error(
        lambda: ds2.settle_window("w-gate3", [("usr:ghost", 5)]),
        DS.E_DS_NOT_DEV)
    bal5 = read_battery(ds2, dk2, led2)
    ok5 = (frozen_ok and dup3 and dup3_ugc and gate_ghost
           and table_counts(db_path) == cnt4 and bal5 == bat4)
    record("AC-DSVP5", ok5, "frozen faces: every pre-existing"
          " window row keeps all persisted fields (window_id/"
          " total_paid/settled_utc) byte-identical to the"
          " pre-close snapshot - the new w3 row only appends;"
          " dup gates across the restart: devshare w3 replay"
          " rejected %s, UGC w3 replay rejected %s (namespace"
          "-separate, zero movement); registry gate still"
          " rejects the non-developer %s; counts and battery"
          " frozen across all three probes" % (
              code_dup3, code_dup3u, code_ghost))

    # -- AC-DSVP6 pure-read law -----------------------------------
    bat_a = read_battery(ds2, dk2, led2)
    bat_b = read_battery(ds2, dk2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(db_path) == cnt4)
    record("AC-DSVP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - windows history + both dev boards +"
          " five balances byte-identical between the two reads and"
          " table counts constant (read faces have zero side"
          " effects)")

    # -- AC-DSVP7 third instance stability + hygiene --------------
    ds2.close()
    inc2.close()
    dk2.close()
    metered2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    metered3 = M.MeteredFace(led3)
    dk3 = D.DevKeyFace(metered3, DISCLAIMER)
    ds3 = DS.DevShareFace(led3, dk3, DISCLAIMER)
    bat3 = read_battery(ds3, dk3, led3)
    diffs3 = battery_diffs(bal5, bat3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in
                         ("urllib", "requests", "socket", "http"))]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                  and os.path.realpath(tmp).startswith(
                      os.path.realpath(tempfile.gettempdir())))
    ok7 = (not diffs3
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok
           and non_ascii == 0 and not net_imports
           and tmp_outside)
    record("AC-DSVP7", ok7, "third instance: five-piece close ->"
          " reopen same db once more - battery byte-identical to"
          " the instance-2 terminal state (diffs=%s, history/"
          " boards/balances stable across a second restart);"
          " shipped files untouched (config + devshare/incentive"
          " /apidev/metered/ledger sha16 stable); suite source"
          " pure ASCII (%d non-ascii), zero network imports (%d"
          " hits), world tmp outside repo (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if tmp_outside else "NO"))

    ds3.close()
    dk3.close()
    metered3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
