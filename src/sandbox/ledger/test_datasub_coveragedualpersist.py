"""Dual-window combined coverage board across a full-stack
restart (BigDomain R2009; the coverage_board_dual persist seat -
the R2008-reseed explore-queue row, criteria AC-CVDBP1..
AC-CVDBP7 pre-registered in the state/queue/explore.md claim row
before this suite code existed; honesty law. The AC-CVDBP
prefix and the suite filename were each git-grep verified
zero-occupied at claim time on 2026-10-17).

Persist-family lineage (R1883/R1884/R1885/R1889/R1900/R1902/
R1935): the dual board is a read-time derivation (single-source
coverage_board() delegations), so this window pins three
instances on the same db paths - anchor world -> close both
pieces -> instance2 reopen byte-identical dual battery replay ->
gate zero-drift probes -> post-restart record-time continuation
on both zones (new registration, new subscription with an
October period recorded in November, new delivery with an
October period recorded in November - the provenance probes) ->
pure-read law -> third instance stability. The frozen clock
(R1678 law) keeps every recorded row's window attribution
deterministic; the double run is byte-identical.

Usage: python test_datasub_coveragedualpersist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                    # noqa: E402 (P-47-2b core)
import datasub as S                   # noqa: E402 (R1764 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: dataset"
              " subscriptions deliver city aggregate data,"
              " not investment advice")

ROW_KEYS = {"dataset_key", "title", "period", "ai_label",
            "subscribers", "subscriptions", "deliveries"}
DUAL_KEYS = {"coverage_board", "coverage_board_window",
             "window", "disclaimer"}

OCT_TS = "2026-10-05T10:00:00Z"
NOV_TS = "2026-11-07T09:30:00Z"
NOV2_TS = "2026-11-20T11:00:00Z"

FROZEN_SCHEMA = """
CREATE TABLE IF NOT EXISTS dataset_registry (
    dataset_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    period TEXT NOT NULL CHECK (period IN ('monthly', 'quarterly')),
    price_cent INTEGER NOT NULL CHECK (price_cent >= 1),
    dataset_digest TEXT NOT NULL,
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dataset_subscriptions (
    sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT NOT NULL,
    dataset_key TEXT NOT NULL,
    period_window TEXT NOT NULL,
    purchase_ref TEXT NOT NULL UNIQUE,
    price_cent INTEGER NOT NULL,
    bound_spend_tx TEXT NOT NULL,
    subscribed_utc TEXT NOT NULL,
    UNIQUE (account, dataset_key, period_window)
);
CREATE TABLE IF NOT EXISTS dataset_deliveries (
    delivery_ref TEXT PRIMARY KEY,
    account TEXT NOT NULL,
    dataset_key TEXT NOT NULL,
    period_window TEXT NOT NULL,
    delivered_utc TEXT NOT NULL
);
"""


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha16(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]


def io_read(path):
    with open(path, "rb") as fh:
        return fh.read()


def expect_error(fn, code):
    try:
        fn()
    except S.DataSubError as exc:
        return (exc.code == code), exc.code
    return False, "NO-RAISE"


def ds_counts(ds_path):
    conn = sqlite3.connect(ds_path)
    out = {}
    for name in ("dataset_registry", "dataset_subscriptions",
                 "dataset_deliveries"):
        out[name] = int(conn.execute(
            "SELECT COUNT(*) FROM " + name).fetchone()[0])
    conn.close()
    return out


def ledger_counts(db_path):
    conn = sqlite3.connect(db_path)
    total = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    spend = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
        ).fetchone()[0])
    conn.close()
    return {"tx_total": total, "spend": spend}


def manual_board(ds_path, month=None):
    """Independent second derivation (direct SQL GROUP BY,
    prefix filter when month given) - never the product's own
    code path."""
    conn = sqlite3.connect(ds_path)
    regs = conn.execute(
        "SELECT dataset_key FROM dataset_registry").fetchall()
    if month is None:
        subs = {r[0]: (int(r[1]), int(r[2])) for r in conn.execute(
            "SELECT dataset_key, COUNT(*), COUNT(DISTINCT account)"
            " FROM dataset_subscriptions GROUP BY dataset_key"
        ).fetchall()}
        dels = {r[0]: int(r[1]) for r in conn.execute(
            "SELECT dataset_key, COUNT(*) FROM dataset_deliveries"
            " GROUP BY dataset_key").fetchall()}
    else:
        subs = {r[0]: (int(r[1]), int(r[2])) for r in conn.execute(
            "SELECT dataset_key, COUNT(*), COUNT(DISTINCT account)"
            " FROM dataset_subscriptions"
            " WHERE substr(subscribed_utc, 1, 7) = ?"
            " GROUP BY dataset_key", (month,)).fetchall()}
        dels = {r[0]: int(r[1]) for r in conn.execute(
            "SELECT dataset_key, COUNT(*) FROM dataset_deliveries"
            " WHERE substr(delivered_utc, 1, 7) = ?"
            " GROUP BY dataset_key", (month,)).fetchall()}
    conn.close()
    out = {}
    for (key,) in regs:
        n_rows, n_hh = subs.get(key, (0, 0))
        out[key] = {"subscribers": n_hh, "subscriptions": n_rows,
                    "deliveries": dels.get(key, 0)}
    return out


def dual_battery(face):
    out = {"oct": json.dumps(face.coverage_board_dual("2026-10"),
                             sort_keys=True),
           "nov": json.dumps(face.coverage_board_dual("2026-11"),
                             sort_keys=True),
           "empty": json.dumps(face.coverage_board_dual("2025-01"),
                               sort_keys=True)}
    out["full"] = json.dumps(face.coverage_board(), sort_keys=True)
    return out


def rows_by_key(env_text, zone):
    env = json.loads(env_text)
    return {r["dataset_key"]: json.dumps(r, sort_keys=True)
            for r in env[zone]}


def build_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    face = S.DatasetSubscriptionFace(led, DISCLAIMER)
    return led, face


class FrozenClock(object):
    """Module-global clock injection (R1678 frozen-clock law):
    save/restore in finally, explicit stamps, zero real-clock
    dependency in every recorded row."""

    def __init__(self):
        self.stamp = OCT_TS

    def __call__(self):
        return self.stamp


def main():
    tmp = tempfile.mkdtemp(prefix="covdualpersist-")
    cfg = json.loads(io_read(os.path.join(BASE, "config.json"))
                     .decode("utf-8"))
    cfg_sha_before = sha16(io_read(os.path.join(BASE, "config.json")))
    ds_sha_before = sha16(io_read(os.path.join(BASE, "datasub.py")))
    led_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))

    real_now = S._now_utc
    clock = FrozenClock()
    S._now_utc = clock
    try:
        db_path = os.path.join(tmp, "ledger.db")
        led, ds = build_stack(db_path, cfg)
        led.mint_to_pool("pool:reserve", 20000, "CVDBP-MINT-A",
                         "settlement")
        for who in ("ada", "bob", "carol"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 700),
                    ("usr:ada", "credit", 700)],
                   "manual:cvdbp-fund-ada", "persist window ada")
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:bob", "credit", 500)],
                   "manual:cvdbp-fund-bob", "persist window bob")
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:carol", "credit", 500)],
                   "manual:cvdbp-fund-carol", "persist window carol")

        ds.register_dataset("city-mobility", "City Mobility Index",
                            "monthly", 300, "digest-mob-1", False)
        ds.register_dataset("city-air", "City Air Quality Readings",
                            "monthly", 200, "digest-air-1", True)
        ds.register_dataset("city-parks", "City Parks Usage Digest",
                            "quarterly", 150, "digest-parks-1", True)

        clock.stamp = OCT_TS
        ds.subscribe("usr:ada", "city-mobility", "2026-10",
                     "dsp-ada-1001")
        ds.subscribe("usr:bob", "city-mobility", "2026-10",
                     "dsp-bob-1001")
        ds.subscribe("usr:carol", "city-air", "2026-10",
                     "dsp-carol-air-1001")

        clock.stamp = NOV_TS
        ds.subscribe("usr:ada", "city-mobility", "2026-11",
                     "dsp-ada-1101")
        ds.subscribe("usr:carol", "city-parks", "2026-Q4",
                     "dsp-carol-q4")
        ds.deliver("usr:ada", "city-mobility", "2026-11",
                   "dlv-ada-1101")
        ds.deliver("usr:bob", "city-mobility", "2026-10",
                   "dlv-bob-1001")

        # ---- AC-CVDBP1: anchor world + pre-close snapshot --------
        bat_pre = dual_battery(ds)
        cnt1 = ds_counts(ds.db_path)
        led1 = ledger_counts(db_path)
        pre_oct_win = rows_by_key(bat_pre["oct"],
                                  "coverage_board_window")
        pre_nov_win = rows_by_key(bat_pre["nov"],
                                  "coverage_board_window")
        man_oct = manual_board(ds.db_path, "2026-10")
        man_nov = manual_board(ds.db_path, "2026-11")
        man_ok = True
        for zone, man in ((pre_oct_win, man_oct),
                          (pre_nov_win, man_nov)):
            for key, m in man.items():
                row = json.loads(zone[key])
                man_ok &= (row["subscribers"] == m["subscribers"]
                           and row["subscriptions"]
                           == m["subscriptions"]
                           and row["deliveries"] == m["deliveries"])
        oct_env = json.loads(bat_pre["oct"])
        nov_env = json.loads(bat_pre["nov"])
        pre_air_oct = json.loads(
            pre_oct_win["city-air"])["deliveries"]
        pre_air_nov = json.loads(
            pre_nov_win["city-air"])["deliveries"]
        ok1 = (
            set(oct_env.keys()) == DUAL_KEYS
            and oct_env["window"] == "2026-10"
            and nov_env["window"] == "2026-11"
            and len(oct_env["coverage_board"]) == 3
            and len(nov_env["coverage_board"]) == 3
            and all(set(r.keys()) == ROW_KEYS
                    for r in oct_env["coverage_board"]
                    + oct_env["coverage_board_window"]
                    + nov_env["coverage_board"]
                    + nov_env["coverage_board_window"])
            and man_ok
            and pre_air_oct == 0 and pre_air_nov == 0
            and json.loads(
                pre_oct_win["city-mobility"])["deliveries"] == 0
            and json.loads(
                pre_nov_win["city-mobility"])["deliveries"] == 2
            and cnt1["dataset_registry"] == 3
            and cnt1["dataset_subscriptions"] == 5
            and cnt1["dataset_deliveries"] == 2
            and led1["spend"] == 5
        )
        record("AC-CVDBP1", ok1,
               "anchor world (frozen clock, real product paths):"
               " 3 datasets, 5 subscriptions (ada two-window"
               " mobility, bob october mobility, carol october air,"
               " carol Q4 parks), 2 deliveries (ada 2026-11 + bob"
               " october-period delivery recorded in November -"
               " provenance probe: oct mobility dlv=0, nov mobility"
               " dlv=2); every dual window-zone row equals the"
               " manual record-time prefix SQL cross derivation;"
               " count anchors registry=3 subs=5 dlv=2 spend=5;"
               " pre-close battery sha16 " +
               sha16(json.dumps(bat_pre, sort_keys=True)))

        # ---- AC-CVDBP2: close -> reopen -> byte-identical -------
        ds.close()
        led.close()
        led2, ds2 = build_stack(db_path, cfg)
        bat2 = dual_battery(ds2)
        diffs2 = [k for k in bat_pre if bat_pre[k] != bat2[k]]
        ok2 = not diffs2
        record("AC-CVDBP2", ok2,
               "instance2 (same db paths, same config) replays the"
               " full four-face battery (three dual windows + the"
               " default full board) byte-identical - the dual"
               " board is a pure read-time derivation with zero"
               " in-memory drift (diff keys=%s, digest %s)"
               % (diffs2 if diffs2 else "none",
                  sha16(json.dumps(bat2, sort_keys=True))))

        # ---- AC-CVDBP3: gate law survives the restart -----------
        cnt3_before = ds_counts(ds2.db_path)
        led3_before = ledger_counts(db_path)
        gates_ok = True
        gate_codes = set()
        for bad in (None, "2026-13", 202610, True,
                    "2026/10", "2026-10\n", "2026-10 "):
            ok_gate, code = expect_error(
                lambda b=bad: ds2.coverage_board_dual(b),
                S.E_DSB_BAD_WINDOW)
            gates_ok &= ok_gate
            gate_codes.add(str(code))
        cnt3_after = ds_counts(ds2.db_path)
        led3_after = ledger_counts(db_path)
        ok3 = (gates_ok and len(gate_codes) == 1
               and cnt3_before == cnt3_after
               and led3_before == led3_after)
        record("AC-CVDBP3", ok3,
               "post-restart window gate: seven representative bad"
               " windows (None, month-13, int, bool, slash,"
               " trailing newline, trailing space) all fail closed"
               " %s before any read with zero side effects (ds"
               " counts %s, ledger %s unchanged) - gate zero drift"
               " across the restart"
               % (sorted(gate_codes),
                  json.dumps(cnt3_after, sort_keys=True),
                  json.dumps(led3_after, sort_keys=True)))

        # ---- AC-CVDBP4: post-restart continuation, both zones ----
        clock.stamp = NOV2_TS
        ds2.register_dataset("city-transit",
                             "City Transit Flow Digest",
                             "monthly", 90, "digest-transit-1",
                             False)
        sub_tr = ds2.subscribe("usr:ada", "city-transit",
                               "2026-10", "dsp-ada-transit-1001")
        ds2.deliver("usr:carol", "city-air", "2026-10",
                    "dlv-carol-air-1001")
        bat_live = dual_battery(ds2)
        led4 = ledger_counts(db_path)
        post_oct_win = rows_by_key(bat_live["oct"],
                                   "coverage_board_window")
        post_nov_win = rows_by_key(bat_live["nov"],
                                   "coverage_board_window")
        post_full = rows_by_key(bat_live["oct"],
                                "coverage_board")
        frozen_oct = all(
            post_oct_win[key] == pre_oct_win[key]
            for key in ("city-mobility", "city-air", "city-parks"))
        frozen_nov = all(
            post_nov_win[key] == pre_nov_win[key]
            for key in ("city-mobility", "city-parks"))
        transit_oct = json.loads(post_oct_win["city-transit"])
        transit_nov = json.loads(post_nov_win["city-transit"])
        air_nov = json.loads(post_nov_win["city-air"])
        transit_full = json.loads(post_full["city-transit"])
        air_full = json.loads(post_full["city-air"])
        mobility_full = json.loads(post_full["city-mobility"])
        ok4 = (
            sub_tr["price_cent"] == 90 and sub_tr["spend_tx"]
            and led4["spend"] == led3_before["spend"] + 1
            and frozen_oct and frozen_nov
            and len(post_oct_win) == 4
            and transit_oct["subscribers"] == 0
            and transit_oct["subscriptions"] == 0
            and transit_oct["deliveries"] == 0
            and transit_nov["subscribers"] == 1
            and transit_nov["subscriptions"] == 1
            and transit_nov["deliveries"] == 0
            and air_nov["deliveries"] == 1
            and transit_full["subscribers"] == 1
            and transit_full["subscriptions"] == 1
            and air_full["deliveries"] == 1
            and mobility_full["deliveries"] == 2
            and led2.balance("usr:ada")["balance"] == 10
        )
        record("AC-CVDBP4", ok4,
               "post-restart continuation at NOV2 record time: new"
               " registration city-transit + ada subscription"
               " (october PERIOD window, november RECORD time,"
               " true spend -1 tx -> %d) + carol october-period air"
               " delivery recorded in november (second provenance"
               " probe, zero token); october window zone: all"
               " three pre-existing dataset rows byte-frozen"
               " (november-recorded data zero permeation) and"
               " city-transit carried as a dense zero row (4 rows,"
               " registry authority); november window zone:"
               " mobility/parks byte-frozen, air delivery row"
               " continues 0->1, city-transit enters {1hh,1sub,"
               "0dlv}; full zone carries all new data (transit"
               " 1/1/0, air dlv 1, mobility dlv 2 constant)"
               % led2.balance("usr:ada")["balance"])

        # ---- AC-CVDBP5: pure-read law across the restart ---------
        cnt5_before = ds_counts(ds2.db_path)
        led5_before = ledger_counts(db_path)
        dual_battery(ds2)
        dual_battery(ds2)
        ds2.coverage_board()
        ds2.coverage_board("2026-10")
        cnt5_after = ds_counts(ds2.db_path)
        led5_after = ledger_counts(db_path)
        ok5 = (cnt5_before == cnt5_after
               and led5_before == led5_after)
        record("AC-CVDBP5", ok5,
               "pure-read law: the full read battery (two dual"
               " batteries + live default board + live month"
               " window) leaves every ds table count and the"
               " ledger tx/spend counts untouched (%s / %s)"
               % (json.dumps(cnt5_after, sort_keys=True),
                  json.dumps(led5_after, sort_keys=True)))

        # ---- AC-CVDBP6: double-restart stability ------------------
        bat_post2 = dual_battery(ds2)
        ds2.close()
        led2.close()
        led3, ds3 = build_stack(db_path, cfg)
        bat3 = dual_battery(ds3)
        diffs6 = [k for k in bat_post2 if bat_post2[k] != bat3[k]]
        ok6 = not diffs6
        record("AC-CVDBP6", ok6,
               "third instance (second full-stack restart) replays"
               " the post-continuation dual battery byte-identical"
               " (continuation face survives a second restart with"
               " zero drift; diff keys=%s, digest %s)"
               % (diffs6 if diffs6 else "none",
                  sha16(json.dumps(bat3, sort_keys=True))))

        # ---- AC-CVDBP7: hygiene -----------------------------------
        cfg_sha_after = sha16(io_read(os.path.join(BASE,
                                                  "config.json")))
        ds_sha_after = sha16(io_read(os.path.join(BASE,
                                                  "datasub.py")))
        led_sha_after = sha16(io_read(os.path.join(BASE,
                                                   "ledger.py")))
        reg_src = io_read(os.path.join(
            os.path.dirname(BASE), "reconcile_all.py")).decode(
                "utf-8")
        reg_ok = ('"ledger-datasub-coveragedualpersist"'
                  in reg_src
                  and '"test_datasub_coveragedualpersist.py"), 7)'
                  in reg_src)
        own_src = io_read(os.path.abspath(__file__)).decode(
            "ascii")
        import_lines = [ln.strip() for ln in own_src.splitlines()
                        if ln.strip().startswith("import ")
                        or ln.strip().startswith("from ")]
        net_words = ("urllib", "requests", "socket", "http")
        network = [ln for ln in import_lines
                   if any(w in ln for w in net_words)]
        ok7 = (
            cfg_sha_before == cfg_sha_after
            and ds_sha_before == ds_sha_after
            and led_sha_before == led_sha_after
            and S._SCHEMA == FROZEN_SCHEMA
            and reg_ok and not network
            and tmp.startswith(tempfile.gettempdir())
        )
        record("AC-CVDBP7", ok7,
               "hygiene: shipped config.json/datasub.py/ledger.py"
               " sha16 unchanged (%s/%s/%s); the three CREATE"
               " TABLE statements byte-identical to the frozen"
               " schema anchor (zero schema touch); reconcile_all"
               " SUITES row ledger-datasub-coveragedualpersist"
               " criteria 7 registered=%s; suite source pure"
               " ASCII, zero network imports; world dbs live"
               " outside the repo=%s"
               % (cfg_sha_after, ds_sha_after, led_sha_after,
                  reg_ok,
                  tmp.startswith(tempfile.gettempdir())))

        ds3.close()
        led3.close()
    finally:
        S._now_utc = real_now

    fails = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fails == 0 else "FAIL",
                              len(RESULTS) - fails, len(RESULTS)),
          flush=True)
    return 0 if fails == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
