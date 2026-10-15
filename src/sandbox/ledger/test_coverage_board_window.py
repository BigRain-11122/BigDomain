"""Dataset coverage board month-window read face (BigDomain R1985;
FIFO-head claim of the R1984 reseed row - the strict file-order
topmost open non-gated claim after the L13/L21 standing gated
rows; windowed-read family R1869/R1888/R1898 lineage, the
R1826/R1888 window-parameterization family law).
Asserts the pre-registered criteria AC-CVW1..AC-CVW7 from the
explore.md claim row (criteria registered before this suite code
existed; honesty law; the AC-CVW prefix was git-grep-verified
zero-occupied at claim time). The windowed board is the same
pure read-time derivation with each row family filtered by its
own record-time provenance stamp (subscriptions by subscribed_utc,
deliveries by delivered_utc) - the period window of a row never
decides which month board it lands on (the provenance-separation
probe: bob's delivery for the 2026-10 period window, recorded in
November, lands on the November board and never on October).
Evidence stdout carries no raw utc/tx values beyond the frozen
clock constants (masked-digest law R1941): the double run is
byte-identical.

Usage: python test_coverage_board_window.py
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
ENV_KEYS = {"coverage_board", "disclaimer"}
WENV_KEYS = {"window", "coverage_board", "disclaimer"}

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


def battery(face):
    """Full read battery: default + three explicit windows, all
    as sort_keys dumps for byte identity."""
    out = {"default": json.dumps(face.coverage_board(),
                                sort_keys=True),
           "oct": json.dumps(face.coverage_board("2026-10"),
                             sort_keys=True),
           "nov": json.dumps(face.coverage_board("2026-11"),
                             sort_keys=True),
           "empty": json.dumps(face.coverage_board("2025-01"),
                               sort_keys=True)}
    return out


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
    tmp = tempfile.mkdtemp(prefix="covboard-window-")
    cfg = json.loads(io_read(os.path.join(BASE, "config.json"))
                     .decode("utf-8"))
    cfg_sha_before = sha16(io_read(os.path.join(BASE, "config.json")))
    led_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    db_path = os.path.join(tmp, "ledger.db")

    real_now = S._now_utc
    clock = FrozenClock()
    S._now_utc = clock
    try:
        led, ds = build_stack(db_path, cfg)
        led.mint_to_pool("pool:reserve", 20000, "CVW-MINT-A",
                         "settlement")
        for who in ("ada", "bob", "carol"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 700),
                    ("usr:ada", "credit", 700)],
                   "manual:cvw-fund-ada", "window face funding ada")
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:bob", "credit", 500)],
                   "manual:cvw-fund-bob", "window face funding bob")
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:carol", "credit", 500)],
                   "manual:cvw-fund-carol",
                   "window face funding carol")

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

        # -- AC-CVW1: default zero-drift + window gate ------------------
        counts_before = ds_counts(ds.db_path)
        led_before = ledger_counts(db_path)
        default_env = ds.coverage_board()
        gate_codes = []
        gates_ok = True
        for bad in ("2026-13", "2026-00", "2026-1", "2026/10",
                    "2026-Q1", 202610, True, "2026-10\n",
                    " 2026-10", "2026-10 ", "26-10", "2026-100"):
            ok, code = expect_error(
                lambda b=bad: ds.coverage_board(b),
                S.E_DSB_BAD_WINDOW)
            gates_ok &= ok
            gate_codes.append(code if ok else "WRONG:" + str(code))
        counts_after_gate = ds_counts(ds.db_path)
        led_after_gate = ledger_counts(db_path)
        man_full = manual_board(ds.db_path)
        rows = default_env["coverage_board"]
        ok1 = (
            set(default_env.keys()) == ENV_KEYS
            and len(rows) == 3
            and all(set(r.keys()) == ROW_KEYS for r in rows)
            and all(r["subscribers"]
                    == man_full[r["dataset_key"]]["subscribers"]
                    and r["subscriptions"]
                    == man_full[r["dataset_key"]]["subscriptions"]
                    and r["deliveries"]
                    == man_full[r["dataset_key"]]["deliveries"]
                    for r in rows)
            and gates_ok
            and len(set(gate_codes)) == 1
            and counts_before == counts_after_gate
            and led_before == led_after_gate
            and default_env["disclaimer"] == DISCLAIMER
        )
        record("AC-CVW1", ok1,
               "default window=None keeps the full-window envelope "
               "exactly {coverage_board,disclaimer} with rows == "
               "manual full SQL GROUP BY cross (mobility {2hh,3subs,"
               "2dlv} / city-air {1,1,0} / city-parks {1,1,0}); 12 "
               "malformed windows (month-13, month-00, short, slash, "
               "quarterly form, int, bool, trailing newline, lead "
               "space, trailing space, 2-digit-year, long) all fail "
               "closed E_DSB_BAD_WINDOW before any read with zero "
               "side effects (ds counts %s, ledger %s)" %
               (json.dumps(counts_after_gate, sort_keys=True),
                json.dumps(led_after_gate, sort_keys=True)))

        # -- AC-CVW2: October window slice -----------------------------
        oct_env = ds.coverage_board("2026-10")
        man_oct = manual_board(ds.db_path, "2026-10")
        oct_by_key = {r["dataset_key"]: r
                      for r in oct_env["coverage_board"]}
        ok2 = (
            set(oct_env.keys()) == WENV_KEYS
            and oct_env["window"] == "2026-10"
            and len(oct_env["coverage_board"]) == 3
            and all(set(r.keys()) == ROW_KEYS
                    for r in oct_env["coverage_board"])
            and oct_by_key["city-mobility"]["subscribers"] == 2
            and oct_by_key["city-mobility"]["subscriptions"] == 2
            and oct_by_key["city-mobility"]["deliveries"] == 0
            and oct_by_key["city-air"]["subscribers"] == 1
            and oct_by_key["city-air"]["subscriptions"] == 1
            and oct_by_key["city-air"]["deliveries"] == 0
            and oct_by_key["city-parks"]["subscribers"] == 0
            and oct_by_key["city-parks"]["subscriptions"] == 0
            and oct_by_key["city-parks"]["deliveries"] == 0
            and all(r["subscribers"]
                    == man_oct[r["dataset_key"]]["subscribers"]
                    and r["subscriptions"]
                    == man_oct[r["dataset_key"]]["subscriptions"]
                    and r["deliveries"]
                    == man_oct[r["dataset_key"]]["deliveries"]
                    for r in oct_env["coverage_board"])
        )
        record("AC-CVW2", ok2,
               "October window: envelope adds exactly one 'window' "
               "key (additive family law); mobility {2hh,2subs,"
               "0dlv} (ada+bob October rows; November rows never "
               "leak in), city-air {1,1,0} (carol October row), "
               "city-parks {0,0,0} honest zero (carol's Q4 "
               "subscription recorded in November stays out); every "
               "row == manual prefix-SQL cross derivation")

        # -- AC-CVW3: November window + provenance separation ----------
        nov_env = ds.coverage_board("2026-11")
        man_nov = manual_board(ds.db_path, "2026-11")
        nov_by_key = {r["dataset_key"]: r
                      for r in nov_env["coverage_board"]}
        dlv_rows = sqlite3.connect(ds.db_path).execute(
            "SELECT delivery_ref, period_window, delivered_utc"
            " FROM dataset_deliveries ORDER BY delivery_ref"
        ).fetchall()
        ok3 = (
            set(nov_env.keys()) == WENV_KEYS
            and nov_env["window"] == "2026-11"
            and nov_by_key["city-mobility"]["subscribers"] == 1
            and nov_by_key["city-mobility"]["subscriptions"] == 1
            and nov_by_key["city-mobility"]["deliveries"] == 2
            and nov_by_key["city-parks"]["subscribers"] == 1
            and nov_by_key["city-parks"]["subscriptions"] == 1
            and nov_by_key["city-parks"]["deliveries"] == 0
            and nov_by_key["city-air"]["subscribers"] == 0
            and nov_by_key["city-air"]["subscriptions"] == 0
            and nov_by_key["city-air"]["deliveries"] == 0
            and all(r["subscribers"]
                    == man_nov[r["dataset_key"]]["subscribers"]
                    and r["subscriptions"]
                    == man_nov[r["dataset_key"]]["subscriptions"]
                    and r["deliveries"]
                    == man_nov[r["dataset_key"]]["deliveries"]
                    for r in nov_env["coverage_board"])
            and [list(r) for r in dlv_rows] ==
            [["dlv-ada-1101", "2026-11", NOV_TS],
             ["dlv-bob-1001", "2026-10", NOV_TS]]
        )
        record("AC-CVW3", ok3,
               "November window: mobility {1hh,1sub,2dlv} - the two "
               "delivery rows both carry November record stamps "
               "(dlv-ada-1101 period-window 2026-11 + dlv-bob-1001 "
               "period-window 2026-10: the provenance-separation "
               "probe - a delivery for the October period window "
               "recorded in November lands on the November board "
               "and never on October), city-parks {1,1,0} (carol "
               "Q4 row recorded in November), city-air {0,0,0} "
               "honest zero; every row == manual prefix-SQL cross")

        # -- AC-CVW4: honest-empty month --------------------------------
        empty_env = ds.coverage_board("2025-01")
        ok4 = (
            set(empty_env.keys()) == WENV_KEYS
            and empty_env["window"] == "2025-01"
            and len(empty_env["coverage_board"]) == 3
            and sorted(r["dataset_key"]
                       for r in empty_env["coverage_board"])
            == ["city-air", "city-mobility", "city-parks"]
            and all(r["subscribers"] == 0
                    and r["subscriptions"] == 0
                    and r["deliveries"] == 0
                    for r in empty_env["coverage_board"])
        )
        record("AC-CVW4", ok4,
               "month 2025-01 has no records anywhere: the board is "
               "the all-zero honest empty - all three registered "
               "datasets keep their dense zero rows (registry "
               "row-set authority holds inside a window; zero "
               "phantom rows, zero dropped rows), deterministic "
               "dataset_key ASC order at the all-tie")

        # -- AC-CVW5: cross-restart persistence --------------------------
        bat_pre = battery(ds)
        ds.close()
        led.close()
        led2, ds2 = build_stack(db_path, cfg)
        bat_post = battery(ds2)
        ok5 = all(bat_post[k] == bat_pre[k] for k in bat_pre)
        record("AC-CVW5", ok5,
               "two-piece restart (face.close + ledger.close -> new "
               "Ledger + new face over the same db paths): the full "
               "read battery (default + October + November + "
               "honest-empty) is byte-identical across the restart "
               "(battery sha16 %s) - read-time derivation, zero "
               "in-memory drift in every window face" %
               sha16(json.dumps(bat_pre, sort_keys=True)))

        # -- AC-CVW6: pure-read law + determinism ------------------------
        cnt_a = ds_counts(ds2.db_path)
        led_a = ledger_counts(db_path)
        bat_one = battery(ds2)
        bat_two = battery(ds2)
        cnt_b = ds_counts(ds2.db_path)
        led_b = ledger_counts(db_path)
        ok6 = (
            cnt_a == cnt_b and led_a == led_b
            and bat_one == bat_two
            and json.dumps(bat_one, sort_keys=True)
            == json.dumps(bat_pre, sort_keys=True)
        )
        record("AC-CVW6", ok6,
               "pure-read law: the full battery (default + three "
               "windows) leaves every ds table count and the ledger "
               "spend count untouched (%s / %s); double battery "
               "run byte-identical (sha16 %s) and equal to the "
               "pre-restart battery - zero RNG, zero time keys, "
               "registry-PK total order in every window" %
               (json.dumps(cnt_b, sort_keys=True),
                json.dumps(led_b, sort_keys=True),
                sha16(json.dumps(bat_one, sort_keys=True))))

        # -- AC-CVW7: hygiene -------------------------------------------
        src = io_read(os.path.join(BASE, "test_coverage_board_window"
                                          ".py")).decode("ascii")
        face_src = inspect.getsource(S.DatasetSubscriptionFace
                                     .coverage_board)
        import_lines = [ln.strip() for ln in
                        src.splitlines() if ln.strip().startswith(
                            "import ") or ln.strip().startswith(
                            "from ")]
        cfg_sha_after = sha16(io_read(os.path.join(BASE,
                                                   "config.json")))
        led_sha_after = sha16(io_read(os.path.join(BASE, "ledger.py")))
        ok7 = (
            cfg_sha_after == cfg_sha_before
            and led_sha_after == led_sha_before
            and S._SCHEMA == FROZEN_SCHEMA
            and "UPDATE" not in face_src
            and "INSERT" not in face_src
            and "DELETE" not in face_src
            and not any(word in ln for ln in import_lines
                        for word in ("urllib", "requests",
                                     "socket", "http"))
        )
        record("AC-CVW7", ok7,
               "hygiene: shipped config.json and ledger.py sha16 "
               "unchanged (%s / %s); the three CREATE TABLE "
               "statements byte-identical to the frozen schema "
               "anchor (zero schema touch); coverage_board source "
               "carries zero INSERT/UPDATE/DELETE (pure read "
               "face); suite source pure ASCII; real import lines "
               "carry zero network libs" %
               (cfg_sha_after, led_sha_after))

        ds2.close()
        led2.close()
    finally:
        S._now_utc = real_now

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d)" % (
        "PASS" if not failed else "FAIL",
        len(RESULTS) - len(failed), len(RESULTS)), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
