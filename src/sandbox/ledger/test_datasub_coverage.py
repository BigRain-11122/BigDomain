"""Acceptance suite for the dataset subscription coverage
board read face (BigDomain explore queue, claimed round R1982;
canon = the "dataset subscription coverage board" row). Asserts
the pre-registered criteria AC-CVB1..AC-CVB7 from the R1982
explore-queue claim row (criteria were registered in
state/queue/explore.md before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Platform-side posture carried over from R1764: dataset registry
and subscription rows contain zero resident free text, so this
board has no msgSecCheck access point; this test source stays
pure ASCII per the encoding discipline.

Usage: python test_datasub_coverage.py
"""

import hashlib
import inspect
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
import datasub as S                   # noqa: E402 (R1764 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the dataset coverage"
              " board is a pure-read derived statistic, not"
              " investment advice")

ROW_KEYS = {"dataset_key", "title", "period", "ai_label",
            "subscribers", "subscriptions", "deliveries"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def build_world(tmp):
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    ds = S.DatasetSubscriptionFace(led, DISCLAIMER)
    return led, ds


def main():
    tmp = tempfile.mkdtemp(prefix="datasub-coverage-ac-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_sha_before = sha_file(cfg_path)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))

    led, ds = build_world(tmp)
    conn = sqlite3.connect(led.db_path)
    ds_conn = sqlite3.connect(ds.db_path)

    led.mint_to_pool("pool:reserve", 5000, "SETTLE-CVB-A", "settlement")
    for who in ("ada", "bob", "cy"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)

    # registry: two subscribed datasets (mixed ai flags / periods)
    # plus two never-subscribed datasets (honest zero rows)
    ds.register_dataset("ds-transit", "Transit Flow", "monthly", 10,
                        "digest-transit-aaaa", False)
    ds.register_dataset("ds-queues", "Queue Depth", "quarterly", 25,
                        "digest-queues-bbbb", True)
    ds.register_dataset("ds-parks", "Parks Usage", "monthly", 8,
                        "digest-parks-cccc", False)
    ds.register_dataset("ds-air", "Air Index", "quarterly", 12,
                        "digest-air-dddd", True)

    # subscriptions: bob holds TWO windows of ds-queues (the
    # household-dedup world); ds-queues 3 rows / 2 households vs
    # ds-transit 2 rows / 2 households -> 2==2 household tie
    # broken by subscriptions 3 > 2
    ds.subscribe("usr:ada", "ds-transit", "2026-09", "cvb-s1")
    ds.subscribe("usr:cy", "ds-transit", "2026-10", "cvb-s4")
    ds.subscribe("usr:ada", "ds-queues", "2026-Q4", "cvb-s3")
    ds.subscribe("usr:bob", "ds-queues", "2026-Q3", "cvb-s5")
    ds.subscribe("usr:bob", "ds-queues", "2026-Q4", "cvb-s6")

    # deliveries: re-downloads with distinct refs are legal new
    # rows (the R1764 delivery judgement); ds-transit 3, ds-queues 4
    ds.deliver("usr:ada", "ds-transit", "2026-09", "cvb-d1")
    ds.deliver("usr:ada", "ds-transit", "2026-09", "cvb-d2")
    ds.deliver("usr:cy", "ds-transit", "2026-10", "cvb-d3")
    ds.deliver("usr:ada", "ds-queues", "2026-Q4", "cvb-d4")
    ds.deliver("usr:bob", "ds-queues", "2026-Q3", "cvb-d5")
    ds.deliver("usr:bob", "ds-queues", "2026-Q4", "cvb-d6")
    ds.deliver("usr:bob", "ds-queues", "2026-Q4", "cvb-d7")

    # pre-read table digests (pure-read law baseline)
    pre = {t: table_digest(ds_conn, t) for t in
           ("dataset_registry", "dataset_subscriptions",
            "dataset_deliveries")}
    pre_ledger_tx = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]

    env = ds.coverage_board()
    board = env["coverage_board"]

    # -- AC-CVB1 row-set authority + honest zeros ------------------------
    reg_keys = {r[0] for r in ds_conn.execute(
        "SELECT dataset_key FROM dataset_registry")}
    row_keys = {row["dataset_key"] for row in board}
    zero_rows = [row for row in board
                 if row["dataset_key"] in ("ds-parks", "ds-air")]
    ok1 = (row_keys == reg_keys and len(board) == len(reg_keys) == 4
           and len(zero_rows) == 2
           and all(r["subscribers"] == 0 and r["subscriptions"] == 0
                   and r["deliveries"] == 0 for r in zero_rows)
           and set(env.keys()) == {"coverage_board", "disclaimer"}
           and all(set(row.keys()) == ROW_KEYS for row in board))
    record("AC-CVB1", ok1,
           "rows=%d==registry=%d zero-rows=%d envelope-two-keys=%s"
           " seven-key-exact=%s"
           % (len(board), len(reg_keys), len(zero_rows),
              set(env.keys()) == {"coverage_board", "disclaimer"},
              all(set(row.keys()) == ROW_KEYS for row in board)))

    # -- AC-CVB2 aggregation + household dedup + cross-face --------------
    indep = {r[0]: (int(r[1]), int(r[2]), int(r[3])) for r in
             ds_conn.execute(
                 "SELECT s.dataset_key, COUNT(*), COUNT(DISTINCT"
                 " s.account), (SELECT COUNT(*) FROM"
                 " dataset_deliveries d WHERE d.dataset_key ="
                 " s.dataset_key) FROM dataset_subscriptions s"
                 " GROUP BY s.dataset_key")}
    ok2 = True
    for row in board:
        key = row["dataset_key"]
        if key in indep:
            n_rows, n_hh, n_del = indep[key]
            ok2 = ok2 and row["subscriptions"] == n_rows
            ok2 = ok2 and row["subscribers"] == n_hh
            ok2 = ok2 and row["deliveries"] == n_del
        view = ds.dataset_view(key)
        ok2 = ok2 and row["subscriptions"] == view["subscriber_count"]
    transit_row = [row for row in board
                   if row["dataset_key"] == "ds-transit"][0]
    queues_row = [row for row in board
                  if row["dataset_key"] == "ds-queues"][0]
    ok2 = (ok2 and queues_row["subscribers"] == 2
           and queues_row["subscriptions"] == 3
           and queues_row["deliveries"] == 4
           and transit_row["subscribers"] == 2
           and transit_row["subscriptions"] == 2
           and transit_row["deliveries"] == 3)
    record("AC-CVB2", ok2,
           "groupby-equal=%s cross-face-dataset_view=%s"
           " queues-dedup hh=2-of-3rows=%s transit-2hh-2rows=%s"
           % (ok2, ok2,
              (queues_row["subscribers"],
               queues_row["subscriptions"]) == (2, 3),
              (transit_row["subscribers"],
               transit_row["subscriptions"]) == (2, 2)))

    # -- AC-CVB3 deterministic three-key order ---------------------------
    order = [row["dataset_key"] for row in board]
    expected_order = ["ds-queues", "ds-transit", "ds-air", "ds-parks"]
    first2 = [row["dataset_key"] for row in board[:2]]
    ok3 = (order == expected_order and first2 == ["ds-queues",
                                                  "ds-transit"])
    again = ds.coverage_board()["coverage_board"]
    blob_a = json.dumps(env, sort_keys=True)
    blob_b = json.dumps({"coverage_board": again,
                         "disclaimer": env["disclaimer"]},
                        sort_keys=True)
    ok3 = ok3 and blob_a == blob_b
    record("AC-CVB3", ok3,
           "order=%s sub-tie-broken-3>2=%s zero-group-id-asc=%s"
           " double-dumps-identical=%s"
           % (order, first2 == ["ds-queues", "ds-transit"],
              order[2:] == ["ds-air", "ds-parks"], blob_a == blob_b))

    # -- AC-CVB4 disclaimer resident + ai_label presentation -------------
    ai_expect = {"ds-transit": 0, "ds-queues": 1,
                 "ds-parks": 0, "ds-air": 1}
    ok4 = (env["disclaimer"] == ds.disclaimer
           and all(row["ai_label"] == ai_expect[row["dataset_key"]]
                   for row in board)
           and {row["ai_label"] for row in board} == {0, 1})
    record("AC-CVB4", ok4,
           "disclaimer-resident=%s ai-label-0-1-dual=%s"
           % (env["disclaimer"] == ds.disclaimer,
              {row["ai_label"] for row in board} == {0, 1}))

    # -- AC-CVB5 pure-read law --------------------------------------------
    post = {t: table_digest(ds_conn, t) for t in
            ("dataset_registry", "dataset_subscriptions",
             "dataset_deliveries")}
    post_ledger_tx = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    method_src = inspect.getsource(S.DatasetSubscriptionFace.
                                   coverage_board)
    write_words = [w for w in ("INSERT", "UPDATE ", "DELETE",
                               "CREATE", "ALTER")
                   if w in method_src]
    ok5 = (pre == post and pre_ledger_tx == post_ledger_tx
           and not write_words
           and ds.coverage_board()["coverage_board"] == board)
    record("AC-CVB5", ok5,
           "three-table digests stable=%s ledger_tx %d==%d"
           " method-write-words=%s re-read-identical=%s"
           % (pre == post, pre_ledger_tx, post_ledger_tx,
              write_words,
              ds.coverage_board()["coverage_board"] == board))

    # -- AC-CVB6 zero-registry honest empty board -------------------------
    tmp2 = tempfile.mkdtemp(prefix="datasub-coverage-empty-")
    led2, ds2 = build_world(tmp2)
    empty_env = ds2.coverage_board()
    ok6 = (empty_env["coverage_board"] == []
           and empty_env["disclaimer"] == ds2.disclaimer)
    record("AC-CVB6", ok6,
           "empty-board=%s disclaimer-present=%s"
           % (empty_env["coverage_board"] == [],
              empty_env["disclaimer"] == ds2.disclaimer))
    ds2.close()
    led2.close()

    # -- AC-CVB7 hygiene ---------------------------------------------------
    src_path = os.path.abspath(__file__)
    with open(src_path, "rb") as handle:
        src_bytes = handle.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    net_hits = []
    with open(src_path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                if any(word in stripped for word in
                       ("urllib", "requests", "socket", "http")):
                    net_hits.append(stripped)
    cfg_sha_after = sha_file(cfg_path)
    mod_path = os.path.join(BASE, "datasub.py")
    with open(mod_path, "rb") as handle:
        mod_ascii = all(b < 128 for b in handle.read())
    tmp_outside = not os.path.abspath(tmp).startswith(repo_root)
    ok7 = (ascii_ok and not net_hits
           and cfg_sha_before == cfg_sha_after and tmp_outside
           and mod_ascii)
    record("AC-CVB7", ok7,
           "src-ascii=%s net-imports=%d config-sha-stable=%s"
           " tmp-outside-repo=%s module-ascii=%s"
           % (ascii_ok, len(net_hits),
              cfg_sha_before == cfg_sha_after, tmp_outside,
              mod_ascii))

    ds.close()
    led.close()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed),
                              len(RESULTS)), flush=True)
    if failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
