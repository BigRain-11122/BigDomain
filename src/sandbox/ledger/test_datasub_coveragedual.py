"""Dataset coverage board dual-window combined read face
(BigDomain R2008; FIFO-head claim of the R1985 reseed row - the
boards_combined single-envelope law (R1974) applied to the
coverage month-window family (R1985); the R1989 dual-board
sentinel lineage).
Asserts the pre-registered criteria AC-CVDB1..AC-CVDB7 from the
explore.md claim row (criteria registered before this suite code
existed; honesty law; the AC-CVDB prefix, the method name
coverage_board_dual and the suite filename were each git-grep
verified zero-occupied at claim time on 2026-10-17). The dual
envelope presents the default full-window coverage board and the
explicit month-window coverage board side by side; both zones
delegate to the reference face (single derivation source, zero
direct queries in the dual body). Evidence stdout carries no raw
utc/tx values beyond the frozen clock constants (masked-digest
law R1941): the double run is byte-identical.

Usage: python test_datasub_coveragedual.py
"""

import hashlib
import inspect
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

DISCLAIMER = ("sandbox stand-in disclaimer: dataset subscriptions"
              " deliver city aggregate data, not investment advice")

ROW_KEYS = {"dataset_key", "title", "period", "ai_label",
            "subscribers", "subscriptions", "deliveries"}
DUAL_KEYS = {"coverage_board", "coverage_board_window",
             "window", "disclaimer"}

OCT_TS = "2026-10-05T10:00:00Z"
NOV_TS = "2026-11-07T09:30:00Z"

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
    """Independent second derivation (direct SQL GROUP BY, prefix
    filter when month given) - never the product's own code path."""
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
    """Full dual read battery over three windows, all as
    sort_keys dumps for byte identity."""
    out = {"oct": json.dumps(face.coverage_board_dual("2026-10"),
                             sort_keys=True),
           "nov": json.dumps(face.coverage_board_dual("2026-11"),
                             sort_keys=True),
           "empty": json.dumps(face.coverage_board_dual("2025-01"),
                               sort_keys=True)}
    return out


