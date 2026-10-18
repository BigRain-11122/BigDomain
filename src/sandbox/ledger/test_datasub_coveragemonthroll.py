"""Coverage dual-board month-roll example window (BigDomain
R2030; the coverage month-window month-roll seat - the R2009
-reseed explore-queue row, criteria AC-CVMR1..AC-CVMR7
pre-registered in the state/queue/explore.md claim row before
this suite code existed; honesty law. The AC-CVMR prefix, the
suite filename and the registry row name were each git-grep
verified zero-occupied at claim time on 2026-10-18).

Month-roll lineage (R1861 banner_board roll / R1997 behavior
month-window / R2008 dual board / R2009 dual persist): the
dual board derives from record-time provenance stamps, so
this window drives the true product write path across a
simulated month boundary under the frozen clock (R1678 law) -
october writes accumulate the october window live (rolling
while in-month), the roll moment freezes the october window
byte-exact against every later november record (including an
october-PERIOD subscription recorded in november - the
provenance probe: the period window never decides the board
month), the november window keeps rolling, and the month-diff
presentation telescopes (additive metrics sum across windows,
households take the union). The freeze/roll state survives
two full-stack restarts byte-identical, and the november
window keeps rolling on the reopened instances.

Usage: python test_datasub_coveragemonthroll.py
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


def dual(face, w):
    return json.dumps(face.coverage_board_dual(w), sort_keys=True)


def zone_rows(env_text, zone):
    env = json.loads(env_text)
    return {r["dataset_key"]: json.dumps(r, sort_keys=True)
            for r in env[zone]}


def zone_order(env_text, zone):
    env = json.loads(env_text)
    return [r["dataset_key"] for r in env[zone]]


def row_fields(env_text, zone, key):
    row = json.loads(zone_rows(env_text, zone)[key])
    return (row["subscribers"], row["subscriptions"],
            row["deliveries"])


def manual_cross(zone, man):
    if set(man) != set(zone):
        return False
    for key, m in man.items():
        row = json.loads(zone[key])
        if not (row["subscribers"] == m["subscribers"]
                and row["subscriptions"] == m["subscriptions"]
                and row["deliveries"] == m["deliveries"]):
            return False
    return True


def all_row_keys_ok(env_text):
    env = json.loads(env_text)
    rows = (env["coverage_board"]
            + env["coverage_board_window"])
    return all(set(r.keys()) == ROW_KEYS for r in rows)


def build_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    face = S.DatasetSubscriptionFace(led, DISCLAIMER)
    return led, face


class FrozenClock(object):
    """Module-global clock injection (R1678 frozen-clock law):
    save/restore in finally, explicit stamps, zero real-clock
    dependency in every recorded row."""

    def __init__(self, stamp):
        self.stamp = stamp

    def __call__(self):
        return self.stamp


def main():
    tmp = tempfile.mkdtemp(prefix="covmonthroll-")
    cfg = json.loads(io_read(os.path.join(BASE, "config.json"))
                     .decode("utf-8"))
    cfg_sha_before = sha16(io_read(os.path.join(BASE, "config.json")))
    ds_sha_before = sha16(io_read(os.path.join(BASE, "datasub.py")))
    led_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))

    real_now = S._now_utc
    clock = FrozenClock(OCT_TS)
    S._now_utc = clock
    try:
        db_path = os.path.join(tmp, "ledger.db")
        led, ds = build_stack(db_path, cfg)
        led.mint_to_pool("pool:reserve", 20000, "CVMR-MINT-A",
                         "settlement")
        for who in ("ada", "bob", "carol", "dave", "erin", "frank"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        for who, amt in (("ada", 700), ("bob", 500), ("carol", 500),
                         ("dave", 400), ("erin", 400),
                         ("frank", 400)):
            led.adjust([("pool:reserve", "debit", amt),
                        ("usr:" + who, "credit", amt)],
                       "manual:cvmr-fund-" + who, "monthroll fund")

        ds.register_dataset("city-mobility", "City Mobility Index",
                            "monthly", 300, "digest-mob-1", False)
        ds.register_dataset("city-air", "City Air Quality Readings",
                            "monthly", 200, "digest-air-1", True)
        ds.register_dataset("city-parks", "City Parks Usage Digest",
                            "quarterly", 150, "digest-parks-1", True)

        # ---- AC-CVMR1: october live-roll anchor -----------------
        clock.stamp = OCT_TS
        ds.subscribe("usr:ada", "city-mobility", "2026-10",
                     "dsp-ada-1001")
        r1 = dual(ds, "2026-10")
        mob_r1 = row_fields(r1, "coverage_board_window",
                            "city-mobility")
        ds.subscribe("usr:bob", "city-mobility", "2026-10",
                     "dsp-bob-1001")
        r2 = dual(ds, "2026-10")
        mob_r2 = row_fields(r2, "coverage_board_window",
                            "city-mobility")
        ds.subscribe("usr:carol", "city-air", "2026-10",
                     "dsp-carol-air-1001")
        ds.deliver("usr:carol", "city-air", "2026-10",
                   "dlv-carol-air-1001")
        oct_final = dual(ds, "2026-10")
        oct_win = zone_rows(oct_final, "coverage_board_window")
        oct_full = zone_rows(oct_final, "coverage_board")
        man_oct = manual_board(ds.db_path, "2026-10")
        env1 = json.loads(oct_final)
        ok1 = (
            mob_r1 == (1, 1, 0)
            and mob_r2 == (2, 2, 0)
            and mob_r1 != mob_r2
            and set(env1.keys()) == DUAL_KEYS
            and env1["window"] == "2026-10"
            and all_row_keys_ok(oct_final)
            and zone_order(oct_final, "coverage_board_window")
            == ["city-mobility", "city-air", "city-parks"]
            and row_fields(oct_final, "coverage_board_window",
                           "city-mobility") == (2, 2, 0)
            and row_fields(oct_final, "coverage_board_window",
                           "city-air") == (1, 1, 1)
            and row_fields(oct_final, "coverage_board_window",
                           "city-parks") == (0, 0, 0)
            and all(oct_full[k] == oct_win[k]
                    for k in oct_win)
            and manual_cross(oct_win, man_oct)
            and ledger_counts(db_path)["spend"] == 3
        )
        record("AC-CVMR1", ok1,
               "october live-roll anchor: frozen-clock october"
               " writes accumulate the october window live"
               " (mobility window row (1,1,0) -> (2,2,0) between"
               " consecutive in-month reads, zero cache); october"
               " final window zone mobility (2,2,0) / air (1,1,1)"
               " / parks (0,0,0) with the decision order pinned;"
               " october-only world: full zone == window zone rows"
               " byte-equal (telescope base); manual record-time"
               " prefix SQL cross green; spend=3; battery sha16 "
               + sha16(oct_final))

        # ---- AC-CVMR2: roll moment + october freeze --------------
        clock.stamp = NOV_TS
        ds.subscribe("usr:ada", "city-mobility", "2026-11",
                     "dsp-ada-1101")
        ds.subscribe("usr:dave", "city-mobility", "2026-11",
                     "dsp-dave-1101")
        ds.subscribe("usr:erin", "city-mobility", "2026-10",
                     "dsp-erin-1001")
        ds.deliver("usr:ada", "city-mobility", "2026-11",
                   "dlv-ada-1101")
        oct_after_roll = dual(ds, "2026-10")
        nov_after_roll = dual(ds, "2026-11")
        frozen_ok = (
            json.loads(oct_after_roll)["coverage_board_window"]
            == json.loads(oct_final)["coverage_board_window"])
        env2 = json.loads(nov_after_roll)
        ok2 = (
            frozen_ok
            and set(env2.keys()) == DUAL_KEYS
            and env2["window"] == "2026-11"
            and all_row_keys_ok(nov_after_roll)
            and row_fields(nov_after_roll, "coverage_board_window",
                           "city-mobility") == (3, 3, 1)
            and row_fields(nov_after_roll, "coverage_board_window",
                           "city-air") == (0, 0, 0)
            and row_fields(nov_after_roll, "coverage_board_window",
                           "city-parks") == (0, 0, 0)
            and zone_order(nov_after_roll,
                           "coverage_board_window")
            == ["city-mobility", "city-air", "city-parks"]
            and row_fields(oct_after_roll,
                           "coverage_board_window",
                           "city-mobility") == (2, 2, 0)
            and ledger_counts(db_path)["spend"] == 6
        )
        record("AC-CVMR2", ok2,
               "roll moment: clock NOV; november records (ada nov"
               " sub + dave nov sub + erin october-PERIOD sub"
               " recorded in november = provenance probe + ada nov"
               " delivery) leave dual('2026-10') byte-frozen =="
               " the october final snapshot (zero permeation, the"
               " october-period erin row stays out of the october"
               " window - record-time law); dual('2026-11')"
               " window zone carries all new rows mobility (3,3,1)"
               " with air/parks honest zeros; spend 3->6; freeze"
               " sha16 " + sha16(oct_after_roll))

        # ---- AC-CVMR3: month-diff + telescoping ------------------
        nov_win = zone_rows(nov_after_roll, "coverage_board_window")
        full_rows = zone_rows(oct_after_roll, "coverage_board")
        man_nov = manual_board(ds.db_path, "2026-11")
        man_full = manual_board(ds.db_path, None)
        additive_ok = True
        union_notes = []
        for key in ("city-mobility", "city-air", "city-parks"):
            o = json.loads(oct_win[key])
            n = json.loads(nov_win[key])
            f = json.loads(full_rows[key])
            additive_ok &= (
                f["subscriptions"]
                == o["subscriptions"] + n["subscriptions"]
                and f["deliveries"]
                == o["deliveries"] + n["deliveries"])
            union_notes.append((key, o["subscribers"],
                                n["subscribers"],
                                f["subscribers"]))
        mob_union = union_notes[0]
        ok3 = (
            additive_ok
            and manual_cross(oct_win, man_oct)
            and manual_cross(nov_win, man_nov)
            and manual_cross(full_rows, man_full)
            and mob_union[1:] == (2, 3, 4)
            and mob_union[3] < mob_union[1] + mob_union[2]
            and json.loads(oct_after_roll)["window"] == "2026-10"
            and json.loads(nov_after_roll)["window"] == "2026-11"
            and "city-parks" in oct_win
            and "city-parks" in nov_win
        )
        record("AC-CVMR3", ok3,
               "month-diff telescoping: additive metrics full =="
               " oct + nov per dataset (mobility subs 5==2+3, dlv"
               " 1==0+1; air subs 1==1+0, dlv 1==1+0; parks 0);"
               " households union law: mobility full 4 ==" 
               " |oct{ada,bob} union nov{ada,dave,erin}| and 4 <"
               " 2+3 (ada counted in both window zones, once in"
               " the full zone - strict-inequality probe); manual"
               " SQL cross green for oct/nov/full zones; both"
               " envelopes carry the window echo; registry dense"
               " (parks honest zero rows in both windows)")

        # ---- AC-CVMR4: cross-restart byte-identical --------------
        bat_pre = {"oct": oct_after_roll,
                   "nov": nov_after_roll,
                   "full": json.dumps(ds.coverage_board(),
                                      sort_keys=True)}
        ds.close()
        led.close()
        led2, ds2 = build_stack(db_path, cfg)
        bat2 = {"oct": dual(ds2, "2026-10"),
                "nov": dual(ds2, "2026-11"),
                "full": json.dumps(ds2.coverage_board(),
                                   sort_keys=True)}
        diffs4 = [k for k in bat_pre if bat_pre[k] != bat2[k]]
        ok4 = not diffs4
        record("AC-CVMR4", ok4,
               "full-stack restart (ds close -> ledger close ->"
               " same db_path same cfg rebuild) replays the"
               " three-form battery byte-identical - the roll"
               " state (frozen october window + rolling november"
               " window + full zone) persists with zero in-memory"
               " drift (diff keys=%s, digest %s)"
               % (diffs4 if diffs4 else "none",
                  sha16(json.dumps(bat2, sort_keys=True))))

        # ---- AC-CVMR5: post-restart rolling + frozen -------------
        clock.stamp = NOV2_TS
        sub_frank = ds2.subscribe("usr:frank", "city-mobility",
                                  "2026-11", "dsp-frank-1101")
        oct_still = dual(ds2, "2026-10")
        nov_rolled = dual(ds2, "2026-11")
        frozen2 = (
            json.loads(oct_still)["coverage_board_window"]
            == json.loads(oct_after_roll)["coverage_board_window"])
        ok5a = (
            frozen2
            and sub_frank["price_cent"] == 300
            and sub_frank["spend_tx"]
            and row_fields(nov_rolled, "coverage_board_window",
                           "city-mobility") == (4, 4, 1)
            and row_fields(oct_still, "coverage_board",
                           "city-mobility") == (5, 6, 1)
            and ledger_counts(db_path)["spend"] == 7
            and led2.balance("usr:ada")["balance"] == 100
        )
        bat_post = {"oct": oct_still, "nov": nov_rolled,
                    "full": json.dumps(ds2.coverage_board(),
                                       sort_keys=True)}
        ds2.close()
        led2.close()
        led3, ds3 = build_stack(db_path, cfg)
        bat3 = {"oct": dual(ds3, "2026-10"),
                "nov": dual(ds3, "2026-11"),
                "full": json.dumps(ds3.coverage_board(),
                                   sort_keys=True)}
        diffs5 = [k for k in bat_post if bat_post[k] != bat3[k]]
        ok5 = ok5a and not diffs5
        record("AC-CVMR5", ok5,
               "post-restart continuation: instance2 NOV2 write"
               " (frank mobility 2026-11, true spend tx -> 7)"
               " rolls the november window zone mobility to"
               " (4,4,1) while dual('2026-10') stays byte-frozen"
               " against the AC-CVMR2 state and the full zone"
               " follows to (6,5,1); ada balance 100 cross; the"
               " second full-stack restart (third instance)"
               " replays the post-continuation battery"
               " byte-identical (diff keys=%s, digest %s)"
               % (diffs5 if diffs5 else "none",
                  sha16(json.dumps(bat3, sort_keys=True))))

        # ---- AC-CVMR6: pure-read law + gate zero-drift -----------
        cnt6_before = ds_counts(ds3.db_path)
        led6_before = ledger_counts(db_path)
        for _ in range(2):
            dual(ds3, "2026-10")
            dual(ds3, "2026-11")
            ds3.coverage_board()
            ds3.coverage_board("2026-10")
        cnt6_after_reads = ds_counts(ds3.db_path)
        led6_after_reads = ledger_counts(db_path)
        gates_ok = True
        gate_codes = set()
        for bad in (None, "2026-13", 202610, True, "2026/10",
                    "2026-10\n", "2026-10 "):
            ok_gate, code = expect_error(
                lambda b=bad: ds3.coverage_board_dual(b),
                S.E_DSB_BAD_WINDOW)
            gates_ok &= ok_gate
            gate_codes.add(str(code))
        for bad in ("2026-13", 202610, True):
            ok_gate, code = expect_error(
                lambda b=bad: ds3.coverage_board(b),
                S.E_DSB_BAD_WINDOW)
            gates_ok &= ok_gate
            gate_codes.add(str(code))
        cnt6_after = ds_counts(ds3.db_path)
        led6_after = ledger_counts(db_path)
        ok6 = (
            gates_ok and len(gate_codes) == 1
            and cnt6_before == cnt6_after_reads
            and led6_before == led6_after_reads
            and cnt6_after_reads == cnt6_after
            and led6_after_reads == led6_after
        )
        record("AC-CVMR6", ok6,
               "pure-read law: the read battery (dual oct/nov +"
               " default board + explicit month window, twice)"
               " leaves every ds table count and the ledger"
               " tx/spend counts untouched; the bad-window gate"
               " family (dual face: None, month-13, int, bool,"
               " slash, trailing newline, trailing space;"
               " coverage_board face: month-13, int, bool) all"
               " fails closed %s before any read with zero side"
               " effects (ds %s, ledger %s unchanged)"
               % (sorted(gate_codes),
                  json.dumps(cnt6_after, sort_keys=True),
                  json.dumps(led6_after, sort_keys=True)))

        # ---- AC-CVMR7: hygiene -----------------------------------
        cfg_sha_after = sha16(io_read(os.path.join(BASE,
                                                   "config.json")))
        ds_sha_after = sha16(io_read(os.path.join(BASE,
                                                  "datasub.py")))
        led_sha_after = sha16(io_read(os.path.join(BASE,
                                                   "ledger.py")))
        reg_src = io_read(os.path.join(
            os.path.dirname(BASE), "reconcile_all.py")).decode(
                "utf-8")
        reg_ok = ('"ledger-datasub-coveragemonthroll"'
                  in reg_src
                  and '"test_datasub_coveragemonthroll.py"), 7)'
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
        record("AC-CVMR7", ok7,
               "hygiene: shipped config.json/datasub.py/ledger.py"
               " sha16 unchanged (%s/%s/%s); the three CREATE"
               " TABLE statements byte-identical to the frozen"
               " schema anchor (zero schema touch); reconcile_all"
               " SUITES row ledger-datasub-coveragemonthroll"
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
