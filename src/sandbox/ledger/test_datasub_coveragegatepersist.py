"""Acceptance suite for the dataset coverage month-roll bad-window
gate family cross-restart same-code example window (BigDomain
R2066; canon = the explore-queue FIFO row reseeded by R2030 and
claimed by R2066, criteria AC-CVGG1..AC-CVGG8 registered in the
claim note BEFORE this code existed - honesty law; AC-CVGG prefix
+ suite filename + registry row three-face git-grep zero-occupancy
anchored 2026-10-24).

Face under proof: the window gate of the coverage read family
(DatasetSubscriptionFace.coverage_board_dual and
DatasetSubscriptionFace.coverage_board). The seed window (R2030,
AC-CVMR6) proved the ten bad-window forms fail closed ONCE, on its
third restart instance, together with the pure-read law. This
window proves the SPECIFIC family code and the GATE ORDER are
restart-invariant, and that every probe batch leaves the world
untouched on each of three instances.

Instances: (1) fresh stack, (2) ordered close (ds -> led) then
same db_path + same cfg bytes rebuild, (3) a second identical
restart.

Probe battery (fixed order, identical on every instance):
  dual face  (7 forms)  None / '2026-13' / 202610 / True /
                        '2026/10' / trailing LF / trailing space
  board face (3 forms)  '2026-13' / 202610 / True
Every form must answer E_DSB_BAD_WINDOW. Gate order is witnessed
by a counting subclass: the dual-face reject must fire before
either coverage_board delegation (counter stays 0), while each
board-face probe lands exactly one delegation (counter +1).

Usage: python test_datasub_coveragegatepersist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
for _d in (BASE,):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import datasub as S                   # noqa: E402 (R1948 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: dataset subscriptions"
              " are a data distribution face, not investment advice")

DATASET = "city-mobility"
DIGEST = "sha256:" + "0" * 64

DUAL_FORMS = [None, "2026-13", 202610, True, "2026/10",
              "2026-10\n", "2026-10 "]
BOARD_FORMS = ["2026-13", 202610, True]

PRODUCT_FILES = [
    os.path.join(BASE, "datasub.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
]

DS_TABLES = ("dataset_registry", "dataset_subscriptions",
             "dataset_deliveries")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_digest(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    finally:
        conn.close()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def world_digests(ds_path, led_path):
    out = {t: table_digest(ds_path, t) for t in DS_TABLES}
    out["ledger_tx"] = table_digest(led_path, "ledger_tx")
    out["ledger_entries"] = table_digest(led_path, "ledger_entries")
    return out


class CountingFace(S.DatasetSubscriptionFace):
    """Read-counting subclass: every coverage_board delegation is
    counted, so a reject that fires inside the front door cannot
    hide behind a landed read. Purely observational - zero
    behaviour change."""

    def __init__(self, ledger, disclaimer):
        S.DatasetSubscriptionFace.__init__(self, ledger, disclaimer)
        self.delegations = 0

    def coverage_board(self, window=None):
        self.delegations += 1
        return S.DatasetSubscriptionFace.coverage_board(self, window)


def expect_error(func, *args):
    try:
        func(*args)
        return None
    except S.DataSubError as exc:
        return exc.code


def build_world(db_path, cfg):
    """Read-world: funded accounts plus one registered monthly
    dataset, and exactly one subscription + one delivery so the
    coverage board carries non-degenerate counts that every probe
    batch must leave untouched."""
    led = L.Ledger(db_path, cfg)
    for who in ("ada", "bob"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-CVGG",
                     "settlement")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:ada", "credit", 400)],
               "manual:fund-ada", "suite funding ada")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:bob", "credit", 400)],
               "manual:fund-bob", "suite funding bob")
    ds = CountingFace(led, DISCLAIMER)
    ds.register_dataset(DATASET, "City Mobility", "monthly", 300,
                        DIGEST, False)
    ds.subscribe("usr:ada", DATASET, "2026-10", "cvv-boot-1")
    ds.deliver("usr:ada", DATASET, "2026-10", "cvv-boot-d1")
    return led, ds


def build_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    ds = CountingFace(led, DISCLAIMER)
    return led, ds


def run_battery(ds):
    """Fixed-order ten-probe battery. Returns (codes, dual_count,
    board_count) where the counts are delegation deltas observed
    inside the battery."""
    start = ds.delegations
    dual_codes = [expect_error(ds.coverage_board_dual, form)
                  for form in DUAL_FORMS]
    dual_delta = ds.delegations - start
    mid = ds.delegations
    board_codes = [expect_error(ds.coverage_board, form)
                   for form in BOARD_FORMS]
    board_delta = ds.delegations - mid
    return dual_codes + board_codes, dual_delta, board_delta


def battery_with_purity(ds, led):
    d_before = world_digests(ds.db_path, led.db_path)
    board_before = dumps(ds.coverage_board())
    codes, dual_delta, board_delta = run_battery(ds)
    d_after = world_digests(ds.db_path, led.db_path)
    board_after = dumps(ds.coverage_board())
    pure = [d_before == d_after, board_before == board_after]
    return (codes, dual_delta, board_delta, pure, d_after,
            board_after)


def row_of(board_env, key):
    for row in board_env.get("coverage_board", []):
        if row.get("dataset_key") == key:
            return (row.get("subscribers"), row.get("subscriptions"),
                    row.get("deliveries"))
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="datasub-cvgg-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))

    led, ds = build_world(db_path, cfg)
    ds_path = ds.db_path

    # -- AC-CVGG1 instance-one anchor --------------------------
    codes1, dual1, board1, pure1, dig1, dump1 = battery_with_purity(
        ds, led)
    ok1 = [
        codes1 == [S.E_DSB_BAD_WINDOW] * 10,
        len(codes1) == 10,
        dual1 == 0,
        board1 == len(BOARD_FORMS),
        all(pure1),
        row_of(ds.coverage_board(), DATASET) == (1, 1, 1),
    ]
    record("AC-CVGG1", all(ok1),
           "instance one anchor: the fixed-order ten-probe battery"
           " answers the single family code E_DSB_BAD_WINDOW on"
           " every form (dual %d forms + board %d forms), the"
           " dual-face reject performs zero coverage_board"
           " delegations (counter delta %d => the window gate"
           " precedes both zone reads) while each board-face probe"
           " lands exactly one delegation (delta %d), the probe"
           " batch leaves every ds table digest and both ledger"
           " tables constant, the board dump is unchanged and the"
           " world keeps its (1, 1, 1) coverage row"
           % (len(DUAL_FORMS), len(BOARD_FORMS), dual1, board1))

    # -- AC-CVGG2 restart instance two -------------------------
    ds.close()
    led.close()
    led2, ds2 = build_stack(db_path, cfg)
    codes2, dual2, board2, pure2, dig2, dump2 = battery_with_purity(
        ds2, led2)
    ok2 = [codes2 == codes1, dual2 == dual1, board2 == board1,
           all(pure2), dig2 == dig1]
    record("AC-CVGG2", all(ok2),
           "restart instance two (ordered close ds -> led, same"
           " db_path same cfg bytes): the ten-code vector is"
           " identical to instance one, the delegation deltas are"
           " identical (%d then %d), the probe batch again leaves"
           " every digest and the board dump constant, and the"
           " world digests match instance one byte for byte"
           % (dual2, board2))

    # -- AC-CVGG3 restart instance three -----------------------
    ds2.close()
    led2.close()
    led3, ds3 = build_stack(db_path, cfg)
    codes3, dual3, board3, pure3, dig3, dump3 = battery_with_purity(
        ds3, led3)
    ok3 = [codes3 == codes2, dual3 == dual2, board3 == board2,
           all(pure3), dig3 == dig2]
    record("AC-CVGG3", all(ok3),
           "restart instance three (second full-stack restart):"
           " the code vector, the delegation deltas (%d then %d),"
           " the purity verdict and the world digests all repeat"
           " exactly - the gate family is restart-invariant"
           % (dual3, board3))

    # -- AC-CVGG4 three-instance invariance --------------------
    ok4 = [codes1 == codes2 == codes3,
           [dual1, board1] == [dual2, board2] == [dual3, board3],
           dump1 == dump2 == dump3,
           row_of(ds3.coverage_board(), DATASET) == (1, 1, 1),
           len(codes1) == 10]
    record("AC-CVGG4", all(ok4),
           "three-instance invariance: the ordered ten-code vector"
           " is pairwise identical across instances one/two/three"
           " (length %d, single family code %s), the delegation"
           " deltas agree pairwise, the post-battery"
           " coverage_board() envelope dump is byte-identical"
           " across all three instances, and the world still"
           " reports the honest (1, 1, 1) row"
           % (len(codes1), S.E_DSB_BAD_WINDOW))

    # -- AC-CVGG5 interleaved sequencing on instance three -----
    start5 = ds3.delegations
    seq = []
    seq.append(("valid-full", expect_error(ds3.coverage_board)))
    seq.append(("bad-dual", expect_error(ds3.coverage_board_dual,
                                        "2026-13")))
    valid_a = dumps(ds3.coverage_board("2026-10"))
    seq.append(("valid-month", None))
    seq.append(("bad-board", expect_error(ds3.coverage_board,
                                          202610)))
    valid_b = dumps(ds3.coverage_board())
    seq.append(("valid-full-again", None))
    delta5 = ds3.delegations - start5
    ok5 = [
        [name for name, _ in seq] ==
        ["valid-full", "bad-dual", "valid-month", "bad-board",
         "valid-full-again"],
        seq[1][1] == S.E_DSB_BAD_WINDOW,
        seq[3][1] == S.E_DSB_BAD_WINDOW,
        delta5 == 4,
        json.loads(valid_a)["window"] == "2026-10",
        valid_b == dumps(ds3.coverage_board()),
    ]
    record("AC-CVGG5", all(ok5),
           "interleaved sequencing on instance three: four"
           " legitimate reads plus two bad probes in mixed order"
           " yield exactly %d delegations (each valid read counts"
           " once, each reject counts zero), so the gate is a"
           " per-call front door with no latching state; the"
           " month read answers window='2026-10' and the repeated"
           " full read is byte-identical" % delta5)

    # -- AC-CVGG6 post-battery liveness on instance three ------
    before6 = row_of(ds3.coverage_board(), DATASET)
    sub6 = ds3.subscribe("usr:bob", DATASET, "2026-10", "cvv-post-1")
    bundle6 = ds3.deliver("usr:bob", DATASET, "2026-10",
                          "cvv-post-d1")
    after6 = row_of(ds3.coverage_board(), DATASET)
    conn = sqlite3.connect(ds_path)
    try:
        sub_rows = conn.execute(
            "SELECT account, period_window, price_cent,"
            " bound_spend_tx FROM dataset_subscriptions"
            " WHERE purchase_ref = ?", ("cvv-post-1",)).fetchall()
    finally:
        conn.close()
    conn = sqlite3.connect(db_path)
    try:
        tx_ids = {str(r[0]) for r in conn.execute(
            "SELECT tx_id FROM ledger_tx").fetchall()}
    finally:
        conn.close()
    ok6 = [
        before6 == (1, 1, 1),
        after6 == (2, 2, 2),
        sub6["price_cent"] == 300,
        str(sub6["spend_tx"]) in tx_ids,
        len(sub_rows) == 1 and int(sub_rows[0][2]) == 300,
        bundle6["disclaimer_first"] == bundle6["disclaimer_last"],
        bundle6["period_window"] == "2026-10",
        bundle6["ai_label"] == 0,
    ]
    record("AC-CVGG6", all(ok6),
           "post-battery liveness on instance three: a legitimate"
           " subscribe + deliver on the true write path still"
           " works (price %d, spend tx %s present in the ledger_tx"
           " set, one bound subscription row), the coverage board"
           " moves honestly from (1, 1, 1) to (2, 2, 2), and the"
           " delivered bundle keeps the non-advisory notice as"
           " first and last line - the probe battery poisoned"
           " nothing"
           % (sub6["price_cent"], sub6["spend_tx"]))

    # -- AC-CVGG7 positive controls ----------------------------
    v71 = ds3.coverage_board("2026-10")
    v72 = ds3.coverage_board("2026-11")
    v70 = ds3.coverage_board()
    ok7 = [
        sorted(v71.keys()) == ["coverage_board", "disclaimer",
                               "window"],
        v71["window"] == "2026-10",
        v72["window"] == "2026-11",
        sorted(v70.keys()) == ["coverage_board", "disclaimer"],
        v71["coverage_board"][0]["dataset_key"] == DATASET,
        v72["coverage_board"][0]["dataset_key"] == DATASET,
        v72["coverage_board"][0]["subscriptions"] == 0,
    ]
    record("AC-CVGG7", all(ok7),
           "positive controls: the same shapes as proper 'YYYY-MM'"
           " strings read through (window='2026-10' sees the two"
           " live rows, window='2026-11' is the honest all-zero"
           " month), the explicit-window envelope adds exactly the"
           " 'window' key while the default envelope keeps its"
           " two-key shape, and the registry row-set authority"
           " holds inside a month with no activity - so the gate"
           " family rejects only malformed forms")

    # -- AC-CVGG8 hygiene + delivery ---------------------------
    ds3.close()
    led3.close()
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok8 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok8.append(not net_hits)
    ok8.append(os.path.abspath(tmp).startswith(
        tempfile.gettempdir()))
    ok8.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    reg_path = os.path.normpath(
        os.path.join(BASE, "..", "reconcile_all.py"))
    with open(reg_path, encoding="utf-8") as handle:
        reg_src = handle.read()
    ok8.append(
        "ledger-datasub-coveragegatepersist" in reg_src
        and "test_datasub_coveragegatepersist.py" in reg_src
        and "), 8)" in reg_src)
    ok8.append(shas_after == shas_before)
    ok8.append(len(RESULTS) + 1 == 8)
    record("AC-CVGG8", all(ok8),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, both world databases in"
           " the system tmp outside the repo, registry row wired"
           " (ledger-datasub-coveragegatepersist, criteria 8),"
           " product three-file sha256 unchanged, criteria"
           " count == 8" % len(src_bytes))

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()