def rows_by_key(env, zone):
    return {r["dataset_key"]: r for r in env[zone]}


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
    tmp = tempfile.mkdtemp(prefix="covdual-")
    cfg = json.loads(io_read(os.path.join(BASE, "config.json"))
                     .decode("utf-8"))
    cfg_sha_before = sha16(io_read(os.path.join(BASE, "config.json")))
    led_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))

    real_now = S._now_utc
    clock = FrozenClock()
    S._now_utc = clock
    try:
        # ---- fresh zero-registration world (contract + gate) --
        # (own temp dir: the datasub db path is sibling-derived
        # from the ledger db path, so a fresh world sharing the
        # main world's temp dir would see its datasub.db rows)
        fresh_tmp = tempfile.mkdtemp(prefix="covdual-fresh-")
        fresh_db = os.path.join(fresh_tmp, "fresh-ledger.db")
        fresh_led, fresh_ds = build_stack(fresh_db, cfg)

        # ---- main world ------------------------------------------
        db_path = os.path.join(tmp, "ledger.db")
        led, ds = build_stack(db_path, cfg)
        led.mint_to_pool("pool:reserve", 20000, "CVDB-MINT-A",
                         "settlement")
        for who in ("ada", "bob", "carol"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 700),
                    ("usr:ada", "credit", 700)],
                   "manual:cvdb-fund-ada", "dual face funding ada")
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:bob", "credit", 500)],
                   "manual:cvdb-fund-bob", "dual face funding bob")
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:carol", "credit", 500)],
                   "manual:cvdb-fund-carol",
                   "dual face funding carol")

        ds.register_dataset("city-mobility", "City Mobility Index",
                            "monthly", 300, "digest-mob-1", False)
        ds.register_dataset("city-air", "City Air Quality Readings",
                            "monthly", 200, "digest-air-1", True)
        ds.register_dataset("city-parks", "City Parks Usage Digest",
                            "quarterly", 150, "digest-parks-1", True)

        # -- October record-time world --------------------------------
        clock.stamp = OCT_TS
        ds.subscribe("usr:ada", "city-mobility", "2026-10",
                     "dsp-ada-1001")
        ds.subscribe("usr:bob", "city-mobility", "2026-10",
                     "dsp-bob-1001")
        ds.subscribe("usr:carol", "city-air", "2026-10",
                     "dsp-carol-air-1001")

        # -- November record-time world --------------------------------
        clock.stamp = NOV_TS
        ds.subscribe("usr:ada", "city-mobility", "2026-11",
                     "dsp-ada-1101")
        ds.subscribe("usr:carol", "city-parks", "2026-Q4",
                     "dsp-carol-q4")
        ds.deliver("usr:ada", "city-mobility", "2026-11",
                   "dlv-ada-1101")
        # provenance-separation probe: delivery for the October
        # period window, recorded in November
        ds.deliver("usr:bob", "city-mobility", "2026-10",
                   "dlv-bob-1001")

        # -- AC-CVDB1: contract + single-source cross + honest empty
        fresh_env = fresh_ds.coverage_board_dual("2026-10")
        oct_env = ds.coverage_board_dual("2026-10")
        full_env = ds.coverage_board()
        win_env = ds.coverage_board("2026-10")
        ok1 = (
            set(fresh_env.keys()) == DUAL_KEYS
            and fresh_env["coverage_board"] == []
            and fresh_env["coverage_board_window"] == []
            and fresh_env["window"] == "2026-10"
            and fresh_env["disclaimer"] == DISCLAIMER
            and set(oct_env.keys()) == DUAL_KEYS
            and oct_env["window"] == "2026-10"
            and len(oct_env["coverage_board"]) == 3
            and len(oct_env["coverage_board_window"]) == 3
            and all(set(r.keys()) == ROW_KEYS
                    for r in oct_env["coverage_board"])
            and all(set(r.keys()) == ROW_KEYS
                    for r in oct_env["coverage_board_window"])
            and json.dumps(oct_env["coverage_board"],
                           sort_keys=True)
            == json.dumps(full_env["coverage_board"],
                          sort_keys=True)
            and json.dumps(oct_env["coverage_board_window"],
                           sort_keys=True)
            == json.dumps(win_env["coverage_board"], sort_keys=True)
            and oct_env["disclaimer"] == DISCLAIMER
        )
        record("AC-CVDB1", ok1,
               "contract: dual envelope keys exactly {coverage_"
               "board, coverage_board_window, window, disclaimer} "
               "with both zones at 3 rows of the 7-key row shape; "
               "full zone == live coverage_board() default rows "
               "and window zone == live coverage_board(\"2026-10\")"
               " rows (single derivation source, byte-identical "
               "dumps); zero-registration fresh face returns the "
               "honest empty dual board (both zones []) with the "
               "window key still carried; disclaimer constant")

        # -- AC-CVDB2: window gate fail-closed before any read -----
        counts_before = ds_counts(ds.db_path)
        led_before = ledger_counts(db_path)
        gate_codes = []
        gates_ok = True
        for bad in (None, "2026-13", "2026-00", "2026-1",
                    "2026/10", "2026-Q1", 202610, True,
                    "2026-10\n", " 2026-10", "2026-10 ",
                    "26-10", "2026-100"):
            ok, code = expect_error(
                lambda b=bad: ds.coverage_board_dual(b),
                S.E_DSB_BAD_WINDOW)
            gates_ok &= ok
            gate_codes.append(code if ok else "WRONG:" + str(code))
        fresh_gate_ok, fresh_gate_code = expect_error(
            lambda: fresh_ds.coverage_board_dual(None),
            S.E_DSB_BAD_WINDOW)
        counts_after_gate = ds_counts(ds.db_path)
        led_after_gate = ledger_counts(db_path)
        ok2 = (
            gates_ok
            and len(set(gate_codes)) == 1
            and fresh_gate_ok
            and fresh_gate_code == S.E_DSB_BAD_WINDOW
            and counts_before == counts_after_gate
            and led_before == led_after_gate
        )
        record("AC-CVDB2", ok2,
               "gate: 13 malformed windows (None - the full-window "
               "shape is already carried by the full zone, month-"
               "13, month-00, short, slash, quarterly form, int, "
               "bool, trailing newline, lead space, trailing "
               "space, 2-digit-year, long) all fail closed "
               "E_DSB_BAD_WINDOW before any read with zero side "
               "effects (ds counts %s, ledger %s); the gate still "
               "fires on the zero-registration fresh world (gate "
               "independent of the data face)" %
               (json.dumps(counts_after_gate, sort_keys=True),
                json.dumps(led_after_gate, sort_keys=True)))

        # -- AC-CVDB3: window slice cross + provenance + monotonic --
        nov_env = ds.coverage_board_dual("2026-11")
        man_oct = manual_board(ds.db_path, "2026-10")
        man_nov = manual_board(ds.db_path, "2026-11")
        oct_win = rows_by_key(oct_env, "coverage_board_window")
        nov_win = rows_by_key(nov_env, "coverage_board_window")
        full_zone = rows_by_key(oct_env, "coverage_board")
        dlv_rows = sqlite3.connect(ds.db_path).execute(
            "SELECT delivery_ref, period_window, delivered_utc"
            " FROM dataset_deliveries ORDER BY delivery_ref"
        ).fetchall()
        man_ok = True
        mon_ok = True
        for zone, man in ((oct_win, man_oct), (nov_win, man_nov)):
            for key, m in man.items():
                r = zone[key]
                man_ok &= (r["subscribers"] == m["subscribers"]
                           and r["subscriptions"]
                           == m["subscriptions"]
                           and r["deliveries"] == m["deliveries"])
                mon_ok &= (r["subscribers"] <= full_zone[key]
                           ["subscribers"]
                           and r["subscriptions"] <= full_zone[key]
                           ["subscriptions"]
                           and r["deliveries"] <= full_zone[key]
                           ["deliveries"])
        ok3 = (
            man_ok and mon_ok
            and oct_win["city-mobility"]["deliveries"] == 0
            and nov_win["city-mobility"]["deliveries"] == 2
            and full_zone["city-mobility"]["deliveries"] == 2
            and [list(r) for r in dlv_rows] ==
            [["dlv-ada-1101", "2026-11", NOV_TS],
             ["dlv-bob-1001", "2026-10", NOV_TS]]
        )
        record("AC-CVDB3", ok3,
               "window slice: every row of both dual window zones "
               "== manual record-time prefix SQL cross derivation; "
               "provenance probe - bob's October-period delivery "
               "recorded in November (dlv-bob-1001) lands on the "
               "November window zone (mobility dlv 2) and never on "
               "October (mobility dlv 0) while the full zone "
               "carries both (dlv 2); monotonic law holds per "
               "dataset per window (every window-zone count <= "
               "the full-zone count, both windows, all rows)")

        # -- AC-CVDB4: out-of-window dense + full-zone constancy ----
        empty_env = ds.coverage_board_dual("2025-01")
        empty_win = empty_env["coverage_board_window"]
        ok4 = (
            set(empty_env.keys()) == DUAL_KEYS
            and empty_env["window"] == "2025-01"
            and len(empty_win) == 3
            and sorted(r["dataset_key"] for r in empty_win)
            == ["city-air", "city-mobility", "city-parks"]
            and all(r["subscribers"] == 0
                    and r["subscriptions"] == 0
                    and r["deliveries"] == 0 for r in empty_win)
            and json.dumps(empty_env["coverage_board"],
                           sort_keys=True)
            == json.dumps(oct_env["coverage_board"],
                          sort_keys=True)
        )
        record("AC-CVDB4", ok4,
               "out-of-window month 2025-01: the window zone keeps "
               "all three registered datasets as dense all-zero "
               "rows (registry row-set authority holds inside a "
               "window, dataset_key ASC at the all-tie, zero "
               "phantom, zero dropped); the full zone is "
               "byte-identical to the October dual's full zone "
               "(full-zone window independence)")

        # -- AC-CVDB5: determinism + zero-cache liveness -------------
        bat_one = dual_battery(ds)
        bat_two = dual_battery(ds)
        nov_pre = json.loads(bat_one["nov"])
        oct_pre = json.loads(bat_one["oct"])
        led_pre_live = ledger_counts(db_path)
        # liveness: ada tops up, then a NEW dataset is registered
        # and subscribed (period window 2026-10) at NOV_TS record
        # time - the period never decides the board month
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:ada", "credit", 500)],
                   "manual:cvdb-fund-ada-2", "dual liveness topup")
        ds.register_dataset("city-transit",
                             "City Transit Flow Digest",
                             "monthly", 250, "digest-transit-1",
                             False)
        ds.subscribe("usr:ada", "city-transit", "2026-10",
                     "dsp-ada-transit-1001")
        led_post_live = ledger_counts(db_path)
        bat_live = dual_battery(ds)
        nov_live = json.loads(bat_live["nov"])
        oct_live = json.loads(bat_live["oct"])
        nov_pre_win = {r["dataset_key"]:
                       r for r in nov_pre["coverage_board_window"]}
        nov_live_win = {r["dataset_key"]:
                        r for r in nov_live["coverage_board_window"]}
        oct_pre_win = {r["dataset_key"]:
                       r for r in oct_pre["coverage_board_window"]}
        oct_live_win = {r["dataset_key"]:
                        r for r in oct_live["coverage_board_window"]}
        frozen_ok = all(
            json.dumps(nov_pre_win[key], sort_keys=True)
            == json.dumps(nov_live_win[key], sort_keys=True)
            and json.dumps(oct_pre_win[key], sort_keys=True)
            == json.dumps(oct_live_win[key], sort_keys=True)
            for key in ("city-mobility", "city-air", "city-parks"))
        nov_transit = rows_by_key(
            nov_live, "coverage_board_window")["city-transit"]
        nov_transit_full = rows_by_key(
            nov_live, "coverage_board")["city-transit"]
        oct_transit = rows_by_key(
            oct_live, "coverage_board_window")["city-transit"]
        ok5 = (
            bat_one == bat_two
            and bat_live != bat_one
            and frozen_ok
            and nov_transit["subscribers"] == 1
            and nov_transit["subscriptions"] == 1
            and nov_transit["deliveries"] == 0
            and nov_transit_full["subscribers"] == 1
            and nov_transit_full["subscriptions"] == 1
            and oct_transit["subscribers"] == 0
            and oct_transit["subscriptions"] == 0
            and led_post_live["spend"] == led_pre_live["spend"] + 1
        )
        record("AC-CVDB5", ok5,
               "determinism: the three-window dual battery is "
               "byte-identical on a double call (sha16 %s); "
               "liveness: after a true-path spend (+1 spend tx) "
               "registering city-transit and subscribing it with "
               "period window 2026-10 at NOV_TS record time, the "
               "re-read dual shows city-transit {1hh,1sub,0dlv} on "
               "the November window zone and the full zone, while "
               "the October window zone carries it as a dense "
               "zero row (the period window never decides the "
               "board month); every pre-existing dataset row is "
               "byte-frozen in both zones; battery sha16 %s "
               "differs from pre (zero-cache recompute)" %
               (sha16(json.dumps(bat_one, sort_keys=True)),
                sha16(json.dumps(bat_live, sort_keys=True))))

        # -- AC-CVDB6: pure-read law + zero-query delegation --------
        cnt_a = ds_counts(ds.db_path)
        led_a = ledger_counts(db_path)
        reads = [ds.coverage_board_dual("2026-10"),
                 ds.coverage_board_dual("2026-11"),
                 ds.coverage_board_dual("2025-01"),
                 ds.coverage_board(),
                 ds.coverage_board("2026-10")]
        reads2 = [ds.coverage_board_dual("2026-10"),
                  ds.coverage_board_dual("2026-11")]
        cnt_b = ds_counts(ds.db_path)
        led_b = ledger_counts(db_path)
        dual_src = inspect.getsource(
            S.DatasetSubscriptionFace.coverage_board_dual)
        ok6 = (
            cnt_a == cnt_b and led_a == led_b
            and json.dumps(reads[0], sort_keys=True)
            == json.dumps(reads2[0], sort_keys=True)
            and "INSERT" not in dual_src
            and "UPDATE" not in dual_src
            and "DELETE" not in dual_src
            and ".execute(" not in dual_src
            and dual_src.count("self.coverage_board(") == 2
        )
        record("AC-CVDB6", ok6,
               "pure-read law: the full read batch (three dual "
               "windows x2 + live default + live month window) "
               "leaves every ds table count and the ledger "
               "tx/spend counts untouched (%s / %s); the dual "
               "method body carries zero write-statement words, "
               "zero direct query calls, and exactly two "
               "self.coverage_board( delegations (single "
               "derivation source machine check)" %
               (json.dumps(cnt_b, sort_keys=True),
                json.dumps(led_b, sort_keys=True)))

        # -- AC-CVDB7: hygiene ---------------------------------------
        src = io_read(os.path.join(BASE,
                                   "test_datasub_coveragedual.py")
                     ).decode("ascii")
        face_src = io_read(os.path.join(BASE,
                                        "datasub.py")).decode(
            "ascii")
        import_lines = [ln.strip() for ln in
                        src.splitlines() if ln.strip().startswith(
                            "import ") or ln.strip().startswith(
                            "from ")]
        mod_import_lines = [ln.strip() for ln in
                            face_src.splitlines()
                            if ln.strip().startswith("import ")
                            or ln.strip().startswith("from ")]
        cfg_sha_after = sha16(io_read(os.path.join(BASE,
                                                   "config.json")))
        led_sha_after = sha16(io_read(os.path.join(BASE, "ledger.py")))
        net_words = ("urllib", "requests", "socket", "http")
        ok7 = (
            cfg_sha_after == cfg_sha_before
            and led_sha_after == led_sha_before
            and S._SCHEMA == FROZEN_SCHEMA
            and not any(word in ln for ln in import_lines
                        for word in net_words)
            and not any(word in ln for ln in mod_import_lines
                        for word in net_words)
        )
        record("AC-CVDB7", ok7,
               "hygiene: shipped config.json and ledger.py sha16 "
               "unchanged (%s / %s); the three CREATE TABLE "
               "statements byte-identical to the frozen schema "
               "anchor (zero schema touch); suite source pure "
               "ASCII; real import lines of both the suite and "
               "the module carry zero network libs; world dbs "
               "live under the system temp dir (outside the "
               "repo); delivery face = reconcile_all SUITES row "
               "ledger-datasub-coveragedual criteria 7 + full "
               "RUNNER PASS + matrix --check in the qa/ evidence "
               "log" % (cfg_sha_after, led_sha_after))

        ds.close()
        led.close()
        fresh_ds.close()
        fresh_led.close()
    finally:
        S._now_utc = real_now

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d)" % (
        "PASS" if not failed else "FAIL",
        len(RESULTS) - len(failed), len(RESULTS)), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
