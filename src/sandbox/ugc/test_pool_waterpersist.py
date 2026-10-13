"""Acceptance suite for the UGC pool-water read-face family
cross-restart persistence example window (BigDomain R1929; canon =
the R1926-reseeded tech-queue row claimed by R1929 after the former
queue head - the lobby two-board persist row - was duplicate-closed
against the in-book R1891 AC-S32..S38 store-level board persist
seats plus the R1915 AC-S49..S54 protocol-face seats).

Dedup adjudication (claim line, honesty law): R1913 AC-DR9 already
pins store.pool_water_levels() byte-identical across a FULL
pipeline-stack restart in the drain world (one criterion inside the
drain-recovery suite; carrier = UGCPipeline close -> fresh
UGCPipeline, pinned levels are drain-window levels). The genuine
zero-in-book surfaces pinned here:

  - the seed row's named carrier: UGCStore close -> new UGCStore
    over the same ugc.db (store-level restart, persist family law);
  - pool_water_delta(caller-held snapshot) across restart: the
    two-call differential face has zero cross-restart seats
    (R1913 covers pipeline.last_water_delta - a different
    mechanism, asserted None after restart - not the store delta);
  - post-restart NEW noise / gray / verdict flows through the real
    product path recomputing both faces zero-cache (R1913's
    post-restart rows are drain-recovery rows);
  - second restart, third-instance sequential reads byte-identical.

Criteria AC-PWP1..AC-PWP7 were pre-registered in
state/queue/tech.md at claim time (R1929, before this code
existed; honesty law; AC-PWP prefix git-grep zero-occupancy
anchored 2026-10-13; AC-DW1..DW7 belong to the single-instance
delta suite and are not re-registered here).

Suite-only round: zero product-code changes (store.py sha256
double-proven unchanged). World = the test_pool_delta twin
build_world (all three noise reasons, gray suspended + both
verdicts, clean pooled control rows) through the REAL pipeline
path; post-restart flows ride a fresh pipeline on the same db.

Usage: python test_pool_waterpersist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pipeline as P                     # noqa: E402 (real-flow world)
import store as UGC                       # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7
TEST_DISCLAIMER = ("sandbox non-advisory standing disclaimer "
                   "(pool-water persist probe)")
TABLES = ("ugc_events", "ugc_items", "review_queue",
          "ugc_ingest_log", "gate_receipts")
EMOJI = "\U0001F44D\U0001F44D"

PRODUCT_FILES = [os.path.join(BASE, "store.py")]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_counts(db):
    conn = sqlite3.connect(db)
    try:
        return {t: int(conn.execute(
            "SELECT COUNT(*) FROM %s" % t).fetchone()[0]) for t in TABLES}
    finally:
        conn.close()


def manual_cells(db):
    """Independent second derivation over the same tables: noise =
    ugc_events payload noise-flag rows (count + by_reason, json
    parsed test-side), suspended = review_queue verdict IS NULL
    count, verdicted = non-null verdict GROUP BY."""
    conn = sqlite3.connect(db)
    try:
        by_reason = {}
        noise_total = 0
        for (raw,) in conn.execute(
                "SELECT payload_json FROM ugc_events"):
            payload = json.loads(raw) if raw else {}
            if isinstance(payload, dict) and payload.get("noise"):
                noise_total += 1
                reason = str(payload.get("noise_reason") or "unknown")
                by_reason[reason] = by_reason.get(reason, 0) + 1
        suspended = int(conn.execute(
            "SELECT COUNT(*) FROM review_queue"
            " WHERE verdict IS NULL").fetchone()[0])
        verdicted = {"pass": 0, "risky": 0}
        for verdict, n in conn.execute(
                "SELECT verdict, COUNT(*) FROM review_queue"
                " WHERE verdict IS NOT NULL GROUP BY verdict"):
            verdicted[str(verdict)] = int(n)
        return (noise_total,
                {k: by_reason[k] for k in sorted(by_reason)},
                suspended, verdicted)
    finally:
        conn.close()


def face_for(db):
    """Store read instance wired with the standing disclaimer."""
    return UGC.UGCStore(db, disclaimer=TEST_DISCLAIMER)


def build_world(cfg, db):
    """Real-flow world through the pipeline (test_pool_delta twin):
    all three noise reasons, gray suspended + both verdicts, clean
    pooled control rows."""
    wcfg = json.loads(json.dumps(cfg))
    wcfg["noise"] = dict(wcfg.get("noise") or {}, flood_max_submissions=2)
    pipe = P.UGCPipeline(wcfg, db)
    gw = wcfg["gate"]["gray_words"][0]
    kw = wcfg["routing"]["rules"][0]["keywords"][0]

    pipe.submit("avatar_intake", "C-dw1", EMOJI)
    pipe.submit("avatar_intake", "C-dw2", "ab")
    pipe.submit("avatar_intake", "C-dw3", "flood probe one")
    pipe.submit("avatar_intake", "C-dw3", "flood probe two")
    pipe.submit("avatar_intake", "C-dw3", "flood probe three")
    pipe.submit("avatar_intake", "C-dw4", "gray park " + gw)
    gray2 = pipe.submit("avatar_intake", "C-dw5",
                        "gray risky " + gw + " park")
    try:
        pipe.review_verdict(gray2["evt_id"], "risky")
    except UGC.PipelineError:
        pass  # risky verdict rejects publication; verdict row stays
    gray3 = pipe.submit("avatar_intake", "C-dw6",
                        "gray pass " + gw + " park")
    pipe.review_verdict(gray3["evt_id"], "pass")
    pipe.submit("avatar_intake", "C-dw7", "clean idea about " + kw)
    pipe.submit("avatar_intake", "C-dw8",
                "clean second idea about " + kw)
    return pipe, gw, kw


def hand_delta(prev_env, cur_env):
    """Test-side independent re-derivation of the flat cell delta
    (test_pool_delta twin helper)."""
    cells = {}
    pn = prev_env["pool_water_levels"]["noise"]
    cn = cur_env["pool_water_levels"]["noise"]
    pr = prev_env["pool_water_levels"]["review"]
    cr = cur_env["pool_water_levels"]["review"]
    for key, now, then in (
            ("noise.total", cn["total"], pn["total"]),
            ("review.suspended", cr["suspended"], pr["suspended"])):
        if now - then:
            cells[key] = now - then
    for key in sorted(set(pn["by_reason"]) | set(cn["by_reason"])):
        diff = cn["by_reason"].get(key, 0) - pn["by_reason"].get(key, 0)
        if diff:
            cells["noise.by_reason." + key] = diff
    for key in sorted(set(pr["verdicted"]) | set(cr["verdicted"])):
        diff = cr["verdicted"].get(key, 0) - pr["verdicted"].get(key, 0)
        if diff:
            cells["review.verdicted." + key] = diff
    return {k: cells[k] for k in sorted(cells)}


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-pwp-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg_sha = sha256_file(os.path.join(BASE, "config.json"))
    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}
    db = os.path.join(tmp, "world.db")

    # ---- AC-PWP1: control anchor, pre-close pinning -------------------
    pipe, gw, kw = build_world(cfg, db)
    store = face_for(db)
    snap_levels = store.pool_water_levels()
    d_self = store.pool_water_delta(snap_levels)
    n, reasons, susp, verd = manual_cells(db)
    ok1 = []
    ok1.append(set(snap_levels) == {"pool_water_levels", "total",
                                    "disclaimer", "persistent"})
    ok1.append(snap_levels["pool_water_levels"]["noise"]
               == {"total": 3, "by_reason": {"emoji_only": 1,
                                              "flooding": 1,
                                              "too_short": 1}})
    ok1.append(snap_levels["pool_water_levels"]["review"]
               == {"suspended": 1, "verdicted": {"pass": 1,
                                                 "risky": 1}})
    ok1.append(snap_levels["total"] == 4
               and snap_levels["persistent"] is True
               and snap_levels["disclaimer"] == TEST_DISCLAIMER)
    ok1.append((n, reasons, susp, verd) == (
        3, {"emoji_only": 1, "flooding": 1, "too_short": 1},
        1, {"pass": 1, "risky": 1}))
    ok1.append(d_self["pool_water_delta"] == {}
               and d_self["total_delta"] == 0
               and set(d_self) == {"pool_water_delta", "total_delta",
                                   "disclaimer", "persistent"})
    record("AC-PWP1", all(ok1),
           "pre-close pinning: levels noise 3 (emoji/flood/short"
           " 1 each), suspended 1, verdicted pass1 risky1, total 4"
           " == manual SQL cross; steady self-delta {} and"
           " total_delta 0; envelope keys exact")
    snap_pre = {"levels": dumps(snap_levels),
                "delta_self": dumps(d_self)}

    # ---- AC-PWP2: store-level restart byte identity -------------------
    store.close()
    store = face_for(db)
    lv2 = store.pool_water_levels()
    d2 = store.pool_water_delta(snap_levels)
    ok2 = (dumps(lv2) == snap_pre["levels"]
           and dumps(d2) == snap_pre["delta_self"])
    record("AC-PWP2", ok2,
           "UGCStore close -> new instance over the same ugc.db:"
           " reopened levels byte-identical to the pre-close"
           " snapshot and delta(caller-held pre-close snapshot)"
           " re-derived as the same steady {} / total_delta 0"
           " (zero in-memory drift in both derived read faces)")

    # ---- AC-PWP3: post-restart new noise + gray flows recompute -------
    pipe.submit("avatar_intake", "C-pwp9", EMOJI)
    gray_new = pipe.submit("avatar_intake", "C-pwp10",
                           "late gray park " + gw)
    lv3 = store.pool_water_levels()
    d3 = store.pool_water_delta(snap_levels)
    n3, reasons3, susp3, verd3 = manual_cells(db)
    ok3 = []
    ok3.append(lv3["pool_water_levels"]["noise"]
               == {"total": 4, "by_reason": {"emoji_only": 2,
                                             "flooding": 1,
                                             "too_short": 1}})
    ok3.append(lv3["pool_water_levels"]["review"]["suspended"] == 2
               and lv3["total"] == 6)
    ok3.append(d3["pool_water_delta"]
               == {"noise.by_reason.emoji_only": 1,
                   "noise.total": 1, "review.suspended": 1}
               and d3["total_delta"] == 2)
    ok3.append(d3["pool_water_delta"]
               == hand_delta(snap_levels, lv3))
    ok3.append((n3, reasons3, susp3, verd3) == (
        4, {"emoji_only": 2, "flooding": 1, "too_short": 1},
        2, {"pass": 1, "risky": 1}))
    record("AC-PWP3", all(ok3),
           "post-restart real-path flows (new emoji noise row + new"
           " gray row through the same-db pipeline): levels"
           " recomputed zero-cache (noise 3->4, emoji_only 1->2,"
           " suspended 1->2, total 4->6), delta vs the same"
           " caller-held pre-close snapshot = {emoji_only +1,"
           " noise.total +1, review.suspended +1} total_delta 2 =="
           " independent hand delta + manual SQL cross")

    # ---- AC-PWP4: verdict flow recompute, change-only across restart -
    pipe.review_verdict(gray_new["evt_id"], "pass")
    lv4 = store.pool_water_levels()
    d4 = store.pool_water_delta(snap_levels)
    n4, reasons4, susp4, verd4 = manual_cells(db)
    ok4 = []
    ok4.append(lv4["pool_water_levels"]["review"]
               == {"suspended": 1, "verdicted": {"pass": 2,
                                                 "risky": 1}}
               and lv4["total"] == 5)
    ok4.append(d4["pool_water_delta"]
               == {"noise.by_reason.emoji_only": 1,
                   "noise.total": 1, "review.verdicted.pass": 1}
               and d4["total_delta"] == 1)
    ok4.append("review.suspended" not in d4["pool_water_delta"])
    ok4.append(d4["pool_water_delta"]
               == hand_delta(snap_levels, lv4))
    ok4.append((n4, susp4, verd4) == (
        4, 1, {"pass": 2, "risky": 1}))
    record("AC-PWP4", all(ok4),
           "verdict flow on the new gray row (review_verdict pass):"
           " suspended 2->1, verdicted pass 1->2 recomputed on the"
           " restarted instance; delta vs the same snapshot ="
           " {emoji_only +1, noise.total +1, verdicted.pass +1}"
           " total_delta 1 with the net-zero suspended cell omitted"
           " (change-only semantics enforced across restart) =="           " hand delta + manual cross")

    snap_post = {"levels": dumps(lv4), "delta": dumps(d4)}

    # ---- AC-PWP5: second restart, sequential reads identical ----------
    counts_before_reads = table_counts(db)
    store.close()
    store3 = face_for(db)
    lv5a = store3.pool_water_levels()
    lv5b = store3.pool_water_levels()
    d5a = store3.pool_water_delta(snap_levels)
    d5b = store3.pool_water_delta(snap_levels)
    counts_after_reads = table_counts(db)
    ok5 = [dumps(lv5a) == snap_post["levels"],
           dumps(lv5b) == snap_post["levels"],
           dumps(d5a) == snap_post["delta"],
           dumps(d5b) == snap_post["delta"],
           counts_after_reads == counts_before_reads]
    record("AC-PWP5", all(ok5),
           "second store restart (third instance, same ugc.db):"
           " both faces re-read twice byte-identical to the"
           " post-verdict state (restart x new-data double"
           " hijack, zero drift); read batch left all five table"
           " row counts constant")

    # ---- AC-PWP6: pure-read law + manual cross + product sha ----------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    n5, reasons5, susp5, verd5 = manual_cells(db)
    lv5 = store3.pool_water_levels()
    ok6 = []
    ok6.append(shas_after == shas_before)
    ok6.append((n5, reasons5, susp5, verd5) == (
        4, {"emoji_only": 2, "flooding": 1, "too_short": 1},
        1, {"pass": 2, "risky": 1}))
    ok6.append(lv5["pool_water_levels"]["noise"]["total"] == n5
               and lv5["pool_water_levels"]["review"]["suspended"]
               == susp5
               and lv5["pool_water_levels"]["review"]["verdicted"]
               == verd5
               and lv5["total"] == n5 + susp5)
    ok6.append(dumps(store3.pool_water_delta(lv5))
               == dumps({"pool_water_delta": {}, "total_delta": 0,
                         "disclaimer": TEST_DISCLAIMER,
                         "persistent": True}))
    record("AC-PWP6", all(ok6),
           "pure-read law: restart read batches left the five"
           " tables constant; final world == fresh manual SQL"
           " cross (noise 4 / suspended 1 / verdicted pass2"
           " risky1); steady self-delta on the third instance"
           " honest {}; store.py sha256 unchanged (suite-only"
           " round)")

    # ---- AC-PWP7: hygiene + delivery wiring ---------------------------
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok7 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok7.append(not net_hits)
    ok7.append(os.path.abspath(tmp).startswith(tempfile.gettempdir()))
    ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    ok7.append(sha256_file(os.path.join(BASE, "config.json"))
               == cfg_sha)
    all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(all_path, encoding="utf-8") as fh:
        all_text = fh.read()
    wired = ('"ugc-pool-waterpersist"' in all_text
             and "test_pool_waterpersist.py" in all_text)
    ok7.append(wired)
    ok7.append(len(RESULTS) == EXPECTED - 1)
    record("AC-PWP7", all(ok7),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system tmp"
           " outside the repo, config.json sha unchanged; delivery"
           " wired into reconcile_all SUITES"
           " (ugc-pool-waterpersist, criteria 7)" % len(src_bytes))

    pipe.close()
    store3.close()

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
